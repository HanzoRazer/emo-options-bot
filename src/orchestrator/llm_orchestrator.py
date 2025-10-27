from __future__ import annotations
import os
from typing import Dict, Any
# minimal, dependency-light mock that can use OpenAI if key present

def analyze_nl_request(text: str) -> Dict[str, Any]:
    # If you wire OpenAI later, translate text → plan sketch here.
    # For now, return a deterministic sketch for CI stability.
    return {
        "strategy": "iron_condor",
        "underlying": "SPY",
        "notes": [f"nl:{text[:64]}"],
        "telemetry": {"orchestrator":"mock"}
    }