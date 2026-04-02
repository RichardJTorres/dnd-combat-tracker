"""Anthropic Claude backend."""

import time
from typing import Callable

import anthropic

from .base import BaseBackend

DEFAULT_MODEL = "claude-sonnet-4-6"
_MODEL_CACHE_TTL = 300


class ClaudeBackend(BaseBackend):
    _model_cache: dict = {"models": None, "ts": 0.0}

    @classmethod
    def fetch_models(cls, api_key: str) -> list[dict]:
        if not api_key:
            return []
        now = time.monotonic()
        if cls._model_cache["models"] is not None and now - cls._model_cache["ts"] < _MODEL_CACHE_TTL:
            return cls._model_cache["models"]
        try:
            client = anthropic.Anthropic(api_key=api_key)
            models = [
                {"id": m.id, "display_name": m.display_name}
                for m in client.models.list(limit=100)
            ]
        except Exception:
            models = []
        cls._model_cache["models"] = models
        cls._model_cache["ts"] = now
        return models

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._history: list[dict] = []

    @property
    def label(self) -> str:
        return self._model

    @property
    def supports_attachments(self) -> bool:
        return True

    def stream_turn(self, system: str, user_input: str, on_token: Callable[[str], None]) -> str:
        self._history.append({"role": "user", "content": user_input})
        response_text = ""

        with self._client.messages.stream(
            model=self._model,
            max_tokens=2048,
            system=system,
            messages=self._history,
        ) as stream:
            for chunk in stream.text_stream:
                on_token(chunk)
                response_text += chunk

        self._history.append({"role": "assistant", "content": response_text})
        return response_text
