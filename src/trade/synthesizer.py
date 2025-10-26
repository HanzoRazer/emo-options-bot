from __future__ import annotations
from typing import List
from src.llm.schemas import MarketView, SynthesizedTrade, Leg, SynthesisResult, RiskViolation

class TradeSynthesizer:
    """Deterministic, testable synthesis from MarketView -> options structure.
    No broker calls here; this just shapes trades."""
    def synthesize(self, mv: MarketView) -> SynthesisResult:
        symbol = mv.symbol
        # Simple mapping for demo purposes:
        if mv.outlook in ("neutral","range"):
            legs: List[Leg] = [
                Leg(action="sell", instrument="put", strike=100.0, quantity=1),
                Leg(action="buy",  instrument="put", strike=95.0,  quantity=1),
                Leg(action="sell", instrument="call", strike=110.0, quantity=1),
                Leg(action="buy",  instrument="call", strike=115.0, quantity=1),
            ]
            trade = SynthesizedTrade(strategy_type="iron_condor", symbol=symbol, legs=legs,
                                     max_risk=500.0, target_credit=100.0,
                                     rationale=f"Neutral-range outlook ({mv.outlook})")
            return SynthesisResult(trade=trade, ok=True, violations=[])
        elif mv.outlook in ("bullish",):
            legs = [
                Leg(action="sell", instrument="put", strike=100.0, quantity=1),
                Leg(action="buy",  instrument="put", strike=95.0,  quantity=1),
            ]
            trade = SynthesizedTrade(strategy_type="put_credit_spread", symbol=symbol, legs=legs,
                                     max_risk=500.0, target_credit=80.0,
                                     rationale="Bullish outlook (credit put spread)")
            return SynthesisResult(trade=trade, ok=True, violations=[])
        elif mv.outlook in ("bearish",):
            legs = [
                Leg(action="sell", instrument="call", strike=110.0, quantity=1),
                Leg(action="buy",  instrument="call", strike=115.0, quantity=1),
            ]
            trade = SynthesizedTrade(strategy_type="call_credit_spread", symbol=symbol, legs=legs,
                                     max_risk=500.0, target_credit=80.0,
                                     rationale="Bearish outlook (credit call spread)")
            return SynthesisResult(trade=trade, ok=True, violations=[])
        else:  # "volatile"
            legs = [
                Leg(action="buy", instrument="call", strike=105.0, quantity=1),
                Leg(action="buy", instrument="put",  strike=95.0,  quantity=1),
            ]
            trade = SynthesizedTrade(strategy_type="long_straddle", symbol=symbol, legs=legs,
                                     rationale="Volatility outlook (long straddle)")
            # Example soft warning:
            return SynthesisResult(trade=trade, ok=True, violations=[
                RiskViolation(rule="vega_risk", detail="Long vol structure; monitor IV crush", severity="warn")
            ])