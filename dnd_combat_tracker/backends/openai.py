"""OpenAI ChatGPT backend."""

import time
from typing import Callable

import openai as _openai

from .base import BaseBackend

DEFAULT_MODEL = "gpt-4o"
_MODEL_CACHE_TTL = 300


class OpenAIBackend(BaseBackend):
    _model_cache: dict = {"models": None, "ts": 0.0}

    @classmethod
    def fetch_models(cls, api_key: str) -> list[dict]:
        if not api_key:
            return []
        now = time.monotonic()
        if cls._model_cache["models"] is not None and now - cls._model_cache["ts"] < _MODEL_CACHE_TTL:
            return cls._model_cache["models"]
        try:
            client = _openai.OpenAI(api_key=api_key)
            models = sorted(
                [
                    {"id": m.id, "display_name": m.id}
                    for m in client.models.list()
                    if m.id.startswith("gpt-") or m.id.startswith("o1") or m.id.startswith("o3")
                ],
                key=lambda m: m["id"],
                reverse=True,
            )
        except Exception:
            models = []
        cls._model_cache["models"] = models
        cls._model_cache["ts"] = now
        return models

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self._client = _openai.OpenAI(api_key=api_key)
        self._model = model
        self._history: list[dict] = []

    @property
    def label(self) -> str:
        return f"openai:{self._model}"

    @property
    def supports_attachments(self) -> bool:
        return False

    def stream_turn(self, system: str, user_input: str, on_token: Callable[[str], None]) -> str:
        self._history.append({"role": "user", "content": user_input})
        response_text = ""

        messages = [{"role": "system", "content": system}, *self._history]
        with self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            stream=True,
        ) as stream:
            for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    on_token(delta.content)
                    response_text += delta.content

        self._history.append({"role": "assistant", "content": response_text})
        return response_text
