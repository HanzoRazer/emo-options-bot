from __future__ import annotations
from typing import Dict
from src.core.schemas import TradePlan, GateOutcome

def evaluate_gates(plan: TradePlan, portfolio: Dict) -> GateOutcome:
    v: list[str] = []
    s: list[str] = []

    equity = float(portfolio.get("equity", 0) or 0)
    open_positions = int(portfolio.get("open_positions", 0) or 0)
    symbol_exposure = float(portfolio.get("symbol_exposure", {}).get(plan.underlying, 0.0))

    rc = plan.risk

    # positions cap
    if rc.max_positions and open_positions >= rc.max_positions:
        v.append(f"positions_cap: {open_positions} >= {rc.max_positions}")
        s.append("Close positions or raise max_positions within policy.")

    # portfolio risk %
    if rc.max_risk_pct_equity and equity > 0:
        # simplistic notional from total quantity; replace with greeks/notional calc in Phase 4
        notional = sum(abs(l.quantity) * (l.strike or 0) for l in plan.legs)
        if (notional / equity) > rc.max_risk_pct_equity:
            v.append(f"risk_pct: {notional/equity:.3f} > {rc.max_risk_pct_equity:.3f}")
            s.append("Reduce quantity or tighten spread width.")

    # per-symbol exposure
    if rc.max_symbol_exposure_pct and symbol_exposure > rc.max_symbol_exposure_pct:
        v.append(f"symbol_exposure: {symbol_exposure:.3f} > {rc.max_symbol_exposure_pct:.3f}")
        s.append("Reduce positions in this symbol.")

    # IVR band (if provided by feed)
    ivr = portfolio.get("ivr", {}).get(plan.underlying)
    if ivr is not None:
        if rc.min_ivr is not None and ivr < rc.min_ivr:
            v.append(f"ivr_low: {ivr:.2f} < {rc.min_ivr:.2f}")
            s.append("Skip premium-selling strategies at low IVR.")
        if rc.max_ivr is not None and ivr > rc.max_ivr:
            v.append(f"ivr_high: {ivr:.2f} > {rc.max_ivr:.2f}")
            s.append("Skip long-vol strategies at high IVR.")

    return GateOutcome(ok=(len(v)==0), violations=v, suggested_fixes=s)