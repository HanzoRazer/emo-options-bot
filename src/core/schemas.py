from __future__ import annotations
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, conint, confloat

Side = Literal["buy","sell"]
OptType = Literal["call","put"]
StrategyType = Literal["iron_condor","put_credit_spread","covered_call","protective_put","straddle","custom"]

class OrderLeg(BaseModel):
    symbol: str
    side: Side
    instrument: OptType
    strike: confloat(gt=0)
    expiry: str  # ISO date (YYYY-MM-DD)
    quantity: conint(gt=0)
    price_limit: Optional[confloat(gt=0)] = None

class RiskConstraints(BaseModel):
    max_risk_dollars: Optional[confloat(gt=0)] = None
    max_risk_pct_equity: Optional[confloat(gt=0, lt=1)] = 0.02
    max_positions: Optional[conint(gt=0)] = 20
    max_symbol_exposure_pct: Optional[confloat(gt=0, lt=1)] = 0.10
    min_ivr: Optional[confloat(ge=0, le=1)] = None
    max_ivr: Optional[confloat(ge=0, le=1)] = None

class TradePlan(BaseModel):
    strategy: StrategyType
    underlying: str
    rationale: str = ""
    notes: List[str] = []
    legs: List[OrderLeg]
    risk: RiskConstraints = RiskConstraints()
    telemetry: Dict[str, Any] = {}

class GateOutcome(BaseModel):
    ok: bool
    violations: List[str] = []
    suggested_fixes: List[str] = []

class StagedOrder(BaseModel):
    plan: TradePlan
    approved: bool = False
    gate_outcome: GateOutcome = GateOutcome(ok=False)