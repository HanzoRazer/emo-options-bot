from __future__ import annotations
from typing import List
from src.llm.schemas import SynthesizedTrade, RiskViolation

class RiskGate:
    """Hard gates: must not pass if violation severity='block'."""
    def __init__(self,
                 max_risk_per_trade: float = 0.02,     # 2% of equity
                 max_total_positions: int = 20):
        self.max_risk_per_trade = max_risk_per_trade
        self.max_total_positions = max_total_positions

    def validate_trade(self,
                       trade: SynthesizedTrade,
                       account_equity: float,
                       open_positions_count: int) -> List[RiskViolation]:
        violations: List[RiskViolation] = []
        # Gate 1: per-trade risk (if provided)
        if trade.max_risk is not None:
            allowed = self.max_risk_per_trade * account_equity
            if trade.max_risk > allowed:
                violations.append(RiskViolation(
                    rule="max_trade_risk",
                    detail=f"Requested {trade.max_risk:.2f} > allowed {allowed:.2f}",
                    severity="block"
                ))
        # Gate 2: open positions cap
        if open_positions_count >= self.max_total_positions:
            violations.append(RiskViolation(
                rule="position_cap",
                detail=f"Open positions {open_positions_count} exceed cap {self.max_total_positions}",
                severity="block"
            ))
        return violations