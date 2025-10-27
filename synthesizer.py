"""
Phase 3 Synthesizer - Trade strategy synthesis and construction
Converts market analysis into concrete options strategies with specific strikes and legs
"""

from __future__ import annotations
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from decimal import Decimal
import json

# Import schemas if available
try:
    from schemas import (
        OptionsOrder, OptionLeg, StrategyType, OrderSide, OptionType, 
        RiskConstraints, TradePlan, StrategyRecommendation
    )
except ImportError:
    # Fallback for development
    OptionsOrder = Dict[str, Any]
    OptionLeg = Dict[str, Any]
    StrategyType = str
    OrderSide = str
    OptionType = str


class StrategyParameters:
    """Default parameters for different strategy types"""
    
    IRON_CONDOR = {
        "wing_width": 5.0,          # Strike spacing for wings
        "body_width": 20.0,         # Distance between short strikes
        "default_dte": 30,          # Days to expiration
        "target_delta": 0.15        # Target delta for short strikes
    }
    
    PUT_CREDIT_SPREAD = {
        "wing_width": 5.0,
        "default_dte": 30,
        "target_delta": 0.20
    }
    
    CALL_CREDIT_SPREAD = {
        "wing_width": 5.0,
        "default_dte": 30,
        "target_delta": 0.20
    }
    
    LONG_CALL = {
        "default_dte": 45,
        "target_delta": 0.50
    }
    
    LONG_PUT = {
        "default_dte": 45,
        "target_delta": 0.50
    }


class MockMarketData:
    """Mock market data provider for development"""
    
    @staticmethod
    def get_current_price(symbol: str) -> Decimal:
        """Get mock current price for symbol"""
        mock_prices = {
            "SPY": Decimal("450.00"),
            "QQQ": Decimal("380.00"),
            "AAPL": Decimal("175.00"),
            "TSLA": Decimal("250.00"),
            "MSFT": Decimal("350.00")
        }
        return mock_prices.get(symbol, Decimal("100.00"))
    
    @staticmethod
    def get_option_chain(symbol: str, expiry: date) -> Dict[str, Any]:
        """Get mock option chain data"""
        current_price = MockMarketData.get_current_price(symbol)
        
        # Generate mock option chain around current price
        chain = {
            "symbol": symbol,
            "expiry": expiry,
            "current_price": current_price,
            "calls": {},
            "puts": {}
        }
        
        # Generate strikes around current price
        for i in range(-10, 11):
            strike = current_price + (i * 5)
            
            # Mock option prices (simplified)
            call_price = max(current_price - strike + 2, 0.50)
            put_price = max(strike - current_price + 2, 0.50)
            
            chain["calls"][str(strike)] = {
                "strike": strike,
                "price": call_price,
                "bid": call_price - 0.05,
                "ask": call_price + 0.05,
                "delta": 0.5 if i == 0 else max(0.05, 0.5 - abs(i) * 0.05)
            }
            
            chain["puts"][str(strike)] = {
                "strike": strike,
                "price": put_price,
                "bid": put_price - 0.05,
                "ask": put_price + 0.05,
                "delta": -0.5 if i == 0 else min(-0.05, -0.5 + abs(i) * 0.05)
            }
        
        return chain


class TradeSynthesizer:
    """Main trade synthesizer for converting plans to orders"""
    
    def __init__(self, market_data_provider=None):
        """Initialize synthesizer"""
        self.market_data = market_data_provider or MockMarketData()
        self.strategy_params = {
            "iron_condor": StrategyParameters.IRON_CONDOR,
            "put_credit_spread": StrategyParameters.PUT_CREDIT_SPREAD,
            "call_credit_spread": StrategyParameters.CALL_CREDIT_SPREAD,
            "long_call": StrategyParameters.LONG_CALL,
            "long_put": StrategyParameters.LONG_PUT
        }
    
    def suggest(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Convert trade plan into concrete options order"""
        try:
            # Extract plan details
            symbol = plan.get("symbol", "SPY")
            strategy_type = plan.get("strategy_type", "iron_condor")
            max_risk = plan.get("max_risk", 500)
            constraints = plan.get("constraints", {})
            
            # Get current market data
            current_price = self.market_data.get_current_price(symbol)
            
            # Calculate expiration date
            dte = constraints.get("days_to_expiration", 30)
            expiry_date = self._calculate_expiry(dte)
            
            # Generate strategy-specific legs
            legs = self._generate_legs(
                symbol=symbol,
                strategy_type=strategy_type,
                current_price=current_price,
                expiry_date=expiry_date,
                constraints=constraints
            )
            
            # Calculate risk metrics
            risk_metrics = self._calculate_risk_metrics(legs, strategy_type)
            
            # Build order structure
            order = {
                "symbol": symbol,
                "strategy_type": strategy_type,
                "legs": legs,
                "risk_constraints": {
                    "max_loss": max_risk
                },
                "metadata": {
                    "synthesizer_version": "phase3_v1.0",
                    "current_price": float(current_price),
                    "expiry_date": expiry_date.isoformat(),
                    "risk_metrics": risk_metrics,
                    "created_at": datetime.now().isoformat()
                }
            }
            
            return order
            
        except Exception as e:
            return {
                "error": f"Synthesis failed: {str(e)}",
                "plan": plan
            }
    
    def _calculate_expiry(self, dte: int) -> date:
        """Calculate option expiration date"""
        base_date = datetime.now().date()
        target_date = base_date + timedelta(days=dte)
        
        # For simplicity, use the target date
        # In real implementation, would find next available expiry
        return target_date
    
    def _generate_legs(self, symbol: str, strategy_type: str, current_price: Decimal, 
                      expiry_date: date, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate option legs for the specified strategy"""
        
        if strategy_type == "iron_condor":
            return self._build_iron_condor(symbol, current_price, expiry_date, constraints)
        elif strategy_type == "put_credit_spread":
            return self._build_put_credit_spread(symbol, current_price, expiry_date, constraints)
        elif strategy_type == "call_credit_spread":
            return self._build_call_credit_spread(symbol, current_price, expiry_date, constraints)
        elif strategy_type == "long_call":
            return self._build_long_call(symbol, current_price, expiry_date, constraints)
        elif strategy_type == "long_put":
            return self._build_long_put(symbol, current_price, expiry_date, constraints)
        else:
            raise ValueError(f"Unsupported strategy type: {strategy_type}")
    
    def _build_iron_condor(self, symbol: str, current_price: Decimal, expiry_date: date, 
                          constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build iron condor legs"""
        params = self.strategy_params["iron_condor"]
        
        # Calculate strikes around current price
        body_width = Decimal(str(constraints.get("body_width", params["body_width"])))
        wing_width = Decimal(str(constraints.get("wing_width", params["wing_width"])))
        
        # Short strikes (center of condor)
        short_put_strike = current_price - (body_width / 2)
        short_call_strike = current_price + (body_width / 2)
        
        # Long strikes (wings)
        long_put_strike = short_put_strike - wing_width
        long_call_strike = short_call_strike + wing_width
        
        legs = [
            {
                "action": "sell",
                "instrument": "put",
                "strike": float(short_put_strike),
                "expiry": expiry_date,
                "quantity": 1
            },
            {
                "action": "buy",
                "instrument": "put",
                "strike": float(long_put_strike),
                "expiry": expiry_date,
                "quantity": 1
            },
            {
                "action": "sell",
                "instrument": "call",
                "strike": float(short_call_strike),
                "expiry": expiry_date,
                "quantity": 1
            },
            {
                "action": "buy",
                "instrument": "call",
                "strike": float(long_call_strike),
                "expiry": expiry_date,
                "quantity": 1
            }
        ]
        
        return legs
    
    def _build_put_credit_spread(self, symbol: str, current_price: Decimal, expiry_date: date,
                                constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build put credit spread legs"""
        params = self.strategy_params["put_credit_spread"]
        wing_width = Decimal(str(constraints.get("wing_width", params["wing_width"])))
        
        # Short put below current price
        short_strike = current_price - Decimal("20")  # Default offset
        long_strike = short_strike - wing_width
        
        legs = [
            {
                "action": "sell",
                "instrument": "put",
                "strike": float(short_strike),
                "expiry": expiry_date,
                "quantity": 1
            },
            {
                "action": "buy",
                "instrument": "put",
                "strike": float(long_strike),
                "expiry": expiry_date,
                "quantity": 1
            }
        ]
        
        return legs
    
    def _build_call_credit_spread(self, symbol: str, current_price: Decimal, expiry_date: date,
                                 constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build call credit spread legs"""
        params = self.strategy_params["call_credit_spread"]
        wing_width = Decimal(str(constraints.get("wing_width", params["wing_width"])))
        
        # Short call above current price
        short_strike = current_price + Decimal("20")  # Default offset
        long_strike = short_strike + wing_width
        
        legs = [
            {
                "action": "sell",
                "instrument": "call",
                "strike": float(short_strike),
                "expiry": expiry_date,
                "quantity": 1
            },
            {
                "action": "buy",
                "instrument": "call",
                "strike": float(long_strike),
                "expiry": expiry_date,
                "quantity": 1
            }
        ]
        
        return legs
    
    def _build_long_call(self, symbol: str, current_price: Decimal, expiry_date: date,
                        constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build long call leg"""
        # At-the-money or slightly out-of-the-money call
        strike = current_price + Decimal("5")
        
        legs = [
            {
                "action": "buy",
                "instrument": "call",
                "strike": float(strike),
                "expiry": expiry_date,
                "quantity": 1
            }
        ]
        
        return legs
    
    def _build_long_put(self, symbol: str, current_price: Decimal, expiry_date: date,
                       constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build long put leg"""
        # At-the-money or slightly out-of-the-money put
        strike = current_price - Decimal("5")
        
        legs = [
            {
                "action": "buy",
                "instrument": "put",
                "strike": float(strike),
                "expiry": expiry_date,
                "quantity": 1
            }
        ]
        
        return legs
    
    def _calculate_risk_metrics(self, legs: List[Dict[str, Any]], strategy_type: str) -> Dict[str, Any]:
        """Calculate risk metrics for the strategy"""
        max_loss = 0
        max_profit = 0
        
        if strategy_type == "iron_condor":
            # For iron condor, max loss is wing width minus credit
            wing_width = 5.0  # Default, would calculate from actual legs
            estimated_credit = 2.0  # Mock credit received
            max_loss = wing_width - estimated_credit
            max_profit = estimated_credit
        
        elif strategy_type in ["put_credit_spread", "call_credit_spread"]:
            wing_width = 5.0
            estimated_credit = 1.5
            max_loss = wing_width - estimated_credit
            max_profit = estimated_credit
        
        elif strategy_type in ["long_call", "long_put"]:
            estimated_premium = 3.0
            max_loss = estimated_premium
            max_profit = float('inf')  # Theoretically unlimited
        
        return {
            "max_loss": max_loss,
            "max_profit": max_profit if max_profit != float('inf') else "unlimited",
            "risk_reward_ratio": max_profit / max_loss if max_loss > 0 else 0,
            "strategy_type": strategy_type
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check synthesizer health"""
        try:
            # Test synthesis with sample plan
            test_plan = {
                "symbol": "SPY",
                "strategy_type": "iron_condor",
                "max_risk": 500,
                "constraints": {}
            }
            
            result = self.suggest(test_plan)
            
            return {
                "status": "healthy",
                "test_successful": "legs" in result,
                "market_data_provider": type(self.market_data).__name__
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Example usage and testing
if __name__ == "__main__":
    print("⚙️ Testing Phase 3 Synthesizer")
    
    # Initialize synthesizer
    synthesizer = TradeSynthesizer()
    print("✅ Synthesizer initialized")
    
    # Health check
    health = synthesizer.health_check()
    print(f"Health: {health['status']}")
    
    # Test different strategies
    test_plans = [
        {
            "symbol": "SPY",
            "strategy_type": "iron_condor",
            "max_risk": 500,
            "constraints": {"body_width": 20, "wing_width": 5}
        },
        {
            "symbol": "QQQ",
            "strategy_type": "put_credit_spread",
            "max_risk": 300,
            "constraints": {"wing_width": 5}
        },
        {
            "symbol": "AAPL",
            "strategy_type": "long_call",
            "max_risk": 200,
            "constraints": {}
        }
    ]
    
    for i, plan in enumerate(test_plans, 1):
        print(f"\n🎯 Test {i}: {plan['symbol']} {plan['strategy_type']}")
        result = synthesizer.suggest(plan)
        
        if "error" not in result:
            print(f"   ✅ Success: {len(result['legs'])} legs")
            print(f"   Risk: ${result['metadata']['risk_metrics']['max_loss']}")
            print(f"   Profit: ${result['metadata']['risk_metrics']['max_profit']}")
        else:
            print(f"   ❌ Failed: {result['error']}")
    
    print("\n🎯 Synthesizer testing complete")