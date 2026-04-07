"""
Central plugin registry.

Generators, Probes, and Detectors register themselves here automatically
when their module is imported (via __init_subclass__).  The runner
imports all sub-packages at startup to trigger registration.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Type

if TYPE_CHECKING:
    from generators.base import Generator
    from probes.base import Probe
    from detectors.base import Detector

_generators: Dict[str, Type] = {}
_probes: Dict[str, Type] = {}
_detectors: Dict[str, Type] = {}


# ── public accessors ──────────────────────────────────────────────────── #

def all_generators() -> Dict[str, Type]:
    return dict(_generators)


def all_probes() -> Dict[str, Type]:
    return dict(_probes)


def all_detectors() -> Dict[str, Type]:
    return dict(_detectors)


def list_generators() -> List[str]:
    return sorted(_generators)


def list_probes() -> List[str]:
    return sorted(_probes)


def list_detectors() -> List[str]:
    return sorted(_detectors)


def get_generator(name: str) -> Type:
    if name not in _generators:
        raise KeyError(f"Unknown generator '{name}'. Available: {list_generators()}")
    return _generators[name]


def get_probe(name: str) -> Type:
    if name not in _probes:
        raise KeyError(f"Unknown probe '{name}'. Available: {list_probes()}")
    return _probes[name]


def get_detector(name: str) -> Type:
    if name not in _detectors:
        raise KeyError(f"Unknown detector '{name}'. Available: {list_detectors()}")
    return _detectors[name]
