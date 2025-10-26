from __future__ import annotations
import json, os, time, uuid, pathlib
from typing import Dict, Any, List

from .fake_market import generate_snapshot, to_dict
from .mock_llm import mock_analyze

# ---- Try real Phase 3 components if available; fall back to shims ----------
try:
    from synthesizer import synthesize_trade  # your real function
except Exception:
    def synthesize_trade(symbol: str, plan: dict, snapshot: dict) -> dict:
        """Minimal synthesizer shim (iron condor / PCS / straddle).
        Output schema matches a typical staged multi-leg order.
        """
        px = snapshot["price"]
        strat = plan["strategy"]
        width = int(plan.get("meta",{}).get("width", 5))
        qty   = max(1, int(plan["risk_budget"] // 500))
        legs: List[dict] = []
        if strat == "iron_condor":
            # symmetric around spot
            call_short = round(px + 2*width, 1)
            call_long  = round(call_short + width, 1)
            put_short  = round(px - 2*width, 1)
            put_long   = round(put_short - width, 1)
            legs = [
                {"action":"sell","type":"call","strike":call_short,"qty":qty},
                {"action":"buy", "type":"call","strike":call_long, "qty":qty},
                {"action":"sell","type":"put", "strike":put_short, "qty":qty},
                {"action":"buy", "type":"put", "strike":put_long,  "qty":qty},
            ]
        elif strat == "straddle":
            k = round(px, 1)
            legs = [
                {"action":"buy","type":"call","strike":k,"qty":qty},
                {"action":"buy","type":"put", "strike":k,"qty":qty},
            ]
        else:
            # put credit spread
            k_short = round(px * 0.97, 1)
            k_long  = round(k_short - width, 1)
            legs = [
                {"action":"sell","type":"put","strike":k_short,"qty":qty},
                {"action":"buy", "type":"put","strike":k_long, "qty":qty},
            ]
        return {
            "symbol": symbol,
            "strategy": strat,
            "legs": legs,
            "risk_budget": plan["risk_budget"],
            "thesis": plan["thesis"],
            "ts": time.time(),
            "meta": plan.get("meta",{}),
        }

try:
    from gates import validate_trade  # your real hard risk-gate validator
except Exception:
    def validate_trade(order: dict, portfolio: dict, equity: float) -> dict:
        """Very small hard-limit shim."""
        max_per_trade = 0.02  # 2%
        max_total     = 0.10  # 10%
        violations = []
        if order.get("risk_budget", 0) > equity * max_per_trade:
            violations.append(f"risk_budget exceeds 2% of equity (>{equity*max_per_trade:.0f})")
        if portfolio.get("risk_allocated", 0) + order.get("risk_budget", 0) > equity * max_total:
            violations.append("portfolio risk allocation would exceed 10%")
        liquid_ok = True  # insert liquidity checks if desired
        if not liquid_ok:
            violations.append("liquidity check failed")
        return {"ok": len(violations) == 0, "violations": violations}

# ---- Orchestrated run -------------------------------------------------------
def run_phase3_flow(
    request_text: str,
    symbols: list[str] = ["SPY", "QQQ"],
    equity: float = 100_000.0,
    staged_dir: str | os.PathLike = "data/staged_orders"
) -> Dict[str, Any]:
    os.makedirs(staged_dir, exist_ok=True)
    snaps = generate_snapshot(symbols)
    llm_plan = mock_analyze(request_text)

    # Use first symbol for the demo (extend to multi-symbol if desired)
    sym = symbols[0]
    order = synthesize_trade(
        symbol=sym,
        plan={"strategy": llm_plan.strategy, "risk_budget": llm_plan.risk_budget,
              "thesis": llm_plan.thesis, "meta": llm_plan.meta},
        snapshot=to_dict(snaps)[sym],
    )

    # simple portfolio stub
    portfolio = {"risk_allocated": 0.0}
    gate = validate_trade(order, portfolio, equity)

    artifact = {
        "request": request_text,
        "snapshot": to_dict(snaps),
        "plan": {
            "strategy": llm_plan.strategy,
            "risk_budget": llm_plan.risk_budget,
            "thesis": llm_plan.thesis,
            "meta": llm_plan.meta,
        },
        "order": order,
        "gate": gate,
        "status": "ok" if gate.get("ok") else "blocked",
    }

    fname = f"{int(time.time())}_{sym}_{uuid.uuid4().hex[:8]}.json"
    fpath = pathlib.Path(staged_dir) / fname
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    return {"artifact_path": str(fpath), "result": artifact}