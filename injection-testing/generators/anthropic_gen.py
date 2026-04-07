"""Anthropic generator (Claude Sonnet, Haiku, Opus, …)."""

from __future__ import annotations

import os
from typing import Optional

from generators.base import Generator

# Default to latest Sonnet; override with --model or ANTHROPIC_MODEL env var.
_DEFAULT_MODEL = "claude-sonnet-4-6"


class AnthropicGenerator(Generator):
    name = "anthropic"
    model_id = _DEFAULT_MODEL

    def __init__(self, model_id: str = _DEFAULT_MODEL, **kwargs: object) -> None:
        self.model_id = model_id
        self._client = None

    @property
    def _anthropic(self):
        if self._client is None:
            import anthropic  # lazy import
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise EnvironmentError("ANTHROPIC_API_KEY environment variable not set.")
            self._client = anthropic.Anthropic(api_key=api_key)
        return self._client

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        kwargs: dict = {
            "model": self.model_id,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = self._anthropic.messages.create(**kwargs)
        return response.content[0].text
