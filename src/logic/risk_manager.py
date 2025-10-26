"""
RiskManager: pre-trade & ongoing risk controls for EMO Options Bot.

Features
- Portfolio heat limit (percent of equity at risk across open positions)
- Per-position risk cap
- Max concurrent positions
- Max correlation guardrail (soft throttle for highly correlated names)
- Max drawdown circuit breaker (uses rolling equity curve)
- Simple beta exposure ceiling (optional)

NOTE: This is broker-agnostic; you provide a portfolio snapshot.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
import math
import time

@dataclass
class Position:
    symbol: str
    qty: float
    mark: float
    value: float                 # qty * mark (signed)
    max_loss: float              # estimated worst-case loss for the position
    beta: float = 1.0            # beta to market (equities ~1, options ~varies)
    sector: Optional[str] = None # optional metadata

@dataclass
class PortfolioSnapshot:
    equity: float
    cash: float
    positions: List[Position] = field(default_factory=list)
    # optional recent equity to track drawdown; RiskManager will also record
    equity_ts: List[Tuple[float, float]] = field(default_factory=list)  # (epoch_sec, equity)

@dataclass
class OrderIntent:
    symbol: str
    side: str        # "buy", "sell", "open", "close"
    est_max_loss: float
    est_value: float # notional | credit/debit magnitude (signed ok)
    correlation_hint: Optional[float] = None  # +1 to -1 vs portfolio core
    beta: float = 1.0

class RiskManager:
    """
    Typical defaults:
    - portfolio_risk_cap: 0.20 => at most 20% of equity at risk across open positions
    - per_position_risk: 0.02  => 2% of equity per single new position worst-case
    - max_drawdown: 0.12       => 12% drawdown pause
    """

    def __init__(
        self,
        portfolio_risk_cap: float = 0.20,
        per_position_risk: float = 0.02,
        max_positions: int = 12,
        max_correlation: float = 0.85,
        max_beta_exposure: float = 2.5,
        max_drawdown: float = 0.12,
        min_equity: float = 10_000.0,
    ):
        self.portfolio_risk_cap = float(portfolio_risk_cap)
        self.per_position_risk  = float(per_position_risk)
        self.max_positions      = int(max_positions)
        self.max_correlation    = float(max_correlation)
        self.max_beta_exposure  = float(max_beta_exposure)
        self.max_drawdown       = float(max_drawdown)
        self.min_equity         = float(min_equity)

        # internal drawdown memory
        self._equity_curve: List[Tuple[float, float]] = []  # (ts, equity)
        self._peak_equity: float = 0.0

    # -------- drawdown tracking ------------------------------------------------
    def record_equity(self, equity: float, ts: Optional[float] = None) -> None:
        ts = time.time() if ts is None else ts
        self._equity_curve.append((ts, float(equity)))
        if equity > self._peak_equity:
            self._peak_equity = float(equity)

    def current_drawdown(self) -> float:
        if self._peak_equity <= 0:
            return 0.0
        latest = self._equity_curve[-1][1] if self._equity_curve else self._peak_equity
        return max(0.0, 1.0 - (latest / self._peak_equity))

    def drawdown_breached(self) -> bool:
        return self.current_drawdown() >= self.max_drawdown

    # -------- risk calculations ------------------------------------------------
    def _portfolio_risk_used(self, pf: PortfolioSnapshot) -> float:
        """Return sum(max_loss) across open positions."""
        return sum(max(0.0, p.max_loss) for p in pf.positions)

    def _portfolio_beta(self, pf: PortfolioSnapshot) -> float:
        """Crude beta exposure proxy (|sum(beta * value)| / equity)."""
        if pf.equity <= 1e-9:
            return 0.0
        gross_beta_value = sum((p.beta * p.value) for p in pf.positions)
        return abs(gross_beta_value) / pf.equity

    # -------- public API -------------------------------------------------------
    def assess_portfolio(self, pf: PortfolioSnapshot) -> Dict:
        heat_used = self._portfolio_risk_used(pf)
        heat_cap  = self.portfolio_risk_cap * pf.equity
        beta_exp  = self._portfolio_beta(pf)

        return {
            "equity": pf.equity,
            "cash": pf.cash,
            "positions": len(pf.positions),
            "risk_used": heat_used,
            "risk_cap": heat_cap,
            "risk_util": (heat_used / heat_cap) if heat_cap > 0 else 0.0,
            "beta_exposure": beta_exp,
            "drawdown": self.current_drawdown(),
            "drawdown_breached": self.drawdown_breached(),
        }

    def validate_order(self, order: OrderIntent, pf: PortfolioSnapshot) -> Tuple[bool, List[str]]:
        reasons: List[str] = []

        # sanity
        if pf.equity < self.min_equity:
            reasons.append(f"Equity below minimum threshold (${self.min_equity:,.0f})")

        # drawdown breaker
        if self.drawdown_breached():
            reasons.append(f"Max drawdown breached ({self.current_drawdown():.1%} >= {self.max_drawdown:.1%})")

        # position count
        if len(pf.positions) >= self.max_positions:
            reasons.append(f"Max positions reached ({self.max_positions})")

        # per-position risk
        per_pos_cap = self.per_position_risk * pf.equity
        if order.est_max_loss > per_pos_cap + 1e-9:
            reasons.append(f"Per-position risk cap exceeded "
                           f"({order.est_max_loss:,.2f} > {per_pos_cap:,.2f})")

        # portfolio heat
        new_heat = self._portfolio_risk_used(pf) + max(0.0, order.est_max_loss)
        heat_cap = self.portfolio_risk_cap * pf.equity
        if new_heat > heat_cap + 1e-9:
            reasons.append(f"Portfolio heat cap exceeded "
                           f"({new_heat:,.2f} > {heat_cap:,.2f})")

        # correlation throttle (soft)
        if order.correlation_hint is not None and order.correlation_hint > self.max_correlation:
            reasons.append(f"High correlation to book ({order.correlation_hint:.2f} > {self.max_correlation:.2f})")

        # beta exposure ceiling (soft)
        beta_after = self._portfolio_beta(pf) + abs(order.beta * order.est_value) / max(pf.equity, 1e-9)
        if beta_after > self.max_beta_exposure:
            reasons.append(f"Beta exposure would exceed ceiling ({beta_after:.2f} > {self.max_beta_exposure:.2f})")

        return (len(reasons) == 0), reasons