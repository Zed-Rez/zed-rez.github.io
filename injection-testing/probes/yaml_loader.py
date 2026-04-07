"""
YAML probe loader.

Scans rules/ directory recursively for *.yaml files and dynamically
creates Probe subclasses from them.  This lets you add a new test
without writing any Python — just drop a YAML file.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import inject.registry as registry
from probes.base import Probe

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


def _make_probe_class(spec: Dict[str, Any]) -> type:
    """Dynamically build a Probe subclass from a YAML spec dict."""
    prompts: List[str] = spec.get("prompts", [])
    det_cfg: Dict[str, Any] = spec.get("detector", {"type": "keyword"})

    # Build class body
    ns: Dict[str, Any] = {
        "name": spec["name"],
        "goal": spec.get("goal", ""),
        "severity": spec.get("severity", "medium"),
        "tags": spec.get("tags", []),
        "system_prompt": spec.get("system_prompt"),
        "metadata": spec.get("metadata", {}),
        "detector": det_cfg.get("type", "keyword"),
        "_prompts": prompts,
        "_det_cfg": det_cfg,
        "get_prompts": lambda self: list(self._prompts),
        "get_detector_config": lambda self: dict(self._det_cfg),
    }
    cls = type(spec["name"], (Probe,), ns)
    return cls


def load_rules_dir(rules_dir: Path) -> List[type]:
    """
    Walk *rules_dir* recursively, parse every *.yaml file, and register
    resulting Probe classes.  Returns the list of created classes.
    """
    if not _HAS_YAML:
        print(
            "WARNING: PyYAML not installed — YAML rules will not be loaded.\n"
            "         Run:  pip install pyyaml"
        )
        return []

    created: List[type] = []
    for yaml_path in sorted(rules_dir.rglob("*.yaml")):
        try:
            with yaml_path.open() as fh:
                spec = yaml.safe_load(fh)
            if not isinstance(spec, dict) or "name" not in spec:
                print(f"WARNING: Skipping {yaml_path} — missing 'name' field.")
                continue
            if spec["name"] in registry._probes:
                continue  # already registered (e.g. Python class with same name)
            cls = _make_probe_class(spec)
            cls.metadata["rule_file"] = str(yaml_path)
            created.append(cls)
        except Exception as exc:  # noqa: BLE001
            print(f"WARNING: Could not load {yaml_path}: {exc}")

    return created
