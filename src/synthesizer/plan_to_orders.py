from __future__ import annotations
from typing import Dict
from src.core.schemas import TradePlan, OrderLeg

def synthesize(plan_sketch: Dict) -> TradePlan:
    # trivial iron condor for demo; Phase 4 will compute greeks/widths/TTM
    legs = [
        OrderLeg(symbol=plan_sketch.get("underlying","SPY"), side="sell", instrument="call", strike=470, expiry="2025-12-20", quantity=1),
        OrderLeg(symbol=plan_sketch.get("underlying","SPY"), side="buy",  instrument="call", strike=475, expiry="2025-12-20", quantity=1),
        OrderLeg(symbol=plan_sketch.get("underlying","SPY"), side="sell", instrument="put",  strike=430, expiry="2025-12-20", quantity=1),
        OrderLeg(symbol=plan_sketch.get("underlying","SPY"), side="buy",  instrument="put",  strike=425, expiry="2025-12-20", quantity=1),
    ]
    return TradePlan(
        strategy="iron_condor",
        underlying=plan_sketch.get("underlying","SPY"),
        rationale="demo",
        notes=plan_sketch.get("notes", []),
        legs=legs
    )