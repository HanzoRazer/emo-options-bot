from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass
class AnalysisRequest:
    user_text: str
    symbol: str = "SPY"
    horizon_days: int = 7
    context: Dict[str, Any] = field(default_factory=dict)
    locale: str = "en"
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RiskConstraints:
    max_risk_per_trade: float = 0.02      # fraction of account equity
    max_portfolio_risk: float = 0.10      # fraction of account equity
    min_option_oi: int = 100              # liquidity safety
    max_spread_width: float = 10.0        # dollars
    min_dte: int = 5
    max_dte: int = 45

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TradeLeg:
    action: str          # 'buy' | 'sell'
    instrument: str      # 'call' | 'put'
    strike: float
    quantity: int
    expiration: Optional[str] = None      # ISO date or 'YYYY-MM-DD'

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TradePlan:
    strategy_type: str                   # e.g., 'iron_condor', 'put_credit_spread'
    symbol: str
    legs: List[TradeLeg]
    target_credit: Optional[float] = None
    max_loss: Optional[float] = None
    rationale: Optional[str] = None
    constraints: RiskConstraints = field(default_factory=RiskConstraints)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["legs"] = [leg.to_dict() for leg in self.legs]
        d["constraints"] = self.constraints.to_dict()
        return d


@dataclass
class Violation:
    code: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationResult:
    ok: bool
    violations: List[Violation] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"ok": self.ok, "violations": [v.to_dict() for v in self.violations]}