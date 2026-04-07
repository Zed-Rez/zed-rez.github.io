"""
Report — formats Attempt lists for console, JSON, and HTML output.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import List, Optional

from inject.attempt import Attempt

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_SEVERITY_EMOJI = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}


# ── console ───────────────────────────────────────────────────────────── #

def print_summary(attempts: List[Attempt]) -> None:
    if not attempts:
        print("No attempts recorded.")
        return

    total = len(attempts)
    vuln = sum(1 for a in attempts if a.vulnerable is True)
    safe = sum(1 for a in attempts if a.vulnerable is False)
    error = sum(1 for a in attempts if a.vulnerable is None)

    print("\n" + "=" * 70)
    print("  INJECTION TEST RESULTS")
    print("=" * 70)
    print(f"  Total attempts : {total}")
    print(f"  Vulnerable     : {vuln}  ({vuln/total*100:.1f}%)")
    print(f"  Safe           : {safe}")
    print(f"  Errors         : {error}")
    print("=" * 70)

    # group by probe
    by_probe: dict = defaultdict(list)
    for a in attempts:
        by_probe[a.probe_name].append(a)

    for probe_name in sorted(by_probe):
        group = by_probe[probe_name]
        sev = group[0].severity
        icon = _SEVERITY_EMOJI.get(sev, "  ")
        v = sum(1 for a in group if a.vulnerable is True)
        print(f"\n  {icon}  {probe_name}  [{sev}]  {v}/{len(group)} vulnerable")
        for a in group:
            status = "VULN" if a.vulnerable else ("SAFE" if a.vulnerable is False else "ERR ")
            model_label = f"{a.provider}/{a.model_id}"
            resp_preview = (a.response or "")[:120].replace("\n", " ")
            print(f"       [{status}] {model_label:<35} {resp_preview!r}")

    print("\n" + "=" * 70 + "\n")


# ── JSON ──────────────────────────────────────────────────────────────── #

def to_json(attempts: List[Attempt], path: Optional[Path] = None) -> str:
    data = {
        "summary": {
            "total": len(attempts),
            "vulnerable": sum(1 for a in attempts if a.vulnerable is True),
            "safe": sum(1 for a in attempts if a.vulnerable is False),
            "errors": sum(1 for a in attempts if a.vulnerable is None),
        },
        "attempts": [a.to_dict() for a in attempts],
    }
    output = json.dumps(data, indent=2)
    if path:
        Path(path).write_text(output)
    return output


# ── HTML ──────────────────────────────────────────────────────────────── #

def to_html(attempts: List[Attempt], path: Optional[Path] = None) -> str:
    rows = ""
    for a in attempts:
        status_cls = (
            "vuln" if a.vulnerable else ("safe" if a.vulnerable is False else "err")
        )
        status_label = (
            "VULNERABLE" if a.vulnerable else ("SAFE" if a.vulnerable is False else "ERROR")
        )
        rows += f"""
        <tr class="{status_cls}">
          <td>{a.probe_name}</td>
          <td>{a.provider}/{a.model_id}</td>
          <td>{a.severity}</td>
          <td class="status">{status_label}</td>
          <td class="prompt">{_esc(a.prompt[:200])}</td>
          <td class="response">{_esc((a.response or '')[:300])}</td>
        </tr>"""

    total = len(attempts)
    vuln = sum(1 for a in attempts if a.vulnerable is True)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>Injection Test Report</title>
  <style>
    body {{ font-family: monospace; background: #0d1117; color: #c9d1d9; padding: 2rem; }}
    h1 {{ color: #58a6ff; }}
    .stats {{ margin: 1rem 0; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th {{ background: #21262d; padding: .5rem; text-align: left; }}
    td {{ border-top: 1px solid #30363d; padding: .4rem .5rem; vertical-align: top; }}
    tr.vuln td.status {{ color: #f85149; font-weight: bold; }}
    tr.safe  td.status {{ color: #3fb950; }}
    tr.err   td.status {{ color: #d29922; }}
    .prompt, .response {{ font-size: .8rem; max-width: 300px; word-break: break-word; }}
  </style>
</head>
<body>
  <h1>AI Injection Test Report</h1>
  <div class="stats">
    Total: <b>{total}</b> &nbsp;|&nbsp;
    Vulnerable: <b style="color:#f85149">{vuln}</b> &nbsp;|&nbsp;
    Safe: <b style="color:#3fb950">{total - vuln}</b>
  </div>
  <table>
    <thead>
      <tr><th>Probe</th><th>Model</th><th>Severity</th><th>Result</th><th>Prompt</th><th>Response</th></tr>
    </thead>
    <tbody>{rows}
    </tbody>
  </table>
</body>
</html>"""
    if path:
        Path(path).write_text(html)
    return html


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
