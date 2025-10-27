#!/usr/bin/env python3
"""
Dashboard Builder Tool - Production Patch Set
Builds and compiles the EMO Options Bot web dashboard with staged orders
"""

from __future__ import annotations
import json
from pathlib import Path

def main():
    staged_dir = Path("data/staged")
    staged = []
    if staged_dir.exists():
        for p in sorted(staged_dir.glob("*.json"))[-50:]:
            try:
                staged.append(json.loads(p.read_text()))
            except Exception:
                pass

    html = ["<html><head><meta http-equiv='refresh' content='10'><title>EMO Dashboard</title></head><body>"]
    html.append("<h2>Staged Orders (most recent)</h2><ul>")
    for s in reversed(staged):
        plan = s.get("plan", {})
        html.append(f"<li><b>{plan.get('underlying')}</b> · {plan.get('strategy')} · legs={len(plan.get('legs',[]))} · ok={s.get('gate_outcome',{}).get('ok')}</li>")
    html.append("</ul></body></html>")
    Path("enhanced_dashboard.html").write_text("\n".join(html))
    print("Wrote enhanced_dashboard.html")

if __name__ == "__main__":
    main()