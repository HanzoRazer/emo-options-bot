"""
Iron Condor strategy using signals-based framework.
"""

from typing import Dict, Any, List
from .base import BaseStrategy, Signal


class IronCondor(BaseStrategy):
    """
    Iron Condor strategy for neutral market conditions with high IV.
    
    This strategy generates signals when:
    - IV Rank is elevated (typically > 25%)
    - Market trend is sideways or mixed
    - Suitable for collecting premium in range-bound markets
    """
    
    name = "IronCondor"

    def __init__(self, config: Dict[str, Any] | None = None):
        """
        Initialize Iron Condor strategy.
        
        Default config:
            min_ivr: 0.25 (minimum IV rank to consider entry)
            max_ivr: 0.80 (maximum IV rank for safety)
            hold_threshold: 0.40 (confidence threshold for hold vs enter)
        """
        default_config = {
            "min_ivr": 0.25,
            "max_ivr": 0.80,
            "hold_threshold": 0.40
        }
        
        if config:
            default_config.update(config)
            
        super().__init__(default_config)

    def evaluate(self, md: Dict[str, Any]) -> List[Signal]:
        """
        Evaluate market conditions for Iron Condor opportunities.
        
        Args:
            md: Market data dict with keys:
                - symbol: Trading symbol
                - ivr: IV rank (0.0 to 1.0)
                - trend: Market trend ("up", "down", "sideways", "mixed")
                - Optional: price, volume, etc.
                
        Returns:
            List containing one Signal with Iron Condor recommendation
        """
        if not self.validate_market_data(md):
            return []

        symbol = md.get("symbol", "SPY")
        ivr = float(md.get("ivr", 0.0))
        trend = md.get("trend", "mixed")
        
        # Get configuration parameters
        min_ivr = float(self.get_config("min_ivr", 0.25))
        max_ivr = float(self.get_config("max_ivr", 0.80))
        hold_threshold = float(self.get_config("hold_threshold", 0.40))

        # Calculate base confidence from IV rank
        if ivr >= min_ivr and ivr <= max_ivr:
            # Higher IV = higher confidence, but cap it
            base_confidence = min(0.9, 0.3 + (ivr - min_ivr) * 2.0)
        else:
            base_confidence = 0.2

        # Adjust confidence based on trend
        trend_multiplier = {
            "sideways": 1.2,    # Best for Iron Condor
            "mixed": 1.0,       # Good for Iron Condor  
            "up": 0.7,          # Less ideal but possible
            "down": 0.7         # Less ideal but possible
        }.get(trend, 0.8)

        final_confidence = min(1.0, base_confidence * trend_multiplier)

        # Determine action based on confidence
        if final_confidence >= hold_threshold and ivr >= min_ivr and trend in {"sideways", "mixed"}:
            action = "enter"
            notes = f"IVR={ivr:.2f} (>{min_ivr:.2f}), trend={trend} - favorable for premium collection"
        elif final_confidence >= 0.3:
            action = "hold"
            notes = f"IVR={ivr:.2f}, trend={trend} - monitoring conditions"
        else:
            action = "hold"
            notes = f"IVR={ivr:.2f} (<{min_ivr:.2f}) or trend={trend} - unfavorable conditions"

        signal = Signal(
            ts=Signal.now_iso(),
            symbol=symbol,
            strategy=self.name,
            action=action,
            confidence=final_confidence,
            notes=notes
        )

        return [signal]

    def warmup(self, **kwargs) -> None:
        """Initialize Iron Condor strategy."""
        super().warmup(**kwargs)
        print(f"[{self.name}] Warmed up with config: {self.config}")

    def validate_market_data(self, md: Dict[str, Any]) -> bool:
        """
        Validate market data for Iron Condor strategy.
        
        Required fields: symbol, ivr, trend
        """
        required_fields = ["symbol", "ivr", "trend"]
        return all(field in md for field in required_fields)