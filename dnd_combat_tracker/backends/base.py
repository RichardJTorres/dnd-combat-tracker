"""Abstract base class for LLM backends."""

from abc import ABC, abstractmethod
from typing import Callable, Iterator


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
