from __future__ import annotations
from typing import Dict, Any, List
from ..base import Strategy, Order

class CoveredCall(Strategy):
    name = "covered_call"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        # Default configuration
        self.target_delta = self.config.get("target_delta", 0.30)
        self.min_premium = self.config.get("min_premium", 0.50)
        self.max_dte = self.config.get("max_dte", 60)
        self.min_dte = self.config.get("min_dte", 15)
        self.shares_per_contract = self.config.get("shares_per_contract", 100)

    def validate_snapshot(self, snapshot: Dict[str, Any]) -> bool:
        """Validate snapshot has required fields for Covered Call."""
        required_fields = ["symbol", "has_shares"]
        return all(field in snapshot for field in required_fields)

    def generate(self, snapshot: Dict[str, Any]) -> List[Order]:
        """
        Generate Covered Call orders when holding the underlying stock.
        Covered Call generates income on existing stock positions.
        """
        if not self.validate_snapshot(snapshot):
            return []
            
        sym = snapshot.get("symbol", "SPY")
        has_shares = bool(snapshot.get("has_shares", False))
        shares_owned = int(snapshot.get("shares_owned", 0))
        current_price = snapshot.get("current_price", 0)
        dte = snapshot.get("dte", 30)
        resistance_level = snapshot.get("resistance_level", None)
        market_outlook = snapshot.get("market_outlook", "neutral")
        
        # Covered Call conditions:
        # 1. Must own the underlying stock
        # 2. Neutral to slightly bullish outlook
        # 3. Adequate premium available
        # 4. Appropriate time to expiration
        
        if not has_shares or shares_owned < self.shares_per_contract:
            return []
            
        if dte > self.max_dte or dte < self.min_dte:
            return []
            
        # Avoid covered calls in strongly bullish markets (would cap gains)
        if market_outlook == "strong_bullish":
            return []
            
        # Calculate number of contracts based on shares owned
        max_contracts = shares_owned // self.shares_per_contract
        
        # Conservative approach: only sell calls on portion of holdings
        contracts_to_sell = max(1, max_contracts // 2)  # Sell calls on half the position
        
        # Adjust strike selection based on market conditions
        target_delta = self.target_delta
        if market_outlook == "bearish":
            target_delta = 0.40  # Closer to money for more premium
        elif market_outlook == "bullish":
            target_delta = 0.20  # Further out of money
            
        # Create Covered Call order
        order = Order(
            symbol=sym,
            side="sell",  # Selling call options
            qty=contracts_to_sell,
            type="covered_call_open",
            meta={
                "strategy": self.name,
                "target_delta": target_delta,
                "shares_owned": shares_owned,
                "shares_covered": contracts_to_sell * self.shares_per_contract,
                "dte": dte,
                "current_price": current_price,
                "resistance_level": resistance_level,
                "market_outlook": market_outlook,
                "min_premium": self.min_premium,
                "risk_note": f"Caps upside at strike price, covers {contracts_to_sell * 100} shares",
                "income_target": f"${int(self.min_premium * 100 * contracts_to_sell)}",
                "beta": 0.9  # Slightly lower beta due to income nature
            }
        )
        
        return [order]

    def risk_note(self) -> str:
        return (f"Covered Call: Income strategy that caps upside potential. "
                f"Risk = opportunity cost if stock price rises above strike. "
                f"Provides downside protection equal to premium received.")
    
    def get_market_outlook(self) -> str:
        return "Neutral to mildly bullish - expects limited upward movement or sideways action"