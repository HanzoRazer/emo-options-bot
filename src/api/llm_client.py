"""
LLM Client for Voice AI Trading Agent
Handles LLM API calls with safety wrappers and prompt engineering.
"""

import json
import openai
from typing import Dict, Any, Optional
from pathlib import Path
import os

class LLMClient:
    """Safe wrapper for LLM API calls with trading-specific prompts."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize LLM client.
        
        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            model: Model to use for completions
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
        if self.api_key:
            openai.api_key = self.api_key
        
        # Load trading knowledge base
        self.trading_context = self._load_trading_context()
    
    def _load_trading_context(self) -> str:
        """Load trading context and strategy knowledge."""
        return """
        TRADING STRATEGY KNOWLEDGE BASE:
        
        Options Strategies:
        - Iron Condor: Neutral strategy, sells OTM call and put spreads, profits from low volatility
        - Put Credit Spread: Bullish strategy, sells put spread, profits from upward/sideways movement
        - Covered Call: Income strategy, sells calls against stock, profits from premium + limited upside
        - Long Straddle: Volatility strategy, buys call and put, profits from large price movements
        - Cash Secured Put: Bullish income, sells puts with cash backing, may acquire stock
        
        Risk Management:
        - Defined Risk: Maximum loss is known at entry (spreads, protected strategies)
        - Undefined Risk: Potential for unlimited loss (naked options, some complex strategies)
        - Portfolio Risk: Percentage of total portfolio at risk in a single trade
        - Probability of Profit: Statistical likelihood of profitable outcome
        
        Market Conditions:
        - High IV: Good for selling premium (iron condors, credit spreads)
        - Low IV: Good for buying options (long straddles, directional plays)
        - Trending Markets: Favor directional strategies
        - Range-bound Markets: Favor income strategies
        """
    
    def parse_trading_intent(self, user_text: str) -> Dict[str, Any]:
        """
        Parse natural language trading request into structured intent.
        
        Args:
            user_text: Natural language trading request
            
        Returns:
            Structured intent dictionary
        """
        system_prompt = f"""
        You are a professional options trading assistant. Your job is to convert natural language 
        trading requests into structured JSON following this exact schema.
        
        {self.trading_context}
        
        CRITICAL INSTRUCTIONS:
        1. Output ONLY valid JSON, no other text
        2. Always include required fields: user_goal, universe, constraints, time_horizon_days
        3. Set reasonable defaults for missing information
        4. Default max_portfolio_risk to 0.01 (1%) for conservative approach
        5. Default risk_defined_only to true for safety
        6. Infer strategy type from user goals
        7. Generate a unique request_id
        
        EXAMPLES:
        User: "I want to make some income from SPY this month"
        → Strategy type: "income", candidates: ["iron_condor", "put_credit_spread"]
        
        User: "I think the market will be volatile, want to profit from big moves"
        → Strategy type: "volatility", candidates: ["long_straddle", "long_strangle"]
        
        User: "Protect my portfolio from a crash"
        → Strategy type: "hedge", candidates: ["protective_put", "bear_put_spread"]
        """
        
        user_prompt = f"""
        Parse this trading request into structured intent JSON:
        
        "{user_text}"
        
        Remember: Output ONLY the JSON, no explanations.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Low temperature for consistent parsing
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip()
            
            # Clean up common JSON formatting issues
            content = content.replace("```json", "").replace("```", "").strip()
            
            # Parse JSON
            intent = json.loads(content)
            
            # Add metadata
            intent["_llm_model"] = self.model
            intent["_original_text"] = user_text
            
            return intent
            
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise RuntimeError(f"LLM API call failed: {e}")
    
    def explain_strategy_plan(self, plan: Dict[str, Any]) -> str:
        """
        Generate natural language explanation of a strategy plan.
        
        Args:
            plan: Strategy plan dictionary
            
        Returns:
            Human-readable explanation
        """
        system_prompt = f"""
        You are a professional options trading assistant. Explain trading strategy plans in simple, 
        clear language that a trader can understand quickly.
        
        {self.trading_context}
        
        GUIDELINES:
        1. Keep explanations concise but complete
        2. Mention key risk/reward characteristics
        3. Explain market conditions where this works well
        4. Include specific details like strikes, expiry, max risk
        5. Use confident, professional tone
        """
        
        user_prompt = f"""
        Explain this trading strategy plan in 2-3 sentences:
        
        {json.dumps(plan, indent=2)}
        
        Focus on: strategy type, symbol, expiry, max risk, and why this makes sense.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Strategy plan for {plan.get('symbol', 'unknown')} {plan.get('strategy', 'unknown')} expiring {plan.get('expiry', 'unknown')}. Max risk: {plan.get('sizing', {}).get('max_risk_per_trade', 'unknown')}."
    
    def assess_market_conditions(self, market_data: Dict[str, Any]) -> str:
        """
        Generate market condition assessment for strategy selection.
        
        Args:
            market_data: Current market metrics (IV, trends, etc.)
            
        Returns:
            Market assessment summary
        """
        system_prompt = f"""
        You are a professional options trading analyst. Assess current market conditions and 
        recommend optimal strategy types.
        
        {self.trading_context}
        
        Provide a brief assessment mentioning:
        1. IV regime and implications
        2. Market trend and strength
        3. Recommended strategy types
        4. Key risks to watch
        """
        
        user_prompt = f"""
        Assess these market conditions and recommend strategy approach:
        
        {json.dumps(market_data, indent=2)}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,
                max_tokens=400
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return "Market conditions assessment unavailable. Proceeding with conservative approach."

# Convenience function for backward compatibility
def llm_parse(system: str, user: str, model: str = "gpt-4") -> Dict[str, Any]:
    """
    Simple LLM parsing function.
    
    Args:
        system: System prompt
        user: User prompt
        model: Model to use
        
    Returns:
        Parsed JSON response
    """
    client = LLMClient(model=model)
    
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()
        
        return json.loads(content)
        
    except Exception as e:
        return {"error": str(e), "raw_response": content if 'content' in locals() else None}