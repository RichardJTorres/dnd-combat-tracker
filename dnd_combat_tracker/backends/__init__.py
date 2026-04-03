from .base import BaseBackend
from .claude import ClaudeBackend
from .gemini import GeminiBackend
from .openai import OpenAIBackend
from .ollama import OllamaBackend

from dnd_combat_tracker.config import settings, VALID_PROVIDERS
from dnd_combat_tracker.db import settings as settings_db

__all__ = [
    "BaseBackend",
    "ClaudeBackend",
    "GeminiBackend",
    "OpenAIBackend",
    "OllamaBackend",
    "get_backend",
]


def get_backend(session) -> BaseBackend:
    """
    Instantiate and return the configured LLM backend using the provider and
    model persisted in the DB settings. Raises ValueError if the provider is
    unknown or the required API key is missing.
    """
    provider = settings_db.get(session, "provider", "claude")

    if provider not in VALID_PROVIDERS:
        raise ValueError(f"Unknown provider: {provider!r}")

    model = settings_db.get(session, f"{provider}_model")

    if provider == "claude":
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured (set ANTHROPIC_API_KEY)")
        return ClaudeBackend(api_key=settings.anthropic_api_key, model=model)

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("Gemini API key not configured (set GEMINI_API_KEY)")
        return GeminiBackend(api_key=settings.gemini_api_key, model=model)

    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured (set OPENAI_API_KEY)")
        return OpenAIBackend(api_key=settings.openai_api_key, model=model)

    if provider == "ollama":
        return OllamaBackend(
            model=model or settings.ollama_model,
            host=settings.ollama_host,
        )

    raise ValueError(f"Unhandled provider: {provider!r}")
