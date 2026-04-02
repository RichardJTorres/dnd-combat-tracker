"""Ollama local backend."""

import json
import time
from typing import Callable

import httpx

from .base import BaseBackend

DEFAULT_HOST = "http://localhost:11434"
DEFAULT_MODEL = "llama3.1"
_MODEL_CACHE_TTL = 300


class OllamaBackend(BaseBackend):
    _model_cache: dict = {"models": None, "ts": 0.0}

    @classmethod
    def fetch_models(cls, host: str) -> list[dict]:
        host = host.rstrip("/")
        now = time.monotonic()
        if cls._model_cache["models"] is not None and now - cls._model_cache["ts"] < _MODEL_CACHE_TTL:
            return cls._model_cache["models"]
        try:
            resp = httpx.get(f"{host}/api/tags", timeout=3)
            models = [
                {"id": m["name"], "display_name": m["name"]}
                for m in resp.json().get("models", [])
            ]
        except Exception:
            models = []
        cls._model_cache["models"] = models
        cls._model_cache["ts"] = now
        return models

    def __init__(self, model: str = DEFAULT_MODEL, host: str = DEFAULT_HOST) -> None:
        self._model = model
        self._host = host.rstrip("/")
        self._history: list[dict] = []

    @property
    def label(self) -> str:
        return f"ollama:{self._model}"

    @property
    def supports_attachments(self) -> bool:
        return False

    def stream_turn(self, system: str, user_input: str, on_token: Callable[[str], None]) -> str:
        self._history.append({"role": "user", "content": user_input})
        response_text = ""

        messages = [{"role": "system", "content": system}, *self._history]
        with httpx.Client(timeout=120) as client:
            with client.stream(
                "POST",
                f"{self._host}/api/chat",
                json={"model": self._model, "messages": messages, "stream": True},
            ) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if not line:
                        continue
                    chunk = json.loads(line)
                    text = chunk.get("message", {}).get("content", "")
                    if text:
                        on_token(text)
                        response_text += text
                    if chunk.get("done"):
                        break

        self._history.append({"role": "assistant", "content": response_text})
        return response_text
