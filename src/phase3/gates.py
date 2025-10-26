from __future__ import annotations
from typing import Dict, Any, List
from .schemas import TradePlan, ValidationResult, Violation


class RiskGate:
    """
    Hard risk guardrails that cannot be bypassed.
    Expects `portfolio` to supply minimal context:
      - account_equity: float
      - portfolio_risk_used: float (0..1)
      - option_liquidity(symbol, strike, expiration, instrument) -> dict(oi: int)
    """
    def __init__(self):
        pass

    def validate_trade(self, trade: TradePlan, portfolio: Dict[str, Any]) -> ValidationResult:
        v: List[Violation] = []
        equity = float(portfolio.get("account_equity", 0.0))
        port_risk_used = float(portfolio.get("portfolio_risk_used", 0.0))  # fraction 0..1
        constraints = trade.constraints

        # 1) Max risk per trade (requires trade.max_loss)
        if trade.max_loss is not None and equity > 0:
            risk_frac = float(trade.max_loss) / equity
            if risk_frac > constraints.max_risk_per_trade:
                v.append(Violation(
                    code="MAX_RISK_TRADE",
                    message=f"Trade risk {risk_frac:.3f} exceeds max {constraints.max_risk_per_trade:.3f}",
                    context={"trade_max_loss": trade.max_loss, "equity": equity}
                ))

        # 2) Portfolio aggregate risk cap
        projected = port_risk_used
        if trade.max_loss is not None and equity > 0:
            projected += float(trade.max_loss) / equity
        if projected > constraints.max_portfolio_risk:
            v.append(Violation(
                code="MAX_PORTFOLIO_RISK",
                message=f"Projected portfolio risk {projected:.3f} exceeds cap {constraints.max_portfolio_risk:.3f}",
                context={"portfolio_risk_used": port_risk_used}
            ))

        # 3) Liquidity minimums (mock: rely on portfolio.option_liquidity if present)
        liq_fn = portfolio.get("option_liquidity")
        if callable(liq_fn):
            for leg in trade.legs:
                info = liq_fn(trade.symbol, leg.strike, leg.expiration, leg.instrument)
                oi = int(info.get("oi", 0))
                if oi < constraints.min_option_oi:
                    v.append(Violation(
                        code="INSUFFICIENT_LIQUIDITY",
                        message=f"Open interest {oi} below minimum {constraints.min_option_oi}",
                        context={"leg": leg.to_dict()}
                    ))

        # 4) Spread width sanity (for two-leg verticals; basic heuristic)
        if trade.strategy_type in ("put_credit_spread", "call_credit_spread") and len(trade.legs) == 2:
            strikes = sorted([float(l.strike) for l in trade.legs])
            width = abs(strikes[1] - strikes[0])
            if width > constraints.max_spread_width:
                v.append(Violation(
                    code="SPREAD_TOO_WIDE",
                    message=f"Spread width {width:.2f} exceeds max {constraints.max_spread_width:.2f}",
                    context={"strikes": strikes}
                ))

        return ValidationResult(ok=(len(v) == 0), violations=v)