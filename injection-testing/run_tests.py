#!/usr/bin/env python3
"""
AI Injection Testing Framework — CLI entry point.

Usage examples
--------------
# Run all probes against Claude Sonnet:
  python run_tests.py --providers anthropic

# Run all probes against GPT-4o and Claude Haiku:
  python run_tests.py --providers openai anthropic \\
      --models openai=gpt-4o-mini anthropic=claude-haiku-4-5-20251001

# Run only jailbreak probes:
  python run_tests.py --providers anthropic --probes jailbreak_dan_classic jailbreak_grandma

# List available probes / generators:
  python run_tests.py --list-probes
  python run_tests.py --list-generators

# Save results to JSON and HTML:
  python run_tests.py --providers anthropic --output-json results.json --output-html results.html

# Use LLM-as-judge detector for all probes:
  python run_tests.py --providers openai --detector llm_judge

Environment variables
---------------------
  OPENAI_API_KEY       — required for openai provider
  ANTHROPIC_API_KEY    — required for anthropic provider
  OLLAMA_BASE_URL      — optional, defaults to http://localhost:11434
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ── bootstrap ─────────────────────────────────────────────────────────── #
FRAMEWORK_ROOT = Path(__file__).parent
sys.path.insert(0, str(FRAMEWORK_ROOT))

from inject.runner import Runner, bootstrap  # noqa: E402
import inject.registry as registry           # noqa: E402
from inject import report                    # noqa: E402

bootstrap(FRAMEWORK_ROOT)


# ── CLI ───────────────────────────────────────────────────────────────── #

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="run_tests.py",
        description="AI Prompt Injection & Jailbreak Test Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    p.add_argument(
        "--providers", "-p",
        nargs="+",
        metavar="PROVIDER",
        help="Generator providers to test against (e.g. openai anthropic ollama)",
    )
    p.add_argument(
        "--models", "-m",
        nargs="+",
        metavar="PROVIDER=MODEL",
        help="Override default model per provider (e.g. openai=gpt-4o-mini)",
    )
    p.add_argument(
        "--probes",
        nargs="+",
        metavar="PROBE_NAME",
        help="Probe names to run (default: all). Use --list-probes to see names.",
    )
    p.add_argument(
        "--detector",
        default=None,
        metavar="DETECTOR",
        help="Override detector for all probes (e.g. llm_judge). Default: per-probe.",
    )
    p.add_argument(
        "--output-json",
        metavar="FILE",
        help="Write JSON report to this file",
    )
    p.add_argument(
        "--output-html",
        metavar="FILE",
        help="Write HTML report to this file",
    )
    p.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress per-attempt progress output",
    )
    p.add_argument(
        "--list-probes",
        action="store_true",
        help="List all registered probes and exit",
    )
    p.add_argument(
        "--list-generators",
        action="store_true",
        help="List all registered generators and exit",
    )
    p.add_argument(
        "--list-detectors",
        action="store_true",
        help="List all registered detectors and exit",
    )
    return p


def parse_model_overrides(raw: list[str] | None) -> dict:
    if not raw:
        return {}
    out = {}
    for item in raw:
        if "=" not in item:
            print(f"WARNING: Ignoring malformed --models entry {item!r} (expected PROVIDER=MODEL)")
            continue
        provider, model = item.split("=", 1)
        out[provider.strip()] = model.strip()
    return out


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.list_probes:
        probes = registry.list_probes()
        print(f"\nRegistered probes ({len(probes)}):\n")
        for name in probes:
            cls = registry.get_probe(name)
            instance = cls()
            sev = instance.severity
            tags = ", ".join(instance.tags) if instance.tags else "—"
            print(f"  {name:<45} [{sev:<8}]  {tags}")
        print()
        return

    if args.list_generators:
        gens = registry.list_generators()
        print(f"\nRegistered generators ({len(gens)}):\n")
        for name in gens:
            cls = registry.get_generator(name)
            print(f"  {name:<20}  default model: {cls.model_id}")
        print()
        return

    if args.list_detectors:
        dets = registry.list_detectors()
        print(f"\nRegistered detectors ({len(dets)}):\n")
        for name in dets:
            print(f"  {name}")
        print()
        return

    if not args.providers:
        parser.print_help()
        print("\nERROR: --providers is required. Example: --providers anthropic\n")
        sys.exit(1)

    model_ids = parse_model_overrides(args.models)

    runner = Runner(
        generator_names=args.providers,
        probe_names=args.probes,
        model_ids=model_ids,
        verbose=not args.quiet,
    )

    print(f"\nRunning {len(runner.probe_classes)} probe(s) against "
          f"{len(runner.generators)} generator(s)…\n")

    attempts = runner.run()

    report.print_summary(attempts)

    if args.output_json:
        report.to_json(attempts, Path(args.output_json))
        print(f"JSON report saved → {args.output_json}")

    if args.output_html:
        report.to_html(attempts, Path(args.output_html))
        print(f"HTML report saved → {args.output_html}")

    # Exit non-zero if any vulnerabilities found
    any_vuln = any(a.vulnerable for a in attempts)
    sys.exit(1 if any_vuln else 0)


if __name__ == "__main__":
    main()
