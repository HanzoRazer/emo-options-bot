from __future__ import annotations
from typing import Dict, Any, List
from ..base import Strategy, Order

class PutCreditSpread(Strategy):
    name = "put_credit_spread"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        # Default configuration
        self.min_iv_rank = self.config.get("min_iv_rank", 20)
        self.target_delta = self.config.get("target_delta", 0.20)
        self.spread_width = self.config.get("spread_width", 5)
        self.min_credit = self.config.get("min_credit", 0.25)
        self.max_dte = self.config.get("max_dte", 45)
        self.min_dte = self.config.get("min_dte", 10)

    def validate_snapshot(self, snapshot: Dict[str, Any]) -> bool:
        """Validate snapshot has required fields for Put Credit Spread."""
        required_fields = ["symbol", "ivr", "bias"]
        return all(field in snapshot for field in required_fields)

    def generate(self, snapshot: Dict[str, Any]) -> List[Order]:
        """
        Generate Put Credit Spread orders based on bullish market conditions.
        Put Credit Spread is a bullish strategy that profits from upward price movement.
        """
        if not self.validate_snapshot(snapshot):
            return []
            
        sym = snapshot.get("symbol", "SPY")
        ivr = float(snapshot.get("ivr", 0.0))
        bias = snapshot.get("bias", "neutral")
        dte = snapshot.get("dte", 30)
        support_level = snapshot.get("support_level", None)
        current_price = snapshot.get("current_price", 0)
        
        # Put Credit Spread conditions:
        # 1. Moderate to high IV (profitable premium collection)
        # 2. Bullish market bias
        # 3. Price above strong support levels
        # 4. Appropriate time to expiration
        
        if ivr < self.min_iv_rank:
            return []
            
        if bias not in ["bullish", "neutral_bullish"]:
            return []
            
        if dte > self.max_dte or dte < self.min_dte:
            return []
            
        # Additional safety check: avoid if price is near support
        if support_level and current_price and current_price < support_level * 1.02:
            return []
            
        # Calculate position size based on IV and market strength
        base_qty = 1
        if bias == "bullish" and ivr > 40:
            base_qty = 2  # Increase size in favorable conditions
            
        # Create Put Credit Spread order
        order = Order(
            symbol=sym,
            side="sell",  # Net credit strategy
            qty=base_qty,
            type="put_credit_spread_open",
            meta={
                "strategy": self.name,
                "spread_width": self.spread_width,
                "target_delta": self.target_delta,
                "iv_rank": ivr,
                "dte": dte,
                "bias": bias,
                "support_level": support_level,
                "expected_credit": self.min_credit,
                "risk_note": f"Max loss ~${(self.spread_width - self.min_credit) * 100 * base_qty}",
                "profit_target": f"${int(self.min_credit * 100 * base_qty * 0.5)}",  # 50% credit target
                "beta": 1.2  # Slightly higher beta due to bullish nature
            }
        )
        
        return [order]

    def risk_note(self) -> str:
        return (f"Put Credit Spread: Bullish strategy with max loss = width - credit received. "
                f"Profits if price stays above short put strike. "
                f"Risk increases if price falls below short strike, especially near expiration.")
    
    def get_market_outlook(self) -> str:
        return "Bullish - expects upward or sideways price movement above support levels"