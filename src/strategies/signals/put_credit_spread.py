"""
Put Credit Spread strategy using signals-based framework.
"""

from typing import Dict, Any, List
from .base import BaseStrategy, Signal


class PutCreditSpread(BaseStrategy):
    """
    Put Credit Spread strategy for bullish to neutral market conditions.
    
    This strategy generates signals when:
    - IV Rank is moderately elevated (typically > 15%)
    - Market trend is bullish or sideways
    - Suitable for generating income while maintaining bullish bias
    """
    
    name = "PutCreditSpread"

    def __init__(self, config: Dict[str, Any] | None = None):
        """
        Initialize Put Credit Spread strategy.
        
        Default config:
            min_ivr: 0.15 (minimum IV rank to consider entry)
            max_ivr: 0.75 (maximum IV rank for safety)
            hold_threshold: 0.35 (confidence threshold for hold vs enter)
            bearish_penalty: 0.5 (confidence reduction for bearish trends)
        """
        default_config = {
            "min_ivr": 0.15,
            "max_ivr": 0.75,
            "hold_threshold": 0.35,
            "bearish_penalty": 0.5
        }
        
        if config:
            default_config.update(config)
            
        super().__init__(default_config)

    def evaluate(self, md: Dict[str, Any]) -> List[Signal]:
        """
        Evaluate market conditions for Put Credit Spread opportunities.
        
        Args:
            md: Market data dict with keys:
                - symbol: Trading symbol
                - ivr: IV rank (0.0 to 1.0)
                - trend: Market trend ("up", "down", "sideways", "mixed")
                - Optional: support_level, resistance_level, etc.
                
        Returns:
            List containing one Signal with Put Credit Spread recommendation
        """
        if not self.validate_market_data(md):
            return []

        symbol = md.get("symbol", "SPY")
        ivr = float(md.get("ivr", 0.0))
        trend = md.get("trend", "up")
        
        # Get configuration parameters
        min_ivr = float(self.get_config("min_ivr", 0.15))
        max_ivr = float(self.get_config("max_ivr", 0.75))
        hold_threshold = float(self.get_config("hold_threshold", 0.35))
        bearish_penalty = float(self.get_config("bearish_penalty", 0.5))

        # Calculate base confidence from IV rank
        if ivr >= min_ivr and ivr <= max_ivr:
            # Scale confidence based on IV rank
            iv_factor = min(1.0, (ivr - min_ivr) / (max_ivr - min_ivr))
            base_confidence = 0.25 + (iv_factor * 0.5)  # 0.25 to 0.75 range
        else:
            base_confidence = 0.15

        # Adjust confidence based on trend - Put Credit Spreads prefer bullish trends
        trend_multiplier = {
            "up": 1.3,          # Best for Put Credit Spreads
            "sideways": 1.1,    # Good for Put Credit Spreads
            "mixed": 0.9,       # Acceptable
            "down": bearish_penalty  # Poor for Put Credit Spreads
        }.get(trend, 0.8)

        final_confidence = min(1.0, base_confidence * trend_multiplier)

        # Determine action based on confidence and market conditions
        if (final_confidence >= hold_threshold and 
            ivr >= min_ivr and 
            trend in {"up", "sideways"}):
            action = "enter"
            notes = f"IVR={ivr:.2f} (>{min_ivr:.2f}), trend={trend} - favorable for put spreads"
        elif final_confidence >= 0.25 and trend != "down":
            action = "hold"
            notes = f"IVR={ivr:.2f}, trend={trend} - monitoring for entry opportunity"
        else:
            action = "hold"
            if trend == "down":
                notes = f"IVR={ivr:.2f}, trend={trend} - bearish trend unfavorable for put spreads"
            else:
                notes = f"IVR={ivr:.2f} (<{min_ivr:.2f}) - IV too low for credit spreads"

        # Special case: Very high IV with any trend gets a signal
        if ivr > 0.60 and final_confidence < hold_threshold:
            action = "enter"
            final_confidence = min(0.8, final_confidence * 1.5)
            notes = f"IVR={ivr:.2f} (very high) - opportunity despite trend={trend}"

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
        """Initialize Put Credit Spread strategy."""
        super().warmup(**kwargs)
        print(f"[{self.name}] Warmed up with config: {self.config}")

    def validate_market_data(self, md: Dict[str, Any]) -> bool:
        """
        Validate market data for Put Credit Spread strategy.
        
        Required fields: symbol, ivr, trend
        """
        required_fields = ["symbol", "ivr", "trend"]
        return all(field in md for field in required_fields)