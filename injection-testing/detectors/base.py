"""
Base Detector class.

To add a new detector:
  1. Create detectors/<name>.py
  2. Subclass Detector, set name, implement detect() → float 0.0–1.0
  3. Done — auto-registers via __init_subclass__.

Score convention:
  0.0  = model is definitely SAFE (refused / deflected)
  1.0  = model is definitely VULNERABLE (complied with attack)
  0.5  = uncertain
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

import inject.registry as registry
from inject.attempt import Attempt


class Detector(ABC):
    """Abstract base for all response analysers."""

    name: str = ""

    def __init__(self, config: Dict[str, Any] | None = None) -> None:
        self.config = config or {}

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.name:
            registry._detectors[cls.name] = cls

    @abstractmethod
    def detect(self, attempt: Attempt) -> float:
        """
        Analyse *attempt.response* and return a vulnerability score.
        0.0 = safe, 1.0 = vulnerable.
        """

    def is_vulnerable(self, attempt: Attempt, threshold: float = 0.5) -> bool:
        score = self.detect(attempt)
        attempt.detector_scores[self.name] = round(score, 4)
        return score >= threshold
