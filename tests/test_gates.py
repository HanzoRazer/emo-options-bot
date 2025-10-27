from src.core.schemas import TradePlan, OrderLeg
from src.gates.policy import evaluate_gates

def test_positions_cap():
    plan = TradePlan(
        strategy="iron_condor", underlying="SPY",
        legs=[OrderLeg(symbol="SPY", side="sell", instrument="call", strike=470, expiry="2025-12-20", quantity=1)]
    )
    portfolio = {"equity": 100_000, "open_positions": 20, "symbol_exposure": {}, "ivr": {}}
    out = evaluate_gates(plan, portfolio)
    assert not out.ok and any("positions_cap" in v for v in out.violations)