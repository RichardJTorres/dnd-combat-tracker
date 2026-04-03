"""Gemini image generation backend (nanobanana models)."""

import base64

from google import genai
from google.genai import types

from .image_base import BaseImageBackend

DEFAULT_MODEL = "gemini-2.0-flash-exp-image-generation"

# Known nanobanana / Gemini image generation models
_KNOWN_MODELS = [
    {"id": "gemini-2.0-flash-exp-image-generation", "display_name": "Gemini 2.0 Flash Image (experimental)"},
    {"id": "imagen-3.0-generate-002", "display_name": "Imagen 3"},
]


class GeminiImageBackend(BaseImageBackend):
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL):
        self._client = genai.Client(api_key=api_key)
        self._model = model

    @property
    def label(self) -> str:
        return f"Gemini Image ({self._model})"

    def generate_image(self, prompt: str) -> bytes:
        response = self._client.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                return base64.b64decode(part.inline_data.data)
        raise RuntimeError("Gemini returned no image in the response")

    @classmethod
    def fetch_models(cls, api_key: str) -> list[dict]:
        return _KNOWN_MODELS
