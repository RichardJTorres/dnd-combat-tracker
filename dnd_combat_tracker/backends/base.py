"""Abstract base class for LLM backends."""

import io
from abc import ABC, abstractmethod
from typing import Callable


def _pdf_to_text(pdf_bytes: bytes) -> str:
    """Extract plain text from a PDF using pypdf (fallback for non-native PDF backends)."""
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages).strip()


class BaseBackend(ABC):
    """
    Wraps one LLM provider. Subclasses implement stream_turn() to send a
    prompt and stream back tokens. History management is left to each backend.
    """

    @property
    @abstractmethod
    def label(self) -> str:
        """Human-readable identifier, e.g. 'claude-sonnet-4-6'."""

    @property
    @abstractmethod
    def supports_attachments(self) -> bool:
        """Whether this backend can accept image/file attachments."""

    @abstractmethod
    def stream_turn(
        self,
        system: str,
        user_input: str,
        on_token: Callable[[str], None],
    ) -> str:
        """
        Send user_input to the LLM, call on_token(chunk) for each streamed
        text chunk, and return the full response text.
        """

    @abstractmethod
    def parse_document(self, pdf_bytes: bytes, prompt: str) -> str:
        """
        Send a PDF document and a prompt, return the model's text response.
        Backends with native PDF support pass the raw bytes; others extract
        text first via _pdf_to_text().
        """
