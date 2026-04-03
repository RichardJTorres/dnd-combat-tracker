"""Stable Diffusion WebUI Forge image generation backend."""

import base64

import httpx

from .image_base import BaseImageBackend

DEFAULT_HOST = "http://localhost:7860"
DEFAULT_MODEL = "sd_xl_base_1.0"

NEGATIVE_PROMPT = (
    "bright colors, cartoon, anime, cute, happy, cheerful, "
    "low quality, blurry, watermark, text, logo"
)


class ForgeImageBackend(BaseImageBackend):
    def __init__(self, host: str = DEFAULT_HOST, model: str = DEFAULT_MODEL):
        self._host = host.rstrip("/")
        self._model = model

    @property
    def label(self) -> str:
        return f"Forge ({self._model})"

    def generate_image(self, prompt: str) -> bytes:
        payload = {
            "prompt": prompt,
            "negative_prompt": NEGATIVE_PROMPT,
            "steps": 25,
            "width": 512,
            "height": 512,
            "cfg_scale": 7,
        }
        r = httpx.post(
            f"{self._host}/sdapi/v1/txt2img",
            json=payload,
            timeout=120,
        )
        r.raise_for_status()
        images = r.json().get("images", [])
        if not images:
            raise RuntimeError("Forge returned no images in the response")
        return base64.b64decode(images[0])

    @classmethod
    def fetch_models(cls, host: str = DEFAULT_HOST) -> list[dict]:
        try:
            r = httpx.get(f"{host.rstrip('/')}/sdapi/v1/sd-models", timeout=5)
            r.raise_for_status()
            return [
                {"id": m["model_name"], "display_name": m.get("title", m["model_name"])}
                for m in r.json()
            ]
        except Exception:
            return [{"id": DEFAULT_MODEL, "display_name": DEFAULT_MODEL}]
