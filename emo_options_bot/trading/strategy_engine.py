"""Trading strategy engine."""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime

from ..core.models import (
    TradingStrategy, Order, OrderStatus, StrategyType,
    OptionType, OrderAction
)


class StrategyEngine:
    """
    Analyze and validate trading strategies.
    
    Calculates risk/reward profiles and validates strategy parameters.
    """
    
    def __init__(self):
        """Initialize strategy engine."""
        self.strategies: List[TradingStrategy] = []
    
    def analyze_strategy(self, strategy: TradingStrategy) -> dict:
        """
        Analyze a trading strategy and calculate risk metrics.
        
        Args:
            strategy: Trading strategy to analyze
            
        Returns:
            Dictionary with analysis results
        """
        analysis = {
            "strategy_id": strategy.id,
            "strategy_type": strategy.strategy_type,
            "max_risk": strategy.max_risk,
            "max_profit": strategy.max_profit,
            "risk_reward_ratio": None,
            "break_even_points": [],
            "probability_of_profit": None,
            "legs": len(strategy.orders),
            "net_premium": self._calculate_net_premium(strategy),
            "Greeks": self._estimate_greeks(strategy),
        }
        
        if strategy.max_profit and strategy.max_risk:
            analysis["risk_reward_ratio"] = float(strategy.max_profit / strategy.max_risk)
        
        return analysis
    
    def validate_strategy(self, strategy: TradingStrategy) -> tuple[bool, List[str]]:
        """
        Validate strategy parameters.
        
        Args:
            strategy: Strategy to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check for orders
        if not strategy.orders:
            errors.append("Strategy must have at least one order")
        
        # Validate each order
        for order in strategy.orders:
            if order.quantity <= 0:
                errors.append(f"Order {order.id} has invalid quantity: {order.quantity}")
            
            if order.contract.strike <= 0:
                errors.append(f"Order {order.id} has invalid strike: {order.contract.strike}")
            
            # Check expiration is in the future
            if order.contract.expiration < datetime.now().date():
                errors.append(f"Order {order.id} has expired contract")
        
        # Check for spread validation
        if strategy.strategy_type in [StrategyType.VERTICAL_SPREAD, StrategyType.IRON_CONDOR]:
            if len(strategy.orders) < 2:
                errors.append(f"{strategy.strategy_type} requires at least 2 legs")
        
        return len(errors) == 0, errors
    
    def _calculate_net_premium(self, strategy: TradingStrategy) -> Decimal:
        """Calculate net premium for the strategy."""
        net_premium = Decimal(0)
        
        for order in strategy.orders:
            if order.limit_price:
                if order.action in [OrderAction.BUY, OrderAction.BUY_TO_OPEN, OrderAction.BUY_TO_CLOSE]:
                    net_premium -= order.limit_price * Decimal(order.quantity) * Decimal(100)
                else:
                    net_premium += order.limit_price * Decimal(order.quantity) * Decimal(100)
        
        return net_premium
    
    def _estimate_greeks(self, strategy: TradingStrategy) -> dict:
        """
        Estimate Greeks for the strategy.
        
        Note: This is a simplified estimation. Real Greeks require market data.
        """
        return {
            "delta": 0.0,
            "gamma": 0.0,
            "theta": 0.0,
            "vega": 0.0,
            "rho": 0.0,
            "note": "Greeks estimation requires real-time market data"
        }
    
    def create_vertical_spread(
        self,
        underlying: str,
        option_type: OptionType,
        long_strike: Decimal,
        short_strike: Decimal,
        expiration,
        quantity: int = 1
    ) -> TradingStrategy:
        """
        Create a vertical spread strategy.
        
        Args:
            underlying: Underlying symbol
            option_type: CALL or PUT
            long_strike: Strike price for long option
            short_strike: Strike price for short option
            expiration: Expiration date
            quantity: Number of spreads
            
        Returns:
            TradingStrategy for the vertical spread
        """
        from ..core.models import OptionContract
        
        # Long leg
        long_contract = OptionContract(
            symbol=f"{underlying}_{long_strike}_{option_type.value}_{expiration}",
            underlying=underlying,
            strike=long_strike,
            expiration=expiration,
            option_type=option_type,
            quantity=quantity
        )
        
        long_order = Order(
            contract=long_contract,
            action=OrderAction.BUY_TO_OPEN,
            quantity=quantity
        )
        
        # Short leg
        short_contract = OptionContract(
            symbol=f"{underlying}_{short_strike}_{option_type.value}_{expiration}",
            underlying=underlying,
            strike=short_strike,
            expiration=expiration,
            option_type=option_type,
            quantity=quantity
        )
        
        short_order = Order(
            contract=short_contract,
            action=OrderAction.SELL_TO_OPEN,
            quantity=quantity
        )
        
        # Calculate max risk/profit
        spread_width = abs(long_strike - short_strike)
        max_risk = spread_width * Decimal(quantity) * Decimal(100)
        
        strategy = TradingStrategy(
            name=f"{underlying} {option_type.value} Vertical Spread {long_strike}/{short_strike}",
            strategy_type=StrategyType.VERTICAL_SPREAD,
            orders=[long_order, short_order],
            max_risk=max_risk,
            max_profit=max_risk  # Simplified, actual depends on premium
        )
        
        return strategy
    
    def save_strategy(self, strategy: TradingStrategy):
        """Save strategy to internal list."""
        self.strategies.append(strategy)
    
    def get_strategies(self) -> List[TradingStrategy]:
        """Get all saved strategies."""
        return self.strategies
