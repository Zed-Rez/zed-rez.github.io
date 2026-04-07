"""
Base Generator class.

To add a new provider:
  1. Create generators/<your_provider>.py
  2. Subclass Generator and set name = "your_provider"
  3. Implement generate(prompt, system_prompt) -> str
  4. Done — the class auto-registers via __init_subclass__.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import inject.registry as registry


class Generator(ABC):
    """Abstract base for all LLM provider adapters."""

    name: str = ""           # unique registry key  (e.g. "openai")
    model_id: str = ""       # default model        (e.g. "gpt-4o")
    max_tokens: int = 512
    temperature: float = 0.7

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.name:
            registry._generators[cls.name] = cls

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Send *prompt* to the model and return the text response."""

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.model_id!r}>"
