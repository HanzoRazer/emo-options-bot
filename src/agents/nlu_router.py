"""
NLU Router - Natural Language Understanding for Trading Commands
Converts voice/text commands into structured trading intents.
"""

import uuid
from typing import Dict, Any, List
from .intent_schema import validate_intent, create_sample_intent, GOAL_TO_STRATEGY_MAP, RISK_LEVEL_CONSTRAINTS
from ..api.llm_client import LLMClient

class NLURouter:
    """Routes natural language trading commands to structured intents."""
    
    def __init__(self, llm_client: LLMClient = None):
        """
        Initialize NLU Router.
        
        Args:
            llm_client: Optional LLM client instance
        """
        self.llm_client = llm_client or LLMClient()
        self.intent_cache = {}  # Cache for repeated requests
    
    def parse_free_text(self, command: str) -> Dict[str, Any]:
        """
        Parse natural language command into structured intent.
        
        Args:
            command: Natural language trading command
            
        Returns:
            Structured intent dictionary
            
        Examples:
            "Make some income from SPY this month" 
            → {user_goal: "income", universe: ["SPY"], time_horizon_days: 30, ...}
            
            "I think there will be big volatility in tech stocks"
            → {user_goal: "volatility", universe: ["QQQ"], strategy_preferences: {...}, ...}
        """
        # Check cache first
        cache_key = command.lower().strip()
        if cache_key in self.intent_cache:
            cached = self.intent_cache[cache_key].copy()
            cached["request_id"] = str(uuid.uuid4())  # New ID for each request
            return cached
        
        try:
            # Use LLM to parse intent
            intent = self.llm_client.parse_trading_intent(command)
            
            # Generate unique request ID if not present
            if "request_id" not in intent:
                intent["request_id"] = str(uuid.uuid4())
            
            # Apply intelligent defaults
            intent = self._apply_intelligent_defaults(intent, command)
            
            # Validate the parsed intent
            errors = validate_intent(intent)
            if errors:
                print(f"[NLU] Intent validation errors: {errors}")
                # Try to fix common errors
                intent = self._fix_common_errors(intent, errors)
                
                # Re-validate
                errors = validate_intent(intent)
                if errors:
                    raise ValueError(f"Could not parse intent: {'; '.join(errors)}")
            
            # Cache successful parse
            self.intent_cache[cache_key] = intent.copy()
            
            print(f"[NLU] Parsed intent: {intent['user_goal']} for {intent['universe']}")
            return intent
            
        except Exception as e:
            print(f"[NLU] Error parsing command '{command}': {e}")
            # Return a safe fallback intent
            return self._create_fallback_intent(command)
    
    def _apply_intelligent_defaults(self, intent: Dict[str, Any], original_command: str) -> Dict[str, Any]:
        """Apply intelligent defaults based on command context."""
        
        # Ensure required fields exist
        if "constraints" not in intent:
            intent["constraints"] = {}
        
        if "strategy_preferences" not in intent:
            intent["strategy_preferences"] = {}
        
        # Default universe based on common patterns
        if "universe" not in intent or not intent["universe"]:
            if any(word in original_command.lower() for word in ["spy", "s&p", "market"]):
                intent["universe"] = ["SPY"]
            elif any(word in original_command.lower() for word in ["tech", "nasdaq", "qqq"]):
                intent["universe"] = ["QQQ"]
            elif any(word in original_command.lower() for word in ["apple", "aapl"]):
                intent["universe"] = ["AAPL"]
            else:
                intent["universe"] = ["SPY"]  # Safe default
        
        # Default time horizon based on common phrases
        if "time_horizon_days" not in intent:
            if any(word in original_command.lower() for word in ["week", "weekly"]):
                intent["time_horizon_days"] = 7
            elif any(word in original_command.lower() for word in ["month", "monthly"]):
                intent["time_horizon_days"] = 30
            elif any(word in original_command.lower() for word in ["quarter", "quarterly"]):
                intent["time_horizon_days"] = 90
            else:
                intent["time_horizon_days"] = 30  # Default to monthly
        
        # Default risk level based on language
        risk_level = "moderate"  # Default
        if any(word in original_command.lower() for word in ["safe", "conservative", "low risk", "careful"]):
            risk_level = "low"
        elif any(word in original_command.lower() for word in ["aggressive", "high risk", "risky"]):
            risk_level = "high"
        
        # Apply risk level constraints
        if risk_level in RISK_LEVEL_CONSTRAINTS:
            intent["constraints"].update(RISK_LEVEL_CONSTRAINTS[risk_level])
            intent["strategy_preferences"]["risk_level"] = risk_level
        
        # Infer strategy type from goals
        user_goal = intent.get("user_goal", "").lower()
        if "income" in user_goal or "premium" in user_goal:
            intent["strategy_preferences"]["type"] = "income"
            intent["strategy_preferences"]["candidates"] = GOAL_TO_STRATEGY_MAP["income"]
        elif "volatility" in user_goal or "volatile" in user_goal or "big move" in user_goal:
            intent["strategy_preferences"]["type"] = "volatility"
            intent["strategy_preferences"]["candidates"] = GOAL_TO_STRATEGY_MAP["volatility_expansion"]
        elif "protect" in user_goal or "hedge" in user_goal or "crash" in user_goal:
            intent["strategy_preferences"]["type"] = "hedge"
            intent["strategy_preferences"]["candidates"] = GOAL_TO_STRATEGY_MAP["protection"]
        elif "bullish" in user_goal or "up" in user_goal or "rise" in user_goal:
            intent["strategy_preferences"]["type"] = "directional"
            intent["strategy_preferences"]["candidates"] = GOAL_TO_STRATEGY_MAP["directional_bullish"]
        elif "bearish" in user_goal or "down" in user_goal or "fall" in user_goal:
            intent["strategy_preferences"]["type"] = "directional"
            intent["strategy_preferences"]["candidates"] = GOAL_TO_STRATEGY_MAP["directional_bearish"]
        
        return intent
    
    def _fix_common_errors(self, intent: Dict[str, Any], errors: List[str]) -> Dict[str, Any]:
        """Attempt to fix common validation errors."""
        
        for error in errors:
            if "max_portfolio_risk" in error:
                # Set safe default
                intent["constraints"]["max_portfolio_risk"] = 0.01
            
            elif "universe" in error:
                # Set safe default
                intent["universe"] = ["SPY"]
            
            elif "time_horizon_days" in error:
                # Set safe default
                intent["time_horizon_days"] = 30
            
            elif "user_goal" in error:
                # Set generic goal
                intent["user_goal"] = "Generate conservative income"
        
        return intent
    
    def _create_fallback_intent(self, command: str) -> Dict[str, Any]:
        """Create a safe fallback intent when parsing fails."""
        return {
            "request_id": str(uuid.uuid4()),
            "user_goal": f"Manual review needed for: {command[:100]}",
            "universe": ["SPY"],
            "constraints": {
                "max_portfolio_risk": 0.005,  # Very conservative
                "risk_defined_only": True,
                "min_probability_of_profit": 0.7
            },
            "strategy_preferences": {
                "type": "income",
                "candidates": ["iron_condor"],
                "risk_level": "low"
            },
            "time_horizon_days": 30,
            "notes": f"Fallback intent created for unparseable command: {command}",
            "_needs_manual_review": True
        }
    
    def validate_and_enhance_intent(self, intent: Dict[str, Any]) -> tuple[Dict[str, Any], List[str]]:
        """
        Validate and enhance an intent with additional context.
        
        Returns:
            Tuple of (enhanced_intent, validation_errors)
        """
        # Validate basic structure
        errors = validate_intent(intent)
        
        # Add enhancements
        enhanced = intent.copy()
        
        # Add timestamp
        from datetime import datetime
        enhanced["created_at"] = datetime.now().isoformat()
        
        # Add risk assessment
        risk_score = self._calculate_risk_score(enhanced)
        enhanced["_risk_score"] = risk_score
        
        return enhanced, errors
    
    def _calculate_risk_score(self, intent: Dict[str, Any]) -> float:
        """Calculate a risk score for the intent (0-1, higher = riskier)."""
        score = 0.0
        
        # Portfolio risk component
        max_risk = intent.get("constraints", {}).get("max_portfolio_risk", 0.01)
        score += min(1.0, max_risk * 20)  # 5% = 1.0 score
        
        # Strategy type risk
        strategy_type = intent.get("strategy_preferences", {}).get("type", "income")
        type_risk = {
            "income": 0.2,
            "hedge": 0.3,
            "directional": 0.6,
            "volatility": 0.8
        }.get(strategy_type, 0.5)
        score += type_risk * 0.5
        
        # Time horizon risk (shorter = riskier for options)
        days = intent.get("time_horizon_days", 30)
        if days < 7:
            score += 0.3
        elif days < 21:
            score += 0.1
        
        return min(1.0, score)

# Convenience function for backward compatibility
def parse_free_text(command: str) -> Dict[str, Any]:
    """
    Simple function to parse trading command.
    
    Args:
        command: Natural language trading command
        
    Returns:
        Structured intent dictionary
    """
    router = NLURouter()
    return router.parse_free_text(command)