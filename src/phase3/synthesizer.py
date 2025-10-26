from __future__ import annotations
from typing import Dict, Any, List
from dataclasses import dataclass
from .schemas import TradePlan, TradeLeg, RiskConstraints


@dataclass
class SynthesisSettings:
    put_spread_delta: float = -0.20
    call_spread_delta: float = 0.20
    condor_short_delta: float = 0.15
    spread_width: float = 5.0
    default_qty: int = 1


class TradeSynthesizer:
    """
    Converts high-level 'view' into a concrete, risk-defined options structure
    using simple delta/width heuristics (no broker dependency).
    """
    def __init__(self, settings: SynthesisSettings | None = None):
        self.s = settings or SynthesisSettings()

    def _build_put_credit_spread(self, symbol: str, width: float, qty: int) -> List[TradeLeg]:
        # Synthetic placeholder: choose two strikes separated by width
        # (In production, find strikes via chain and targeted delta)
        short_strike = 100.0  # placeholder
        long_strike = short_strike - width
        return [
            TradeLeg(action="sell", instrument="put", strike=short_strike, quantity=qty),
            TradeLeg(action="buy", instrument="put", strike=long_strike, quantity=qty),
        ]

    def _build_call_credit_spread(self, symbol: str, width: float, qty: int) -> List[TradeLeg]:
        short_strike = 100.0
        long_strike = short_strike + width
        return [
            TradeLeg(action="sell", instrument="call", strike=short_strike, quantity=qty),
            TradeLeg(action="buy", instrument="call", strike=long_strike, quantity=qty),
        ]

    def _build_iron_condor(self, symbol: str, width: float, qty: int) -> List[TradeLeg]:
        put_side = self._build_put_credit_spread(symbol, width, qty)
        call_side = self._build_call_credit_spread(symbol, width, qty)
        return put_side + call_side

    def synthesize(self, symbol: str, llm_view: Dict[str, Any], constraints: RiskConstraints | None = None) -> TradePlan:
        view = llm_view.get("view", "neutral")
        constraints = constraints or RiskConstraints()
        qty = int(llm_view.get("suggested_qty", self.s.default_qty))
        width = float(llm_view.get("spread_width", self.s.spread_width))

        if view == "neutral":
            strategy = "iron_condor"
            legs = self._build_iron_condor(symbol, width, qty)
            rationale = "Neutral view → theta-positive iron condor"
        elif view == "high_vol":
            # For high vol, also consider iron condor (rich premium), but could add strangle later
            strategy = "iron_condor"
            legs = self._build_iron_condor(symbol, width, qty)
            rationale = "High-vol view → credit strategy to harvest IV"
        elif view == "bullish":
            strategy = "put_credit_spread"
            legs = self._build_put_credit_spread(symbol, width, qty)
            rationale = "Bullish view → sell downside skew via put credit spread"
        elif view == "bearish":
            strategy = "call_credit_spread"
            legs = self._build_call_credit_spread(symbol, width, qty)
            rationale = "Bearish view → sell topside via call credit spread"
        else:
            strategy = "iron_condor"
            legs = self._build_iron_condor(symbol, width, qty)
            rationale = "Fallback neutral strategy"

        # Heuristic max loss (width * qty * 100)
        max_loss = width * qty * 100.0
        return TradePlan(
            strategy_type=strategy,
            symbol=symbol,
            legs=legs,
            max_loss=max_loss,
            target_credit=None,
            rationale=rationale,
            constraints=constraints,
            metadata={"llm_view": llm_view}
        )