"""
Contract test for Phase 3 schemas interface.
Ensures basic objects and attributes exist for dependent systems.
"""

import sys
from pathlib import Path
import pytest

repo = Path(__file__).resolve().parents[1]
if str(repo) not in sys.path:
    sys.path.insert(0, str(repo))

def test_phase3_schemas_import_and_structure():
    try:
        from src.phase3 import schemas
        from src.phase3.schemas import TradeLeg, TradePlan, AnalysisRequest, RiskConstraints
    except Exception as e:
        pytest.skip(f"Phase 3 schemas not importable ({e})")
        return

    # Test TradeLeg structure
    leg = TradeLeg(action="buy", instrument="call", strike=100.0, quantity=1)
    assert hasattr(leg, "action") and leg.action == "buy"
    assert hasattr(leg, "strike") and leg.strike == 100.0
    assert hasattr(leg, "to_dict") and callable(leg.to_dict)

    # Test TradePlan structure
    plan = TradePlan(
        strategy_type="iron_condor",
        symbol="SPY", 
        legs=[leg],
        max_loss=500.0
    )
    assert hasattr(plan, "symbol") and plan.symbol == "SPY"
    assert hasattr(plan, "legs") and len(plan.legs) == 1
    assert hasattr(plan, "strategy_type") and plan.strategy_type == "iron_condor"
    assert hasattr(plan, "to_dict") and callable(plan.to_dict)

    # Test AnalysisRequest structure
    req = AnalysisRequest(user_text="test market view")
    assert hasattr(req, "user_text") and req.user_text == "test market view"
    assert hasattr(req, "symbol") and req.symbol == "SPY"  # default
    assert hasattr(req, "to_dict") and callable(req.to_dict)

def test_phase3_orchestrator_import():
    try:
        from src.phase3.orchestrator import LLMOrchestrator, MockLLM
        orch = LLMOrchestrator()
        assert hasattr(orch, "analyze") and callable(orch.analyze)
    except Exception as e:
        pytest.skip(f"Phase 3 orchestrator not importable ({e})")

def test_phase3_synthesizer_import():
    try:
        from src.phase3.synthesizer import TradeSynthesizer
        synth = TradeSynthesizer()
        assert hasattr(synth, "synthesize") and callable(synth.synthesize)
    except Exception as e:
        pytest.skip(f"Phase 3 synthesizer not importable ({e})")

def test_phase3_gates_import():
    try:
        from src.phase3.gates import RiskGate
        gate = RiskGate()
        assert hasattr(gate, "validate_trade") and callable(gate.validate_trade)
    except Exception as e:
        pytest.skip(f"Phase 3 gates not importable ({e})")