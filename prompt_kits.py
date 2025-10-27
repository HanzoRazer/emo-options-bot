"""
Phase 3 Prompt Kits - LLM prompt management and templates
Provides structured prompts for different trading analysis scenarios
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class PromptTemplate:
    """Template for LLM prompts"""
    name: str
    category: str
    template: str
    variables: List[str]
    description: str
    examples: List[Dict[str, Any]]


class PromptManager:
    """Manages trading-focused prompt templates"""
    
    def __init__(self):
        """Initialize with predefined prompt templates"""
        self.templates = self._load_default_templates()
    
    def _load_default_templates(self) -> Dict[str, PromptTemplate]:
        """Load default prompt templates for options trading"""
        
        templates = {}
        
        # Market Analysis Prompts
        templates["market_analysis"] = PromptTemplate(
            name="market_analysis",
            category="analysis",
            template="""You are an expert options trader analyzing market conditions for {symbol}.

Current market data:
- Price: ${current_price}
- Recent context: {market_context}
- Time horizon: {time_horizon}
- User request: {user_input}

Provide analysis covering:
1. Market outlook (bullish/bearish/neutral/volatile)
2. Key factors influencing price
3. Volatility assessment
4. Time decay considerations
5. Recommended strategy direction

Format your response as structured analysis with confidence level.""",
            variables=["symbol", "current_price", "market_context", "time_horizon", "user_input"],
            description="Comprehensive market analysis for options trading",
            examples=[
                {
                    "symbol": "SPY",
                    "current_price": "450.00",
                    "market_context": "Recent Fed meeting, earnings season",
                    "time_horizon": "2 weeks",
                    "user_input": "I want to trade SPY options"
                }
            ]
        )
        
        # Strategy Selection Prompts
        templates["strategy_selection"] = PromptTemplate(
            name="strategy_selection",
            category="strategy",
            template="""Based on the market analysis for {symbol}, recommend an appropriate options strategy.

Market Analysis:
- Outlook: {market_outlook}
- Volatility: {volatility_assessment}
- Price target: {price_target}
- Time horizon: {time_horizon}

Risk constraints:
- Max loss: ${max_risk}
- Portfolio allocation: {portfolio_allocation}%

Consider these strategy types:
- Iron Condor (neutral, range-bound)
- Put Credit Spread (bullish)
- Call Credit Spread (bearish)
- Long Call/Put (directional)
- Straddle/Strangle (volatility plays)

Recommend the best strategy with:
1. Strategy name and rationale
2. Approximate strike selection
3. Expected profit/loss range
4. Probability of success
5. Risk considerations""",
            variables=["symbol", "market_outlook", "volatility_assessment", "price_target", 
                      "time_horizon", "max_risk", "portfolio_allocation"],
            description="Strategy recommendation based on market analysis",
            examples=[]
        )
        
        # Risk Assessment Prompts
        templates["risk_assessment"] = PromptTemplate(
            name="risk_assessment",
            category="risk",
            template="""Assess the risk profile of this options strategy for {symbol}:

Strategy Details:
- Type: {strategy_type}
- Legs: {legs_description}
- Max loss: ${max_loss}
- Max profit: ${max_profit}
- Current price: ${current_price}

Portfolio Context:
- Account size: ${account_equity}
- Current risk: {current_portfolio_risk}%
- Position size: {position_size} contracts

Evaluate:
1. Risk-reward ratio
2. Probability of profit
3. Sensitivity to price movement
4. Volatility impact
5. Time decay effects
6. Portfolio impact
7. Risk mitigation suggestions

Provide risk score (1-100) and recommendation.""",
            variables=["symbol", "strategy_type", "legs_description", "max_loss", "max_profit",
                      "current_price", "account_equity", "current_portfolio_risk", "position_size"],
            description="Comprehensive risk assessment for options strategies",
            examples=[]
        )
        
        # Voice Command Processing
        templates["voice_command"] = PromptTemplate(
            name="voice_command",
            category="nlp",
            template="""Parse this voice command for options trading: "{user_voice_input}"

Extract and identify:
1. Action type (buy, sell, analyze, check, cancel)
2. Symbol/ticker
3. Strategy type (if mentioned)
4. Quantity or size
5. Risk parameters
6. Time preferences
7. Any special instructions

Provide structured response:
{{
    "action": "...",
    "symbol": "...",
    "strategy": "...",
    "parameters": {{}},
    "confidence": 0.XX,
    "clarifications_needed": []
}}

If unclear, ask for clarification.""",
            variables=["user_voice_input"],
            description="Parse natural language voice commands for trading",
            examples=[
                {
                    "user_voice_input": "Buy SPY iron condor with max risk 500 dollars"
                }
            ]
        )
        
        # Portfolio Review
        templates["portfolio_review"] = PromptTemplate(
            name="portfolio_review",
            category="analysis",
            template="""Review this options portfolio and provide insights:

Portfolio Summary:
- Total equity: ${total_equity}
- Available cash: ${available_cash}
- Current positions: {position_count}
- Total risk: {total_risk}%

Active Positions:
{positions_summary}

Market Environment:
- VIX level: {vix_level}
- Market trend: {market_trend}
- Earnings calendar: {upcoming_earnings}

Provide analysis on:
1. Risk concentration
2. Strategy diversification
3. Expiration management
4. Profit/loss opportunities
5. Adjustment recommendations
6. New position suggestions

Format as actionable portfolio insights.""",
            variables=["total_equity", "available_cash", "position_count", "total_risk",
                      "positions_summary", "vix_level", "market_trend", "upcoming_earnings"],
            description="Comprehensive portfolio review and recommendations",
            examples=[]
        )
        
        return templates
    
    def get_prompt(self, template_name: str, **kwargs) -> str:
        """Get formatted prompt from template"""
        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")
        
        template = self.templates[template_name]
        
        # Check for missing variables
        missing_vars = [var for var in template.variables if var not in kwargs]
        if missing_vars:
            # Provide defaults for missing variables
            defaults = {
                "symbol": "SPY",
                "current_price": "450.00",
                "market_context": "Normal market conditions",
                "time_horizon": "2 weeks",
                "user_input": "Trade analysis request",
                "max_risk": "500",
                "account_equity": "10000",
                "portfolio_allocation": "5"
            }
            
            for var in missing_vars:
                if var in defaults:
                    kwargs[var] = defaults[var]
                else:
                    kwargs[var] = f"[{var}_not_provided]"
        
        try:
            return template.template.format(**kwargs)
        except KeyError as e:
            return f"Error formatting template '{template_name}': missing variable {e}"
    
    def list_templates(self) -> Dict[str, str]:
        """List available templates with descriptions"""
        return {
            name: template.description 
            for name, template in self.templates.items()
        }
    
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """Get detailed information about a template"""
        if template_name not in self.templates:
            return {"error": f"Template '{template_name}' not found"}
        
        template = self.templates[template_name]
        return {
            "name": template.name,
            "category": template.category,
            "description": template.description,
            "variables": template.variables,
            "examples": template.examples
        }
    
    def add_template(self, template: PromptTemplate) -> bool:
        """Add custom template"""
        try:
            self.templates[template.name] = template
            return True
        except Exception:
            return False
    
    def create_market_analysis_prompt(self, symbol: str, user_input: str, **kwargs) -> str:
        """Convenience method for market analysis prompts"""
        return self.get_prompt("market_analysis", 
                             symbol=symbol, 
                             user_input=user_input, 
                             **kwargs)
    
    def create_strategy_prompt(self, symbol: str, market_outlook: str, **kwargs) -> str:
        """Convenience method for strategy selection prompts"""
        return self.get_prompt("strategy_selection",
                             symbol=symbol,
                             market_outlook=market_outlook,
                             **kwargs)
    
    def create_risk_prompt(self, symbol: str, strategy_type: str, **kwargs) -> str:
        """Convenience method for risk assessment prompts"""
        return self.get_prompt("risk_assessment",
                             symbol=symbol,
                             strategy_type=strategy_type,
                             **kwargs)
    
    def parse_voice_command_prompt(self, voice_input: str) -> str:
        """Convenience method for voice command parsing"""
        return self.get_prompt("voice_command", user_voice_input=voice_input)
    
    def health_check(self) -> Dict[str, Any]:
        """Check prompt manager health"""
        try:
            # Test template rendering
            test_prompt = self.get_prompt("market_analysis", 
                                        symbol="SPY", 
                                        user_input="test")
            
            return {
                "status": "healthy",
                "templates_loaded": len(self.templates),
                "categories": list(set(t.category for t in self.templates.values())),
                "test_successful": len(test_prompt) > 100
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Global prompt manager instance
_prompt_manager = None

def get_prompt_manager() -> PromptManager:
    """Get global prompt manager instance"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager


# Convenience functions
def get_analysis_prompt(symbol: str, user_input: str, **kwargs) -> str:
    """Get market analysis prompt"""
    manager = get_prompt_manager()
    return manager.create_market_analysis_prompt(symbol, user_input, **kwargs)


def get_strategy_prompt(symbol: str, outlook: str, **kwargs) -> str:
    """Get strategy selection prompt"""
    manager = get_prompt_manager()
    return manager.create_strategy_prompt(symbol, outlook, **kwargs)


def get_risk_prompt(symbol: str, strategy: str, **kwargs) -> str:
    """Get risk assessment prompt"""
    manager = get_prompt_manager()
    return manager.create_risk_prompt(symbol, strategy, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    print("📝 Testing Phase 3 Prompt Kits")
    
    # Initialize prompt manager
    manager = PromptManager()
    print(f"✅ Prompt manager initialized")
    
    # Health check
    health = manager.health_check()
    print(f"Health: {health['status']}")
    print(f"Templates loaded: {health['templates_loaded']}")
    
    # List available templates
    templates = manager.list_templates()
    print(f"\n📋 Available templates:")
    for name, desc in templates.items():
        print(f"   {name}: {desc}")
    
    # Test different prompt types
    print(f"\n🎯 Testing prompt generation...")
    
    # Test 1: Market analysis
    analysis_prompt = manager.create_market_analysis_prompt(
        symbol="SPY",
        user_input="I want to trade SPY options with neutral outlook",
        current_price="450.00",
        market_context="Post-earnings consolidation"
    )
    print(f"\n📊 Market Analysis Prompt ({len(analysis_prompt)} chars):")
    print(analysis_prompt[:200] + "..." if len(analysis_prompt) > 200 else analysis_prompt)
    
    # Test 2: Strategy selection
    strategy_prompt = manager.create_strategy_prompt(
        symbol="QQQ",
        market_outlook="bullish",
        volatility_assessment="low",
        max_risk="300"
    )
    print(f"\n⚙️ Strategy Prompt ({len(strategy_prompt)} chars):")
    print(strategy_prompt[:200] + "..." if len(strategy_prompt) > 200 else strategy_prompt)
    
    # Test 3: Voice command
    voice_prompt = manager.parse_voice_command_prompt(
        "Buy SPY iron condor with max risk 500 dollars"
    )
    print(f"\n🎤 Voice Command Prompt ({len(voice_prompt)} chars):")
    print(voice_prompt[:200] + "..." if len(voice_prompt) > 200 else voice_prompt)
    
    print(f"\n📝 Prompt kits testing complete")