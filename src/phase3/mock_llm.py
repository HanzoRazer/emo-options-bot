from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class LLMPlan:
    strategy: str           # e.g., "iron_condor" | "put_credit_spread"
    thesis: str
    risk_budget: float      # absolute currency risk cap (per-trade)
    meta: Dict[str, Any]

def mock_analyze(nl_request: str) -> LLMPlan:
    """Very small, deterministic planner for the harness.
       Choose a neutral or directional structure based on hints.
    """
    req = nl_request.lower()
    if any(k in req for k in ("sideways", "range", "neutral", "consolidate")):
        return LLMPlan(
            strategy="iron_condor",
            thesis="Range-bound outlook; premium harvesting.",
            risk_budget=1500.0,
            meta={"center_hint":"atm","width":5}
        )
    if any(k in req for k in ("volatile", "volatility", "big move", "uncertain")):
        return LLMPlan(
            strategy="straddle",
            thesis="Expecting larger realized volatility than implied.",
            risk_budget=1200.0,
            meta={"atm":True}
        )
    # default: mildly bullish income via PCS
    return LLMPlan(
        strategy="put_credit_spread",
        thesis="Mildly bullish; sell downside premium with defined risk.",
        risk_budget=1000.0,
        meta={"delta":0.20,"width":5}
    )