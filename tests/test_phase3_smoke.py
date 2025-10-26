from pathlib import Path
import json
from src.phase3.schemas import AnalysisRequest, RiskConstraints
from src.phase3.orchestrator import LLMOrchestrator
from src.phase3.synthesizer import TradeSynthesizer
from src.phase3.gates import RiskGate


def test_phase3_flow(tmp_path: Path):
    req = AnalysisRequest(user_text="I expect SPY to be sideways")
    llm = LLMOrchestrator()
    view = llm.analyze(req)
    assert view["view"] in {"neutral", "high_vol", "bullish", "bearish"}

    synth = TradeSynthesizer()
    plan = synth.synthesize("SPY", view, RiskConstraints())
    assert plan.legs and plan.strategy_type
    assert plan.max_loss and plan.max_loss > 0

    gate = RiskGate()
    portfolio = {
        "account_equity": 100000.0,
        "portfolio_risk_used": 0.05,
        "option_liquidity": lambda sym, strike, exp, instr: {"oi": 999},
    }
    res = gate.validate_trade(plan, portfolio)
    assert res.ok is True

    # Stage to tmp as proof-of-life
    staged = tmp_path / "stage.json"
    staged.write_text(json.dumps({
        "request": req.to_dict(),
        "llm_view": view,
        "trade_plan": plan.to_dict(),
        "validation": res.to_dict(),
    }, indent=2))
    assert staged.exists()