from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass
class Order:
    symbol: str
    side: str          # "buy" / "sell"
    qty: int
    type: str = "market"
    price: Optional[float] = None
    time_in_force: str = "DAY"
    meta: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert order to dictionary for serialization."""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "qty": self.qty,
            "type": self.type,
            "price": self.price,
            "time_in_force": self.time_in_force,
            "meta": self.meta or {}
        }

class Strategy:
    name: str = "base"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.performance_metrics = {
            "total_trades": 0,
            "winning_trades": 0,
            "total_pnl": 0.0,
            "max_drawdown": 0.0
        }

    def warmup(self, market_data: Any) -> None:
        """Optional pre-compute indicators."""
        return

    def generate(self, snapshot: Dict[str, Any]) -> List[Order]:
        """
        Produce a list of desired orders given current snapshot/context.
        Must be overridden by child strategies.
        """
        return []

    def risk_note(self) -> str:
        """Return risk assessment note for this strategy."""
        return "No risk note."
    
    def validate_snapshot(self, snapshot: Dict[str, Any]) -> bool:
        """Validate that snapshot contains required data for this strategy."""
        required_fields = ["symbol"]
        return all(field in snapshot for field in required_fields)
    
    def update_performance(self, trade_result: Dict[str, Any]) -> None:
        """Update strategy performance metrics."""
        self.performance_metrics["total_trades"] += 1
        
        pnl = trade_result.get("pnl", 0.0)
        self.performance_metrics["total_pnl"] += pnl
        
        if pnl > 0:
            self.performance_metrics["winning_trades"] += 1
    
    def get_win_rate(self) -> float:
        """Calculate win rate."""
        if self.performance_metrics["total_trades"] == 0:
            return 0.0
        return self.performance_metrics["winning_trades"] / self.performance_metrics["total_trades"]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get strategy performance summary."""
        return {
            "name": self.name,
            "total_trades": self.performance_metrics["total_trades"],
            "win_rate": self.get_win_rate(),
            "total_pnl": self.performance_metrics["total_pnl"],
            "max_drawdown": self.performance_metrics["max_drawdown"]
        }