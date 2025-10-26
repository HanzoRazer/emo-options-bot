"""
Strategy Translator - Converts Trading Intents to Concrete Strategy Plans
Bridges the gap between natural language intents and executable trading strategies.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class StrategyLeg:
    """Represents one leg of an options strategy."""
    side: str       # "buy" or "sell"
    type: str       # "call" or "put"
    strike: float   # Strike price
    qty: int        # Quantity (contracts)
    expiry: str     # Expiration date

class StrategyTranslator:
    """Translates trading intents into concrete strategy plans."""
    
    def __init__(self):
        """Initialize the strategy translator."""
        self.strategy_builders = {
            "iron_condor": self._build_iron_condor,
            "put_credit_spread": self._build_put_credit_spread,
            "covered_call": self._build_covered_call,
            "long_straddle": self._build_long_straddle,
            "cash_secured_put": self._build_cash_secured_put,
            "protective_put": self._build_protective_put
        }
    
    def to_strategy_plan(self, intent: Dict[str, Any], market_ctx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert intent and market context into executable strategy plan.
        
        Args:
            intent: Structured trading intent from NLU
            market_ctx: Current market conditions and data
            
        Returns:
            Concrete strategy plan ready for validation and execution
        """
        # Select best strategy for intent
        strategy_name = self._select_strategy(intent, market_ctx)
        
        # Get primary symbol
        symbol = intent["universe"][0] if intent["universe"] else "SPY"
        
        # Calculate expiry date
        expiry_date = self._calculate_expiry(intent["time_horizon_days"], market_ctx)
        
        # Get current price and calculate strikes
        current_price = market_ctx.get("current_price", self._get_default_price(symbol))
        
        # Build strategy using appropriate builder
        if strategy_name in self.strategy_builders:
            legs = self.strategy_builders[strategy_name](
                symbol, current_price, expiry_date, intent, market_ctx
            )
        else:
            # Fallback to iron condor
            legs = self._build_iron_condor(symbol, current_price, expiry_date, intent, market_ctx)
            strategy_name = "iron_condor"
        
        # Calculate position sizing
        sizing = self._calculate_sizing(intent, market_ctx, legs)
        
        # Build complete plan
        plan = {
            "request_id": intent["request_id"],
            "symbol": symbol,
            "strategy": strategy_name,
            "expiry": expiry_date,
            "legs": [
                {
                    "side": leg.side,
                    "type": leg.type,
                    "strike": leg.strike,
                    "qty": leg.qty
                }
                for leg in legs
            ],
            "sizing": sizing,
            "entry_rules": self._get_entry_rules(strategy_name, intent),
            "risk_tags": self._get_risk_tags(strategy_name),
            "market_context": market_ctx,
            "intent_summary": intent["user_goal"],
            "status": "proposed",
            "created_at": datetime.now().isoformat(),
            "max_risk": sizing.get("max_risk_per_trade", 0.01),
            "target_profit": sizing.get("target_profit", 0.005),
            "probability_of_profit": self._estimate_pop(strategy_name, market_ctx)
        }
        
        return plan
    
    def _select_strategy(self, intent: Dict[str, Any], market_ctx: Dict[str, Any]) -> str:
        """Select best strategy based on intent and market conditions."""
        
        # Get strategy preferences from intent
        preferences = intent.get("strategy_preferences", {})
        candidates = preferences.get("candidates", [])
        strategy_type = preferences.get("type", "income")
        
        # If specific candidates are given, evaluate them
        if candidates:
            for candidate in candidates:
                if self._is_strategy_suitable(candidate, intent, market_ctx):
                    return candidate
        
        # Fallback based on strategy type and market conditions
        iv_regime = market_ctx.get("iv_regime", "moderate")
        trend = market_ctx.get("trend", "neutral")
        
        if strategy_type == "income":
            if iv_regime == "high":
                return "iron_condor"  # Sell premium in high IV
            else:
                return "put_credit_spread"  # Bullish bias in low IV
        
        elif strategy_type == "volatility":
            if iv_regime == "low":
                return "long_straddle"  # Buy cheap options
            else:
                return "iron_condor"  # Neutral in high IV
        
        elif strategy_type == "directional":
            if trend == "bullish":
                return "put_credit_spread"
            elif trend == "bearish":
                return "protective_put"
            else:
                return "iron_condor"
        
        elif strategy_type == "hedge":
            return "protective_put"
        
        # Ultimate fallback
        return "iron_condor"
    
    def _is_strategy_suitable(self, strategy: str, intent: Dict[str, Any], market_ctx: Dict[str, Any]) -> bool:
        """Check if a strategy is suitable for current conditions."""
        
        iv_regime = market_ctx.get("iv_regime", "moderate")
        trend = market_ctx.get("trend", "neutral")
        
        # Strategy-specific suitability rules
        suitability_rules = {
            "iron_condor": iv_regime in ["moderate", "high"] and trend == "neutral",
            "put_credit_spread": trend in ["bullish", "neutral"] and iv_regime != "low",
            "covered_call": trend in ["neutral", "bullish"] and iv_regime != "low",
            "long_straddle": iv_regime == "low" or market_ctx.get("upcoming_event", False),
            "cash_secured_put": trend == "bullish" and iv_regime != "low",
            "protective_put": True  # Always suitable as hedge
        }
        
        return suitability_rules.get(strategy, False)
    
    def _calculate_expiry(self, time_horizon_days: int, market_ctx: Dict[str, Any]) -> str:
        """Calculate appropriate expiry date."""
        
        # For options, we typically want 30-45 DTE for income strategies
        if time_horizon_days <= 30:
            target_dte = min(45, time_horizon_days + 15)  # Add buffer
        else:
            target_dte = min(60, time_horizon_days)
        
        # Calculate expiry date (simplified - in practice, use actual option chains)
        expiry = datetime.now() + timedelta(days=target_dte)
        
        # Round to next Friday (typical option expiry)
        days_ahead = 4 - expiry.weekday()  # Friday is weekday 4
        if days_ahead <= 0:
            days_ahead += 7
        expiry += timedelta(days=days_ahead)
        
        return expiry.strftime("%Y-%m-%d")
    
    def _get_default_price(self, symbol: str) -> float:
        """Get default/mock price for symbol."""
        default_prices = {
            "SPY": 450.0,
            "QQQ": 380.0,
            "AAPL": 175.0,
            "MSFT": 330.0,
            "TSLA": 220.0,
            "GOOGL": 140.0,
            "NVDA": 450.0,
            "IWM": 195.0
        }
        return default_prices.get(symbol, 100.0)
    
    def _build_iron_condor(self, symbol: str, price: float, expiry: str, intent: Dict[str, Any], market_ctx: Dict[str, Any]) -> List[StrategyLeg]:
        """Build iron condor strategy legs."""
        
        # Standard iron condor: sell call spread + sell put spread
        # Target ~15-20 delta on short strikes
        call_strike_short = price * 1.05   # ~15 delta call
        call_strike_long = price * 1.10    # Wing
        put_strike_short = price * 0.95    # ~15 delta put  
        put_strike_long = price * 0.90     # Wing
        
        return [
            StrategyLeg("sell", "call", call_strike_short, 1, expiry),
            StrategyLeg("buy", "call", call_strike_long, 1, expiry),
            StrategyLeg("sell", "put", put_strike_short, 1, expiry),
            StrategyLeg("buy", "put", put_strike_long, 1, expiry)
        ]
    
    def _build_put_credit_spread(self, symbol: str, price: float, expiry: str, intent: Dict[str, Any], market_ctx: Dict[str, Any]) -> List[StrategyLeg]:
        """Build put credit spread strategy legs."""
        
        # Sell higher strike put, buy lower strike put
        put_strike_short = price * 0.95   # ~20 delta
        put_strike_long = price * 0.90    # ~10 delta
        
        return [
            StrategyLeg("sell", "put", put_strike_short, 1, expiry),
            StrategyLeg("buy", "put", put_strike_long, 1, expiry)
        ]
    
    def _build_covered_call(self, symbol: str, price: float, expiry: str, intent: Dict[str, Any], market_ctx: Dict[str, Any]) -> List[StrategyLeg]:
        """Build covered call strategy legs."""
        
        # Assume we own 100 shares, sell call against them
        call_strike = price * 1.05  # ~20 delta call
        
        return [
            StrategyLeg("sell", "call", call_strike, 1, expiry)
        ]
    
    def _build_long_straddle(self, symbol: str, price: float, expiry: str, intent: Dict[str, Any], market_ctx: Dict[str, Any]) -> List[StrategyLeg]:
        """Build long straddle strategy legs."""
        
        # Buy ATM call and put
        atm_strike = round(price / 5) * 5  # Round to nearest $5
        
        return [
            StrategyLeg("buy", "call", atm_strike, 1, expiry),
            StrategyLeg("buy", "put", atm_strike, 1, expiry)
        ]
    
    def _build_cash_secured_put(self, symbol: str, price: float, expiry: str, intent: Dict[str, Any], market_ctx: Dict[str, Any]) -> List[StrategyLeg]:
        """Build cash secured put strategy legs."""
        
        # Sell OTM put with cash backing
        put_strike = price * 0.95  # ~20 delta
        
        return [
            StrategyLeg("sell", "put", put_strike, 1, expiry)
        ]
    
    def _build_protective_put(self, symbol: str, price: float, expiry: str, intent: Dict[str, Any], market_ctx: Dict[str, Any]) -> List[StrategyLeg]:
        """Build protective put strategy legs."""
        
        # Buy OTM put for protection
        put_strike = price * 0.95  # ~20 delta protection
        
        return [
            StrategyLeg("buy", "put", put_strike, 1, expiry)
        ]
    
    def _calculate_sizing(self, intent: Dict[str, Any], market_ctx: Dict[str, Any], legs: List[StrategyLeg]) -> Dict[str, Any]:
        """Calculate position sizing based on risk constraints."""
        
        max_portfolio_risk = intent.get("constraints", {}).get("max_portfolio_risk", 0.01)
        
        # Estimate max risk per contract (simplified)
        max_risk_per_contract = 500  # Default assumption
        
        # For spreads, max risk is difference between strikes
        if len(legs) >= 2:
            strikes = [leg.strike for leg in legs]
            if len(set(strikes)) > 1:
                max_risk_per_contract = abs(max(strikes) - min(strikes)) * 100  # $100 per point
        
        # Calculate max contracts based on portfolio risk
        portfolio_value = market_ctx.get("portfolio_value", 100000)  # Default $100k
        max_risk_dollars = portfolio_value * max_portfolio_risk
        max_contracts = max(1, int(max_risk_dollars / max_risk_per_contract))
        
        return {
            "max_risk_per_trade": max_portfolio_risk,
            "max_risk_dollars": max_risk_dollars,
            "contracts": min(max_contracts, 10),  # Cap at 10 contracts
            "risk_per_contract": max_risk_per_contract,
            "target_profit": max_portfolio_risk * 0.5  # Target 50% of risk
        }
    
    def _get_entry_rules(self, strategy: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Get entry rules for strategy."""
        
        rules = {
            "iron_condor": {"min_credit": 1.50, "spread_width": 5},
            "put_credit_spread": {"min_credit": 1.00, "spread_width": 5},
            "covered_call": {"min_premium": 0.50},
            "long_straddle": {"max_cost": 10.00},
            "cash_secured_put": {"min_premium": 0.75},
            "protective_put": {"max_cost": 5.00}
        }
        
        return rules.get(strategy, {})
    
    def _get_risk_tags(self, strategy: str) -> List[str]:
        """Get risk characteristic tags for strategy."""
        
        risk_tags = {
            "iron_condor": ["theta+", "vega-", "delta~0", "defined_risk"],
            "put_credit_spread": ["theta+", "vega-", "delta+", "defined_risk"],
            "covered_call": ["theta+", "vega-", "delta+", "undefined_risk"],
            "long_straddle": ["theta-", "vega+", "delta~0", "defined_risk"],
            "cash_secured_put": ["theta+", "vega-", "delta+", "undefined_risk"],
            "protective_put": ["theta-", "vega+", "delta-", "defined_risk"]
        }
        
        return risk_tags.get(strategy, ["unknown"])
    
    def _estimate_pop(self, strategy: str, market_ctx: Dict[str, Any]) -> float:
        """Estimate probability of profit for strategy."""
        
        # Simplified POP estimates based on strategy type
        base_pop = {
            "iron_condor": 0.65,
            "put_credit_spread": 0.70,
            "covered_call": 0.60,
            "long_straddle": 0.45,
            "cash_secured_put": 0.65,
            "protective_put": 0.80  # Hedge always "wins" by protecting
        }
        
        pop = base_pop.get(strategy, 0.50)
        
        # Adjust for market conditions
        iv_regime = market_ctx.get("iv_regime", "moderate")
        if iv_regime == "high" and strategy in ["iron_condor", "put_credit_spread"]:
            pop += 0.05  # Higher IV favors premium selling
        elif iv_regime == "low" and strategy in ["long_straddle"]:
            pop += 0.10  # Low IV favors volatility buying
        
        return min(0.95, max(0.20, pop))  # Clamp between 20% and 95%