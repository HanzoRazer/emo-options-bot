from __future__ import annotations
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class MarketView(BaseModel):
    # Parsed "intent" from user/voice -> LLM -> structure
    symbol: str = Field(..., description="Primary symbol, e.g., SPY")
    outlook: Literal["bullish","bearish","neutral","volatile","range"] = "neutral"
    horizon_days: int = 7
    confidence: float = 0.5
    notes: Optional[str] = None

class Leg(BaseModel):
    action: Literal["buy","sell"]
    instrument: Literal["call","put"]
    strike: float
    quantity: int = 1
    expiry: Optional[str] = None   # ISO date or yyyymmdd

class SynthesizedTrade(BaseModel):
    strategy_type: Literal[
        "iron_condor","put_credit_spread","call_credit_spread",
        "long_straddle","long_put","long_call","covered_call","collar"
    ]
    symbol: str
    legs: List[Leg]
    max_risk: Optional[float] = None
    target_credit: Optional[float] = None
    rationale: Optional[str] = None
    notes: Optional[str] = None

class RiskViolation(BaseModel):
    rule: str
    detail: str
    severity: Literal["info","warn","block"] = "block"

class SynthesisResult(BaseModel):
    trade: Optional[SynthesizedTrade] = None
    violations: List[RiskViolation] = []
    ok: bool = False