"""OpenAI generator (GPT-4o, GPT-4-turbo, GPT-3.5-turbo, …)."""

from __future__ import annotations

import os
from typing import Optional

from generators.base import Generator


class OpenAIGenerator(Generator):
    name = "openai"
    model_id = "gpt-4o"

    def __init__(self, model_id: str = "gpt-4o", **kwargs: object) -> None:
        self.model_id = model_id
        self._client = None

    @property
    def _openai(self):
        if self._client is None:
            from openai import OpenAI  # lazy import
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise EnvironmentError("OPENAI_API_KEY environment variable not set.")
            self._client = OpenAI(api_key=api_key)
        return self._client

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self._openai.chat.completions.create(
            model=self.model_id,
            messages=messages,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        return response.choices[0].message.content or ""
