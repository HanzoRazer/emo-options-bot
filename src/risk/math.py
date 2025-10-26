# src/risk/math.py
"""
Enhanced Risk Mathematics for Options Trading
Production-ready calculations with comprehensive error handling
"""
from __future__ import annotations
import logging
import math
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Union
from decimal import Decimal

logger = logging.getLogger(__name__)

@dataclass
class Leg:
    """Enhanced options leg with validation and calculations"""
    right: str      # "call" or "put"
    strike: float
    qty: int        # positive for long, negative for short
    price: float    # premium per contract
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    symbol: Optional[str] = None
    expiry: Optional[str] = None
    
    def __post_init__(self):
        """Validate leg data after initialization"""
        try:
            # Validate required fields
            if self.right not in ("call", "put"):
                raise ValueError(f"Invalid right: {self.right}. Must be 'call' or 'put'")
            
            if self.strike <= 0:
                raise ValueError(f"Invalid strike: {self.strike}. Must be positive")
            
            if self.qty == 0:
                raise ValueError("Quantity cannot be zero")
            
            if self.price < 0:
                raise ValueError(f"Invalid price: {self.price}. Cannot be negative")
            
            # Validate Greeks if provided
            if self.delta is not None:
                if self.right == "call" and not (-0.1 <= self.delta <= 1.1):
                    logger.warning(f"Unusual call delta: {self.delta}")
                elif self.right == "put" and not (-1.1 <= self.delta <= 0.1):
                    logger.warning(f"Unusual put delta: {self.delta}")
            
        except Exception as e:
            logger.error(f"Error validating Leg: {e}")
            raise
    
    def notional_value(self) -> float:
        """Calculate notional value of the position"""
        return abs(self.qty) * self.price * 100  # Standard option multiplier
    
    def is_long(self) -> bool:
        """Check if this is a long position"""
        return self.qty > 0
    
    def is_short(self) -> bool:
        """Check if this is a short position"""
        return self.qty < 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)

@dataclass
class AggregateGreeks:
    """Aggregate Greeks for a position or portfolio"""
    delta: float
    gamma: float
    theta: float
    vega: float
    
    def __post_init__(self):
        """Round Greeks to reasonable precision"""
        self.delta = round(self.delta, 4)
        self.gamma = round(self.gamma, 6)
        self.theta = round(self.theta, 4)
        self.vega = round(self.vega, 4)
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary"""
        return asdict(self)
    
    def risk_adjusted_delta(self, portfolio_value: float) -> float:
        """Calculate delta as percentage of portfolio"""
        return self.delta / (portfolio_value / 100) if portfolio_value > 0 else 0.0

@dataclass
class RiskProfile:
    """Enhanced risk profile with comprehensive metrics"""
    credit: float              # Net credit received (positive) or debit paid (negative)
    max_loss: float           # Maximum possible loss
    max_gain: float           # Maximum possible gain
    breakevens: List[float]   # Breakeven points
    margin_estimate: float    # Estimated margin requirement
    greeks: AggregateGreeks   # Aggregate Greeks
    profit_probability: Optional[float] = None  # Estimated probability of profit
    expected_return: Optional[float] = None     # Expected return
    
    def __post_init__(self):
        """Validate and enhance risk profile"""
        # Ensure positive values where appropriate
        self.max_loss = abs(self.max_loss)
        self.max_gain = abs(self.max_gain)
        self.margin_estimate = abs(self.margin_estimate)
        
        # Calculate return metrics if possible
        if self.max_loss > 0:
            self.max_return_pct = (self.max_gain / self.max_loss) * 100
            self.risk_reward_ratio = self.max_gain / self.max_loss
        else:
            self.max_return_pct = 0.0
            self.risk_reward_ratio = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with all metrics"""
        result = asdict(self)
        result.update({
            "max_return_pct": getattr(self, "max_return_pct", 0.0),
            "risk_reward_ratio": getattr(self, "risk_reward_ratio", 0.0)
        })
        return result
    
    def risk_grade(self) -> str:
        """Assign a risk grade based on profile"""
        if self.max_loss == 0:
            return "RISK_FREE"
        
        risk_reward = getattr(self, "risk_reward_ratio", 0)
        
        if risk_reward >= 3.0:
            return "LOW_RISK"
        elif risk_reward >= 1.5:
            return "MEDIUM_RISK"
        elif risk_reward >= 0.5:
            return "HIGH_RISK"
        else:
            return "VERY_HIGH_RISK"

def aggregate_greeks(legs: List[Leg]) -> AggregateGreeks:
    """
    Calculate aggregate Greeks for a position
    
    Args:
        legs: List of option legs
    
    Returns:
        AggregateGreeks object with portfolio Greeks
    """
    try:
        total_delta = 0.0
        total_gamma = 0.0
        total_theta = 0.0
        total_vega = 0.0
        
        for leg in legs:
            if not isinstance(leg, Leg):
                logger.warning(f"Invalid leg type: {type(leg)}")
                continue
            
            # Delta and theta are additive with quantity
            if leg.delta is not None:
                total_delta += leg.delta * leg.qty
            
            if leg.theta is not None:
                total_theta += leg.theta * leg.qty
            
            if leg.vega is not None:
                total_vega += leg.vega * leg.qty
            
            # Gamma adds up in magnitude (always positive contribution)
            if leg.gamma is not None:
                total_gamma += leg.gamma * abs(leg.qty)
        
        return AggregateGreeks(
            delta=total_delta,
            gamma=total_gamma,
            theta=total_theta,
            vega=total_vega
        )
        
    except Exception as e:
        logger.error(f"Error calculating aggregate Greeks: {e}")
        return AggregateGreeks(delta=0.0, gamma=0.0, theta=0.0, vega=0.0)

def credit_debit(legs: List[Leg]) -> float:
    """
    Calculate net credit/debit for a position
    
    Convention:
    - Long positions (qty > 0): pay premium (negative contribution)
    - Short positions (qty < 0): receive premium (positive contribution)
    
    Args:
        legs: List of option legs
    
    Returns:
        Net credit (positive) or debit (negative)
    """
    try:
        total = 0.0
        
        for leg in legs:
            if not isinstance(leg, Leg):
                logger.warning(f"Invalid leg type: {type(leg)}")
                continue
            
            # Convention: long pays premium, short receives premium
            if leg.qty > 0:  # Long position
                total -= abs(leg.qty) * leg.price * 100.0
            else:  # Short position
                total += abs(leg.qty) * leg.price * 100.0
        
        return round(total, 2)
        
    except Exception as e:
        logger.error(f"Error calculating credit/debit: {e}")
        return 0.0

def _spread_width(legs: List[Leg], side: str) -> float:
    """Calculate spread width for a given side (call or put)"""
    try:
        strikes = [leg.strike for leg in legs if leg.right == side]
        
        if len(strikes) < 2:
            return 0.0
        
        return max(strikes) - min(strikes)
        
    except Exception as e:
        logger.error(f"Error calculating spread width: {e}")
        return 0.0

def iron_condor_risk(legs: List[Leg]) -> RiskProfile:
    """
    Calculate risk profile for iron condor strategy
    
    Assumes structure:
    - Short put @ K2, long put @ K1 (K1 < K2)
    - Short call @ K3, long call @ K4 (K3 < K4)
    
    Args:
        legs: List of 4 option legs
    
    Returns:
        RiskProfile with comprehensive risk metrics
    """
    try:
        if len(legs) != 4:
            logger.warning(f"Iron condor should have 4 legs, got {len(legs)}")
        
        # Separate puts and calls
        put_legs = [leg for leg in legs if leg.right == "put"]
        call_legs = [leg for leg in legs if leg.right == "call"]
        
        if len(put_legs) != 2 or len(call_legs) != 2:
            logger.warning("Iron condor should have 2 puts and 2 calls")
        
        # Calculate net credit/debit
        net_credit = credit_debit(legs)
        
        # Calculate spread widths
        put_width = _spread_width(put_legs, "put") * 100.0
        call_width = _spread_width(call_legs, "call") * 100.0
        max_width = max(put_width, call_width)
        
        # Risk calculations
        if net_credit >= 0:  # Credit condor
            max_gain = net_credit
            max_loss = max(0.0, max_width - net_credit)
        else:  # Debit condor (rare)
            max_loss = abs(net_credit)
            max_gain = max(0.0, max_width - abs(net_credit))
        
        # Calculate breakevens
        breakevens = []
        try:
            # Find short strikes
            short_puts = sorted([leg.strike for leg in put_legs if leg.qty < 0])
            short_calls = sorted([leg.strike for leg in call_legs if leg.qty < 0])
            
            if short_puts:
                breakevens.append(short_puts[0] - net_credit / 100.0)
            if short_calls:
                breakevens.append(short_calls[0] + net_credit / 100.0)
                
        except Exception as e:
            logger.warning(f"Error calculating breakevens: {e}")
        
        # Aggregate Greeks
        greeks = aggregate_greeks(legs)
        
        # Margin estimate (typically equals max width)
        margin = max_width
        
        return RiskProfile(
            credit=net_credit,
            max_loss=max_loss,
            max_gain=max_gain,
            breakevens=sorted(breakevens),
            margin_estimate=margin,
            greeks=greeks
        )
        
    except Exception as e:
        logger.error(f"Error calculating iron condor risk: {e}")
        # Return safe default
        return RiskProfile(
            credit=0.0,
            max_loss=1000.0,
            max_gain=0.0,
            breakevens=[],
            margin_estimate=1000.0,
            greeks=AggregateGreeks(0.0, 0.0, 0.0, 0.0)
        )

def vertical_spread_risk(legs: List[Leg]) -> RiskProfile:
    """
    Calculate risk profile for vertical spread (bull/bear credit/debit)
    
    Args:
        legs: List of 2 option legs
    
    Returns:
        RiskProfile with comprehensive risk metrics
    """
    try:
        if len(legs) != 2:
            logger.warning(f"Vertical spread should have 2 legs, got {len(legs)}")
        
        # Determine if call or put spread
        sides = [leg.right for leg in legs]
        if "call" in sides:
            side = "call"
        elif "put" in sides:
            side = "put"
        else:
            raise ValueError("Invalid vertical spread: mixed call/put legs")
        
        # Calculate net credit/debit
        net_credit = credit_debit(legs)
        
        # Calculate spread width
        width_dollars = _spread_width(legs, side) * 100.0
        
        # Risk calculations
        if net_credit >= 0:  # Credit spread
            max_gain = net_credit
            max_loss = max(0.0, width_dollars - net_credit)
        else:  # Debit spread
            max_loss = abs(net_credit)
            max_gain = max(0.0, width_dollars - abs(net_credit))
        
        # Calculate breakeven
        breakevens = []
        try:
            short_strikes = sorted([leg.strike for leg in legs if leg.qty < 0])
            if short_strikes:
                if side == "call":
                    breakevens.append(short_strikes[0] + net_credit / 100.0)
                else:  # put
                    breakevens.append(short_strikes[0] - net_credit / 100.0)
        except Exception as e:
            logger.warning(f"Error calculating breakeven: {e}")
        
        # Aggregate Greeks
        greeks = aggregate_greeks(legs)
        
        # Margin estimate
        margin = width_dollars if net_credit >= 0 else max_loss
        
        return RiskProfile(
            credit=net_credit,
            max_loss=max_loss,
            max_gain=max_gain,
            breakevens=breakevens,
            margin_estimate=margin,
            greeks=greeks
        )
        
    except Exception as e:
        logger.error(f"Error calculating vertical spread risk: {e}")
        # Return safe default
        return RiskProfile(
            credit=0.0,
            max_loss=500.0,
            max_gain=0.0,
            breakevens=[],
            margin_estimate=500.0,
            greeks=AggregateGreeks(0.0, 0.0, 0.0, 0.0)
        )

def straddle_strangle_risk(legs: List[Leg]) -> RiskProfile:
    """Calculate risk profile for straddle or strangle"""
    try:
        net_debit = abs(credit_debit(legs))  # Usually a debit
        
        # For long straddle/strangle: unlimited upside, limited loss
        max_loss = net_debit
        max_gain = float('inf')  # Theoretically unlimited
        
        # Breakevens (rough approximation)
        strikes = sorted([leg.strike for leg in legs])
        if len(strikes) >= 2:
            lower_strike = min(strikes)
            upper_strike = max(strikes)
            breakevens = [
                lower_strike - net_debit / 100.0,
                upper_strike + net_debit / 100.0
            ]
        else:
            # Single strike (straddle)
            strike = strikes[0] if strikes else 0
            breakevens = [
                strike - net_debit / 100.0,
                strike + net_debit / 100.0
            ]
        
        greeks = aggregate_greeks(legs)
        
        return RiskProfile(
            credit=-net_debit,  # Negative for debit
            max_loss=max_loss,
            max_gain=10000.0,  # Cap at reasonable number for practical purposes
            breakevens=breakevens,
            margin_estimate=net_debit,
            greeks=greeks
        )
        
    except Exception as e:
        logger.error(f"Error calculating straddle/strangle risk: {e}")
        return RiskProfile(
            credit=0.0,
            max_loss=1000.0,
            max_gain=0.0,
            breakevens=[],
            margin_estimate=1000.0,
            greeks=AggregateGreeks(0.0, 0.0, 0.0, 0.0)
        )

def calculate_position_risk(
    legs: List[Leg], 
    strategy_type: Optional[str] = None
) -> RiskProfile:
    """
    Calculate risk profile for any options position
    
    Args:
        legs: List of option legs
        strategy_type: Optional strategy hint for optimized calculations
    
    Returns:
        RiskProfile with comprehensive metrics
    """
    try:
        if not legs:
            raise ValueError("No legs provided")
        
        # Route to appropriate calculator based on strategy type or leg count
        if strategy_type:
            if "condor" in strategy_type.lower():
                return iron_condor_risk(legs)
            elif "spread" in strategy_type.lower():
                return vertical_spread_risk(legs)
            elif strategy_type.lower() in ("straddle", "strangle"):
                return straddle_strangle_risk(legs)
        
        # Auto-detect based on leg count and structure
        if len(legs) == 4:
            # Check if it's an iron condor
            put_count = sum(1 for leg in legs if leg.right == "put")
            call_count = sum(1 for leg in legs if leg.right == "call")
            if put_count == 2 and call_count == 2:
                return iron_condor_risk(legs)
        
        elif len(legs) == 2:
            # Check if same underlying type (vertical spread)
            rights = [leg.right for leg in legs]
            if len(set(rights)) == 1:  # All same type
                return vertical_spread_risk(legs)
            else:  # Mixed call/put (straddle/strangle)
                return straddle_strangle_risk(legs)
        
        # Fallback: generic calculation
        net_credit = credit_debit(legs)
        greeks = aggregate_greeks(legs)
        
        # Rough estimates for unknown strategies
        notional = sum(leg.notional_value() for leg in legs)
        max_loss = abs(net_credit) if net_credit < 0 else notional * 0.5
        max_gain = net_credit if net_credit > 0 else notional * 0.3
        
        return RiskProfile(
            credit=net_credit,
            max_loss=max_loss,
            max_gain=max_gain,
            breakevens=[],
            margin_estimate=max_loss,
            greeks=greeks
        )
        
    except Exception as e:
        logger.error(f"Error calculating position risk: {e}")
        return RiskProfile(
            credit=0.0,
            max_loss=1000.0,
            max_gain=0.0,
            breakevens=[],
            margin_estimate=1000.0,
            greeks=AggregateGreeks(0.0, 0.0, 0.0, 0.0)
        )

# Convenience functions
def quick_risk_check(legs: List[Leg]) -> Dict[str, Any]:
    """Quick risk summary for a position"""
    try:
        profile = calculate_position_risk(legs)
        return {
            "net_credit": profile.credit,
            "max_risk": profile.max_loss,
            "max_reward": profile.max_gain,
            "risk_reward_ratio": getattr(profile, "risk_reward_ratio", 0),
            "delta": profile.greeks.delta,
            "risk_grade": profile.risk_grade()
        }
    except Exception as e:
        logger.error(f"Error in quick risk check: {e}")
        return {"error": str(e)}

# Export main components
__all__ = [
    "Leg",
    "AggregateGreeks", 
    "RiskProfile",
    "aggregate_greeks",
    "credit_debit",
    "iron_condor_risk",
    "vertical_spread_risk", 
    "straddle_strangle_risk",
    "calculate_position_risk",
    "quick_risk_check"
]