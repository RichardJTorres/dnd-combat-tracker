"""AI provider and model settings endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from dnd_combat_tracker.config import settings, VALID_PROVIDERS
from dnd_combat_tracker.db.engine import get_session
from dnd_combat_tracker.db import settings as settings_db

router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsBody(BaseModel):
    provider: str | None = None
    model: str | None = None


@router.get("")
def get_settings(session: Session = Depends(get_session)):
    provider = settings_db.get(session, "provider", "claude")
    return {
        "provider": provider,
        "model": settings_db.get(session, f"{provider}_model"),
    }


@router.put("")
def put_settings(body: SettingsBody, session: Session = Depends(get_session)):
    if body.provider is not None:
        if body.provider not in VALID_PROVIDERS:
            raise HTTPException(
                status_code=400,
                detail=f"provider must be one of {sorted(VALID_PROVIDERS)}",
            )
        settings_db.set(session, "provider", body.provider)

    if body.model is not None:
        provider = body.provider or settings_db.get(session, "provider", "claude")
        settings_db.set(session, f"{provider}_model", body.model)

    provider = settings_db.get(session, "provider", "claude")
    return {
        "provider": provider,
        "model": settings_db.get(session, f"{provider}_model"),
    }


@router.get("/providers")
def get_providers():
    """Return each provider and whether its API key is configured."""
    return [
        {
            "id": "claude",
            "label": "Claude (Anthropic)",
            "configured": bool(settings.anthropic_api_key),
        },
        {
            "id": "gemini",
            "label": "Gemini (Google)",
            "configured": bool(settings.gemini_api_key),
        },
        {
            "id": "openai",
            "label": "ChatGPT (OpenAI)",
            "configured": bool(settings.openai_api_key),
        },
        {
            "id": "ollama",
            "label": "Ollama (local)",
            "configured": _ollama_available(),
        },
    ]


@router.get("/providers/{provider}/models")
def get_models(provider: str):
    if provider not in VALID_PROVIDERS:
        raise HTTPException(status_code=404, detail=f"Unknown provider: {provider}")
    return _fetch_models(provider)


def _ollama_available() -> bool:
    import httpx
    try:
        httpx.get(f"{settings.ollama_host}/api/tags", timeout=2)
        return True
    except Exception:
        return False


def _fetch_models(provider: str) -> list[dict]:
    from dnd_combat_tracker.backends import ClaudeBackend, GeminiBackend, OpenAIBackend, OllamaBackend
    if provider == "claude":
        return ClaudeBackend.fetch_models(settings.anthropic_api_key)
    if provider == "gemini":
        return GeminiBackend.fetch_models(settings.gemini_api_key)
    if provider == "openai":
        return OpenAIBackend.fetch_models(settings.openai_api_key)
    if provider == "ollama":
        return OllamaBackend.fetch_models(settings.ollama_host)
    return []
