from .base import BaseBackend
from .claude import ClaudeBackend
from .gemini import GeminiBackend
from .openai import OpenAIBackend
from .ollama import OllamaBackend
from .image_base import BaseImageBackend
from .gemini_image import GeminiImageBackend
from .forge_image import ForgeImageBackend

from dnd_combat_tracker.config import settings, VALID_PROVIDERS
from dnd_combat_tracker.db import settings as settings_db

VALID_IMAGE_PROVIDERS = {"gemini", "forge"}

__all__ = [
    "BaseBackend",
    "ClaudeBackend",
    "GeminiBackend",
    "OpenAIBackend",
    "OllamaBackend",
    "BaseImageBackend",
    "GeminiImageBackend",
    "ForgeImageBackend",
    "get_backend",
    "get_image_backend",
    "VALID_IMAGE_PROVIDERS",
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


def get_image_backend(session) -> BaseImageBackend:
    """
    Instantiate and return the configured image generation backend.
    Raises ValueError if no image provider is configured or the provider is invalid.
    """
    provider = settings_db.get(session, "image_provider", "")

    if not provider:
        raise ValueError("No image generation provider configured")

    if provider not in VALID_IMAGE_PROVIDERS:
        raise ValueError(f"Unknown image provider: {provider!r}")

    model = settings_db.get(session, f"{provider}_image_model")

    if provider == "gemini":
        if not settings.gemini_api_key:
            raise ValueError("Gemini API key not configured (set GEMINI_API_KEY)")
        return GeminiImageBackend(api_key=settings.gemini_api_key, model=model)

    if provider == "forge":
        return ForgeImageBackend(host=settings.forge_image_host, model=model)

    raise ValueError(f"Unhandled image provider: {provider!r}")
