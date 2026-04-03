"""Google Gemini backend."""

import time
from typing import Callable

from google import genai
from google.genai import types

from .base import BaseBackend

DEFAULT_MODEL = "gemini-2.5-flash"
_MODEL_CACHE_TTL = 300


class GeminiBackend(BaseBackend):
    _model_cache: dict = {"models": None, "ts": 0.0}

    @classmethod
    def fetch_models(cls, api_key: str) -> list[dict]:
        if not api_key:
            return []
        now = time.monotonic()
        if cls._model_cache["models"] is not None and now - cls._model_cache["ts"] < _MODEL_CACHE_TTL:
            return cls._model_cache["models"]
        try:
            client = genai.Client(api_key=api_key)
            models = []
            for m in client.models.list():
                if "generateContent" not in (m.supported_actions or []):
                    continue
                model_id = m.name.removeprefix("models/")
                if not model_id.startswith("gemini-"):
                    continue
                models.append({"id": model_id, "display_name": m.display_name or model_id})
        except Exception:
            models = []
        cls._model_cache["models"] = models
        cls._model_cache["ts"] = now
        return models

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._history: list[types.Content] = []

    @property
    def label(self) -> str:
        return f"gemini:{self._model}"

    @property
    def supports_attachments(self) -> bool:
        return False

    def stream_turn(self, system: str, user_input: str, on_token: Callable[[str], None]) -> str:
        self._history.append(
            types.Content(role="user", parts=[types.Part.from_text(text=user_input)])
        )
        response_text = ""

        config = types.GenerateContentConfig(system_instruction=system)
        for chunk in self._client.models.generate_content_stream(
            model=self._model,
            contents=self._history,
            config=config,
        ):
            if chunk.text:
                on_token(chunk.text)
                response_text += chunk.text

        self._history.append(
            types.Content(role="model", parts=[types.Part.from_text(text=response_text)])
        )
        return response_text

    def parse_document(self, pdf_bytes: bytes, prompt: str) -> str:
        response = self._client.models.generate_content(
            model=self._model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                        types.Part.from_text(text=prompt),
                    ],
                )
            ],
        )
        return response.text
