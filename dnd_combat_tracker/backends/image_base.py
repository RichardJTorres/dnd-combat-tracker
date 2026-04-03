"""Abstract base class for image generation backends."""

from abc import ABC, abstractmethod


class BaseImageBackend(ABC):
    @property
    @abstractmethod
    def label(self) -> str: ...

    @abstractmethod
    def generate_image(self, prompt: str) -> bytes:
        """Generate an image from a text prompt. Returns raw PNG bytes."""
        ...

    @classmethod
    @abstractmethod
    def fetch_models(cls, *args, **kwargs) -> list[dict]:
        """Return available models as [{"id": ..., "display_name": ...}]."""
        ...
