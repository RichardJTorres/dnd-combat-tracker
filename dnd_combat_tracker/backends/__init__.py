from .base import BaseBackend
from .claude import ClaudeBackend
from .gemini import GeminiBackend
from .openai import OpenAIBackend
from .ollama import OllamaBackend

__all__ = ["BaseBackend", "ClaudeBackend", "GeminiBackend", "OpenAIBackend", "OllamaBackend", "get_backend"]


def get_backend(session) -> BaseBackend:
    """Return the configured backend using provider/model from app settings."""
    from dnd_combat_tracker.config import settings
    from dnd_combat_tracker.db import settings as settings_db

    provider = settings_db.get(session, "provider", "claude")
    model = settings_db.get(session, f"{provider}_model") or None

    if provider == "claude":
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured — add ANTHROPIC_API_KEY to .env")
        kw = {"model": model} if model else {}
        return ClaudeBackend(api_key=settings.anthropic_api_key, **kw)
    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("Gemini API key not configured — add GEMINI_API_KEY to .env")
        kw = {"model": model} if model else {}
        return GeminiBackend(api_key=settings.gemini_api_key, **kw)
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured — add OPENAI_API_KEY to .env")
        kw = {"model": model} if model else {}
        return OpenAIBackend(api_key=settings.openai_api_key, **kw)
    if provider == "ollama":
        kw = {"model": model} if model else {}
        return OllamaBackend(**kw, host=settings.ollama_host)
    raise ValueError(f"Unknown provider: {provider}")
