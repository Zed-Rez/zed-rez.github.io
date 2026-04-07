"""Ollama generator — runs local models via the Ollama REST API."""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Optional

from generators.base import Generator

_DEFAULT_BASE_URL = "http://localhost:11434"
_DEFAULT_MODEL = "llama3"


class OllamaGenerator(Generator):
    name = "ollama"
    model_id = _DEFAULT_MODEL

    def __init__(
        self,
        model_id: str = _DEFAULT_MODEL,
        base_url: str = _DEFAULT_BASE_URL,
        **kwargs: object,
    ) -> None:
        self.model_id = model_id
        self.base_url = os.environ.get("OLLAMA_BASE_URL", base_url).rstrip("/")

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        payload: dict = {
            "model": self.model_id,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": self.temperature, "num_predict": self.max_tokens},
        }
        if system_prompt:
            payload["system"] = system_prompt

        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read())
        return body.get("response", "")
