from __future__ import annotations
from typing import Dict, Any, List
from ..base import Strategy, Order

class IronCondor(Strategy):
    name = "iron_condor"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        # Default configuration
        self.min_iv_rank = self.config.get("min_iv_rank", 30)
        self.target_delta = self.config.get("target_delta", 0.15)
        self.wing_width = self.config.get("wing_width", 5)
        self.min_credit = self.config.get("min_credit", 0.30)
        self.max_dte = self.config.get("max_dte", 45)
        self.min_dte = self.config.get("min_dte", 15)

    def validate_snapshot(self, snapshot: Dict[str, Any]) -> bool:
        """Validate snapshot has required fields for Iron Condor."""
        required_fields = ["symbol", "ivr"]
        return all(field in snapshot for field in required_fields)

    def generate(self, snapshot: Dict[str, Any]) -> List[Order]:
        """
        Generate Iron Condor orders based on market conditions.
        Iron Condor is a neutral strategy that profits from low volatility.
        """
        if not self.validate_snapshot(snapshot):
            return []
            
        sym = snapshot.get("symbol", "SPY")
        ivr = float(snapshot.get("ivr", 0.0))
        dte = snapshot.get("dte", 30)  # Days to expiration
        market_trend = snapshot.get("market_trend", "neutral")
        
        # Iron Condor conditions:
        # 1. High IV Rank (expensive options)
        # 2. Neutral market expectation
        # 3. Appropriate time to expiration
        
        if ivr < self.min_iv_rank:
            return []
            
        if dte > self.max_dte or dte < self.min_dte:
            return []
            
        # Prefer neutral markets, avoid strong trends
        if market_trend in ["strong_bullish", "strong_bearish"]:
            return []
            
        # Calculate position size based on account and volatility
        base_qty = 1
        vol_adjustment = min(2.0, ivr / 30.0)  # Increase size with higher IV
        adjusted_qty = max(1, int(base_qty * vol_adjustment))
        
        # Create Iron Condor order
        order = Order(
            symbol=sym,
            side="sell",  # Net credit strategy
            qty=adjusted_qty,
            type="iron_condor_open",
            meta={
                "strategy": self.name,
                "wing_width": self.wing_width,
                "target_delta": self.target_delta,
                "iv_rank": ivr,
                "dte": dte,
                "market_trend": market_trend,
                "expected_credit": self.min_credit,
                "risk_note": f"Max loss ~${self.wing_width * 100 * adjusted_qty}, Target profit ~${int(self.min_credit * 100 * adjusted_qty)}",
                "beta": 0.8  # Lower beta due to neutral nature
            }
        )
        
        return [order]

    def risk_note(self) -> str:
        return (f"Iron Condor: Neutral strategy with max loss = wing width (${self.wing_width * 100}). "
                f"Profits from time decay when price stays between short strikes. "
                f"Risk increases near expiration if price approaches strikes.")
    
    def get_market_outlook(self) -> str:
        return "Neutral - expects low volatility and sideways price movement"