"""
Base Probe class.

To add a new Python-coded probe:
  1. Create probes/<category>.py  (or add to an existing file)
  2. Subclass Probe, set class attributes, implement get_prompts()
  3. Done — auto-registers via __init_subclass__.

To add a YAML-backed probe (no coding required):
  1. Drop a .yaml file under rules/<category>/
  2. Done — the yaml_loader picks it up at startup.

YAML schema (all fields except name/prompts are optional):
  name: unique_snake_case_id
  goal: Human-readable description of what this probe tests
  severity: low | medium | high | critical
  tags: [list, of, strings]
  system_prompt: |
    Optional system prompt (for white-box testing)
  prompts:
    - "First attack prompt"
    - "Second attack prompt"
  detector:
    type: keyword          # or llm_judge
    vulnerable_patterns:   # response contains any → VULNERABLE
      - "pattern one"
    safe_patterns:         # response contains any → SAFE (overrides above)
      - "I cannot"
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import inject.registry as registry


class Probe(ABC):
    """Abstract base for all injection test probes."""

    name: str = ""
    goal: str = ""
    severity: str = "medium"        # low | medium | high | critical
    tags: List[str] = []
    system_prompt: Optional[str] = None
    metadata: Dict[str, Any] = {}

    # Name of the detector to use (must match Detector.name in the registry)
    detector: str = "keyword"

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.name:
            registry._probes[cls.name] = cls

    @abstractmethod
    def get_prompts(self) -> List[str]:
        """Return the list of prompts to send to the target model."""

    def get_detector_config(self) -> Dict[str, Any]:
        """Return detector configuration dict passed to the Detector constructor."""
        return {"type": self.detector}

    def __repr__(self) -> str:
        return f"<Probe name={self.name!r} severity={self.severity!r}>"
