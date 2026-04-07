"""
Runner — orchestrates probes × generators and collects Attempts.

Flow:
  1. Import all plugin packages (triggers __init_subclass__ registration).
  2. Instantiate selected generators and probes.
  3. For each probe × each prompt × each generator:
       a. Send prompt → generator.generate()
       b. Score response → detector.detect()
       c. Record Attempt.
  4. Return list[Attempt].
"""

from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path
from typing import List, Optional

from inject.attempt import Attempt
import inject.registry as registry


# ── plugin discovery ──────────────────────────────────────────────────── #

def _import_package(pkg_name: str) -> None:
    """Import all modules inside a package so subclasses self-register."""
    try:
        pkg = importlib.import_module(pkg_name)
    except ModuleNotFoundError:
        return
    pkg_path = getattr(pkg, "__path__", [])
    for _, mod_name, _ in pkgutil.iter_modules(pkg_path):
        importlib.import_module(f"{pkg_name}.{mod_name}")


def bootstrap(framework_root: Path) -> None:
    """
    Add framework_root to sys.path then import all plugin packages.
    Call once before any registry lookups.
    """
    root = str(framework_root)
    if root not in sys.path:
        sys.path.insert(0, root)
    for pkg in ("generators", "probes", "detectors"):
        _import_package(pkg)
    # Load YAML-backed probes
    from probes.yaml_loader import load_rules_dir
    rules_dir = framework_root / "rules"
    if rules_dir.is_dir():
        load_rules_dir(rules_dir)


# ── runner ────────────────────────────────────────────────────────────── #

class Runner:
    """
    Runs selected probes against selected generators.

    Parameters
    ----------
    generator_names : list[str]
        Registry keys for generators, e.g. ["openai", "anthropic"].
    probe_names : list[str] | None
        Registry keys for probes.  None → run all registered probes.
    model_ids : dict[str, str] | None
        Override default model ID per provider, e.g. {"openai": "gpt-4o-mini"}.
    verbose : bool
        Print progress to stdout.
    """

    def __init__(
        self,
        generator_names: List[str],
        probe_names: Optional[List[str]] = None,
        model_ids: Optional[dict] = None,
        verbose: bool = True,
    ) -> None:
        self.verbose = verbose
        model_ids = model_ids or {}

        # instantiate generators
        self.generators = []
        for g_name in generator_names:
            GenCls = registry.get_generator(g_name)
            kwargs = {}
            if g_name in model_ids:
                kwargs["model_id"] = model_ids[g_name]
            self.generators.append(GenCls(**kwargs))

        # resolve probes
        if probe_names is None:
            probe_names = registry.list_probes()
        self.probe_classes = [registry.get_probe(n) for n in probe_names]

    def run(self) -> List[Attempt]:
        attempts: List[Attempt] = []

        for ProbeCls in self.probe_classes:
            probe = ProbeCls()
            prompts = probe.get_prompts()
            det_cfg = probe.get_detector_config()
            DetCls = registry.get_detector(det_cfg.get("type", "keyword"))
            detector = DetCls(config=det_cfg)

            for generator in self.generators:
                for prompt in prompts:
                    attempt = Attempt(
                        probe_name=probe.name,
                        prompt=prompt,
                        model_id=generator.model_id,
                        provider=generator.name,
                        severity=probe.severity,
                        tags=list(probe.tags),
                        system_prompt=probe.system_prompt,
                        metadata=probe.metadata,
                    )

                    if self.verbose:
                        print(
                            f"  [{generator.name}/{generator.model_id}] "
                            f"{probe.name}: {prompt[:60].strip()!r}…"
                        )

                    try:
                        attempt.response = generator.generate(
                            prompt, system_prompt=probe.system_prompt
                        )
                        attempt.vulnerable = detector.is_vulnerable(attempt)
                    except Exception as exc:  # noqa: BLE001
                        attempt.response = f"ERROR: {exc}"
                        attempt.vulnerable = None

                    attempts.append(attempt)

        return attempts
