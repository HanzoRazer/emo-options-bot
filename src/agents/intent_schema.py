"""
Intent Schema for Voice AI Trading Agent
Defines the structure for natural language trading requests.
"""

from typing import Dict, Any, List, Union
from enum import Enum

class StrategyType(str, Enum):
    INCOME = "income"
    DIRECTIONAL = "directional"
    VOLATILITY = "volatility"
    HEDGE = "hedge"

class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"

# JSON Schema for Intent validation
INTENT_SCHEMA = {
    "type": "object",
    "required": ["user_goal", "universe", "constraints", "time_horizon_days"],
    "properties": {
        "request_id": {
            "type": "string",
            "description": "Unique identifier for this request"
        },
        "user_goal": {
            "type": "string",
            "description": "Natural language description of trading objective",
            "examples": [
                "Generate low-risk income for the next month",
                "Protect my portfolio from a market crash",
                "Profit from high volatility in tech stocks"
            ]
        },
        "universe": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of symbols to consider",
            "minItems": 1,
            "examples": [["SPY", "QQQ"], ["AAPL", "MSFT"], ["SPY"]]
        },
        "constraints": {
            "type": "object",
            "required": ["max_portfolio_risk"],
            "properties": {
                "max_portfolio_risk": {
                    "type": "number",
                    "minimum": 0.001,
                    "maximum": 0.1,
                    "description": "Maximum portfolio risk as decimal (0.01 = 1%)"
                },
                "risk_defined_only": {
                    "type": "boolean",
                    "description": "Only allow defined-risk strategies",
                    "default": True
                },
                "min_probability_of_profit": {
                    "type": "number",
                    "minimum": 0.1,
                    "maximum": 0.95,
                    "description": "Minimum probability of profit threshold"
                },
                "max_trade_size": {
                    "type": "number",
                    "description": "Maximum size per trade (contracts or shares)"
                },
                "avoid_earnings": {
                    "type": "boolean",
                    "description": "Avoid positions through earnings",
                    "default": True
                }
            }
        },
        "strategy_preferences": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["income", "directional", "volatility", "hedge"],
                    "description": "Primary strategy type preference"
                },
                "candidates": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific strategies to consider",
                    "examples": [
                        ["iron_condor", "put_credit_spread"],
                        ["covered_call", "cash_secured_put"],
                        ["long_straddle", "iron_butterfly"]
                    ]
                },
                "risk_level": {
                    "type": "string",
                    "enum": ["low", "moderate", "high"],
                    "description": "Risk tolerance for this request"
                }
            }
        },
        "time_horizon_days": {
            "type": "integer",
            "minimum": 1,
            "maximum": 365,
            "description": "Time horizon for the strategy in days"
        },
        "market_conditions": {
            "type": "object",
            "properties": {
                "iv_regime": {
                    "type": "string",
                    "enum": ["low", "moderate", "high"],
                    "description": "Current implied volatility regime"
                },
                "trend": {
                    "type": "string",
                    "enum": ["bullish", "bearish", "neutral", "uncertain"],
                    "description": "Current market trend bias"
                }
            }
        },
        "notes": {
            "type": "string",
            "description": "Additional notes or preferences"
        }
    }
}

# Strategy mapping for different goals
GOAL_TO_STRATEGY_MAP = {
    "income": ["iron_condor", "put_credit_spread", "covered_call", "cash_secured_put"],
    "directional_bullish": ["put_credit_spread", "covered_call", "bull_call_spread"],
    "directional_bearish": ["bear_put_spread", "protective_put"],
    "volatility_expansion": ["long_straddle", "long_strangle"],
    "volatility_contraction": ["iron_condor", "iron_butterfly"],
    "protection": ["protective_put", "collar", "bear_put_spread"]
}

# Risk level mappings
RISK_LEVEL_CONSTRAINTS = {
    "low": {
        "max_portfolio_risk": 0.01,
        "risk_defined_only": True,
        "min_probability_of_profit": 0.6
    },
    "moderate": {
        "max_portfolio_risk": 0.03,
        "risk_defined_only": True,
        "min_probability_of_profit": 0.5
    },
    "high": {
        "max_portfolio_risk": 0.05,
        "risk_defined_only": False,
        "min_probability_of_profit": 0.4
    }
}

def validate_intent(intent: Dict[str, Any]) -> List[str]:
    """
    Validate intent against schema and business rules.
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    # Check required fields
    required_fields = INTENT_SCHEMA["required"]
    for field in required_fields:
        if field not in intent:
            errors.append(f"Missing required field: {field}")
    
    # Validate constraints
    if "constraints" in intent:
        constraints = intent["constraints"]
        if "max_portfolio_risk" in constraints:
            risk = constraints["max_portfolio_risk"]
            if not 0.001 <= risk <= 0.1:
                errors.append(f"max_portfolio_risk must be between 0.1% and 10%, got {risk*100:.1f}%")
    
    # Validate universe
    if "universe" in intent:
        universe = intent["universe"]
        if not isinstance(universe, list) or len(universe) == 0:
            errors.append("universe must be a non-empty list of symbols")
    
    # Validate time horizon
    if "time_horizon_days" in intent:
        days = intent["time_horizon_days"]
        if not isinstance(days, int) or not 1 <= days <= 365:
            errors.append("time_horizon_days must be between 1 and 365")
    
    return errors

def create_sample_intent() -> Dict[str, Any]:
    """Create a sample intent for testing."""
    return {
        "request_id": "sample_001",
        "user_goal": "Generate low-risk income for the next month",
        "universe": ["SPY", "QQQ"],
        "constraints": {
            "max_portfolio_risk": 0.01,
            "risk_defined_only": True,
            "min_probability_of_profit": 0.6,
            "avoid_earnings": True
        },
        "strategy_preferences": {
            "type": "income",
            "candidates": ["iron_condor", "put_credit_spread"],
            "risk_level": "low"
        },
        "time_horizon_days": 30,
        "market_conditions": {
            "iv_regime": "moderate",
            "trend": "neutral"
        },
        "notes": "Focus on SPY, avoid earnings weeks, prefer high probability setups"
    }