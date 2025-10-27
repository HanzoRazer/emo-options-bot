from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path

from src.orchestrator.llm_orchestrator import analyze_nl_request
from src.synthesizer.plan_to_orders import synthesize
from src.gates.policy import evaluate_gates
from src.core.schemas import StagedOrder

def _portfolio_snapshot():
    return {"equity": 100_000.0, "open_positions": 3, "symbol_exposure": {"SPY": 0.07}, "ivr": {"SPY": 0.35}}

def stage_trade_from_text(text: str) -> StagedOrder:
    sketch = analyze_nl_request(text)
    plan = synthesize(sketch)
    gates = evaluate_gates(plan, _portfolio_snapshot())
    staged = StagedOrder(plan=plan, approved=False, gate_outcome=gates)

    out_dir = Path("data") / "staged"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    f = out_dir / f"{ts}_{plan.underlying}_{plan.strategy}.json"
    f.write_text(json.dumps(staged.model_dump(), indent=2))
    return staged

if __name__ == "__main__":
    s = stage_trade_from_text("I think SPY will be range-bound; propose a safe premium strategy.")
    print(json.dumps(s.model_dump(), indent=2))