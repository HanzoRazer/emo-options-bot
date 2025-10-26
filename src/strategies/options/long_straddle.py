from __future__ import annotations
from typing import Dict, Any, List
from ..base import Strategy, Order

class LongStraddle(Strategy):
    name = "long_straddle"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        # Default configuration
        self.min_iv_rank = self.config.get("min_iv_rank", 15)  # Lower than other strategies
        self.max_iv_rank = self.config.get("max_iv_rank", 70)  # Don't buy when IV too high
        self.target_dte = self.config.get("target_dte", 30)
        self.max_dte = self.config.get("max_dte", 60)
        self.min_dte = self.config.get("min_dte", 7)
        self.min_expected_move = self.config.get("min_expected_move", 0.03)  # 3% minimum expected move

    def validate_snapshot(self, snapshot: Dict[str, Any]) -> bool:
        """Validate snapshot has required fields for Long Straddle."""
        required_fields = ["symbol", "event"]
        return all(field in snapshot for field in required_fields)

    def generate(self, snapshot: Dict[str, Any]) -> List[Order]:
        """
        Generate Long Straddle orders around high-impact events.
        Long Straddle profits from large price movements in either direction.
        """
        if not self.validate_snapshot(snapshot):
            return []
            
        sym = snapshot.get("symbol", "SPY")
        event = snapshot.get("event", "")
        days_to_event = snapshot.get("days_to_event", 30)
        dte = snapshot.get("dte", 30)
        iv_rank = float(snapshot.get("iv_rank", 0.0))
        expected_move = float(snapshot.get("expected_move", 0.0))
        current_price = snapshot.get("current_price", 0)
        
        # Long Straddle conditions:
        # 1. Major event expected (earnings, FOMC, etc.)
        # 2. IV not too high (avoid overpaying)
        # 3. Sufficient expected move to overcome time decay
        # 4. Appropriate timing relative to event
        
        # Check for major events
        major_events = ["earnings", "fomc", "fed", "election", "announcement", "merger"]
        has_major_event = any(event_type in event.lower() for event_type in major_events)
        
        if not has_major_event:
            return []
            
        # IV should be reasonable (not too high to avoid overpaying)
        if iv_rank < self.min_iv_rank or iv_rank > self.max_iv_rank:
            return []
            
        # Time to event should be appropriate
        if days_to_event > 7 or days_to_event < 0:  # Event should be within a week
            return []
            
        # DTE should be close to event
        if dte > self.max_dte or dte < self.min_dte:
            return []
            
        # Expected move should justify the premium
        if expected_move < self.min_expected_move:
            return []
            
        # Calculate position size based on event importance and expected move
        base_qty = 1
        if expected_move > 0.05:  # 5%+ expected move
            base_qty = 2
        if "earnings" in event.lower() and expected_move > 0.08:  # 8%+ earnings move
            base_qty = 3
            
        # Reduce size if event is far away or DTE is long
        if days_to_event > 3 or dte > 21:
            base_qty = max(1, base_qty - 1)
            
        # Create Long Straddle order
        order = Order(
            symbol=sym,
            side="buy",  # Long strategy (debit)
            qty=base_qty,
            type="long_straddle_open",
            meta={
                "strategy": self.name,
                "event": event,
                "days_to_event": days_to_event,
                "dte": dte,
                "iv_rank": iv_rank,
                "expected_move": expected_move,
                "current_price": current_price,
                "breakeven_up": current_price * (1 + expected_move) if current_price else 0,
                "breakeven_down": current_price * (1 - expected_move) if current_price else 0,
                "risk_note": f"Max loss = premium paid, profits if move > {expected_move:.1%}",
                "time_decay_risk": "High - loses value daily if price doesn't move",
                "beta": 1.5  # Higher beta due to volatility exposure
            }
        )
        
        return [order]

    def risk_note(self) -> str:
        return (f"Long Straddle: High-risk/high-reward strategy requiring large moves. "
                f"Max loss = total premium paid. Loses value rapidly from time decay. "
                f"Profits only if move exceeds breakeven points.")
    
    def get_market_outlook(self) -> str:
        return "High volatility expected - anticipates large price movement in either direction"