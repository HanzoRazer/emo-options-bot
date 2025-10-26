#!/usr/bin/env python
"""
Stage a synthesized trade plan safely to disk for review.
Writes JSON drafts to: data/staged_orders/

Usage:
  python scripts/stage_order_cli.py --symbol SPY --text "market looks sideways"
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
from datetime import datetime

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.phase3.schemas import AnalysisRequest, RiskConstraints
from src.phase3.orchestrator import LLMOrchestrator
from src.phase3.synthesizer import TradeSynthesizer
from src.phase3.gates import RiskGate


STAGED = ROOT / "data" / "staged_orders"
STAGED.mkdir(parents=True, exist_ok=True)


def fake_portfolio():
    return {
        "account_equity": 100000.0,
        "portfolio_risk_used": 0.04,
        # Liquidity check stub: always returns moderate OI
        "option_liquidity": lambda sym, strike, exp, instr: {"oi": 250}
    }


def main():
    p = argparse.ArgumentParser(description="Stage an options trade plan safely.")
    p.add_argument("--symbol", "-s", default="SPY")
    p.add_argument("--text", "-t", required=True, help="Natural language intent, e.g. 'SPY will be range-bound'")
    p.add_argument("--max-risk", type=float, default=0.02, help="Max risk per trade (fraction of equity)")
    p.add_argument("--portfolio-cap", type=float, default=0.10, help="Max portfolio risk (fraction of equity)")
    p.add_argument("--min-oi", type=int, default=100, help="Minimum open interest for legs")
    p.add_argument("--spread-width", type=float, default=5.0, help="Spread width in dollars")
    args = p.parse_args()

    req = AnalysisRequest(user_text=args.text, symbol=args.symbol)
    llm = LLMOrchestrator()
    view = llm.analyze(req)

    synth = TradeSynthesizer()
    constraints = RiskConstraints(
        max_risk_per_trade=args.max_risk,
        max_portfolio_risk=args.portfolio_cap,
        min_option_oi=args.min_oi,
        max_spread_width=args.spread_width,
    )
    plan = synth.synthesize(args.symbol, view, constraints)

    # Hard risk gates
    gate = RiskGate()
    result = gate.validate_trade(plan, fake_portfolio())
    payload = {
        "request": req.to_dict(),
        "llm_view": view,
        "trade_plan": plan.to_dict(),
        "validation": result.to_dict(),
        "staged_at": datetime.utcnow().isoformat() + "Z",
    }

    # Decide filename with status
    status = "OK" if result.ok else "BLOCKED"
    fn = f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}_{args.symbol}_{plan.strategy_type}_{status}.json"
    out = STAGED / fn
    out.write_text(json.dumps(payload, indent=2))
    print(f"Staged: {out}")
    if not result.ok:
        print("Violations:")
        for v in result.violations:
            print(f"  - [{v.code}] {v.message}")


if __name__ == "__main__":
    main()