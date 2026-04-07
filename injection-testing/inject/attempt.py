"""Attempt — the central data structure representing one probe run against one model."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class Attempt:
    """One injection attempt: a single prompt sent to a model and the result."""

    probe_name: str
    prompt: str
    model_id: str
    provider: str
    severity: str = "medium"
    tags: List[str] = field(default_factory=list)
    system_prompt: Optional[str] = None

    # Filled after generation
    response: Optional[str] = None

    # Filled after detection
    detector_scores: Dict[str, float] = field(default_factory=dict)
    vulnerable: Optional[bool] = None

    # Free-form metadata (probe author, rule file path, …)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    # ------------------------------------------------------------------ #
    def to_dict(self) -> Dict[str, Any]:
        def _trunc(s: Optional[str], n: int = 500) -> Optional[str]:
            if s is None:
                return None
            return s[:n] + "…" if len(s) > n else s

        return {
            "probe": self.probe_name,
            "prompt": _trunc(self.prompt, 300),
            "model": f"{self.provider}/{self.model_id}",
            "response": _trunc(self.response),
            "vulnerable": self.vulnerable,
            "severity": self.severity,
            "tags": self.tags,
            "detector_scores": self.detector_scores,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }
