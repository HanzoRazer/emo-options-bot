"""
Phase 3 Orchestrator - LLM orchestration and market analysis
Handles natural language processing and market analysis coordination
"""

from __future__ import annotations
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

# Import schemas if available
try:
    from schemas import MarketAnalysis, TradePlan, StrategyType
except ImportError:
    # Fallback for development
    MarketAnalysis = Dict[str, Any]
    TradePlan = Dict[str, Any]
    StrategyType = str


@dataclass
class LLMConfig:
    """LLM provider configuration"""
    provider: str = "mock"
    api_key: Optional[str] = None
    model: str = "gpt-4"
    temperature: float = 0.1
    max_tokens: int = 1000


class MockLLMProvider:
    """Mock LLM provider for testing and development"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.call_count = 0
    
    def analyze_market(self, symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mock market analysis"""
        self.call_count += 1
        
        # Simple mock responses based on symbol
        if symbol == "SPY":
            outlook = "neutral"
            reasoning = "SPY showing sideways consolidation pattern"
        elif symbol.startswith("QQQ"):
            outlook = "bullish"
            reasoning = "Tech sector showing strength"
        else:
            outlook = "neutral"
            reasoning = f"Standard market analysis for {symbol}"
        
        return {
            "symbol": symbol,
            "outlook": outlook,
            "reasoning": reasoning,
            "time_horizon": "1-2 weeks",
            "confidence": 0.7,
            "key_factors": ["market consolidation", "low volatility", "neutral sentiment"],
            "timestamp": datetime.now()
        }
    
    def suggest_strategy(self, analysis: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Mock strategy suggestion"""
        outlook = analysis.get("outlook", "neutral")
        symbol = analysis.get("symbol", "SPY")
        
        # Simple strategy mapping
        if outlook == "neutral":
            strategy = "iron_condor"
            rationale = "Range-bound market suggests neutral strategy"
        elif outlook == "bullish":
            strategy = "put_credit_spread"
            rationale = "Bullish outlook suggests selling puts"
        elif outlook == "bearish":
            strategy = "call_credit_spread"
            rationale = "Bearish outlook suggests selling calls"
        else:
            strategy = "straddle"
            rationale = "High volatility suggests long straddle"
        
        return {
            "strategy_type": strategy,
            "rationale": rationale,
            "expected_profit": 200.0,
            "max_risk": 500.0,
            "probability_of_profit": 0.65,
            "time_horizon": "2 weeks"
        }


class OpenAIProvider:
    """OpenAI GPT provider (placeholder for real implementation)"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.api_key = config.api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key and config.provider == "openai":
            raise ValueError("OpenAI API key required for OpenAI provider")
    
    def analyze_market(self, symbol: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Real OpenAI market analysis (placeholder)"""
        # For now, fallback to mock
        mock_provider = MockLLMProvider(self.config)
        return mock_provider.analyze_market(symbol, context)
    
    def suggest_strategy(self, analysis: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Real OpenAI strategy suggestion (placeholder)"""
        # For now, fallback to mock
        mock_provider = MockLLMProvider(self.config)
        return mock_provider.suggest_strategy(analysis, constraints)


class Orchestrator:
    """Main LLM orchestrator for Phase 3"""
    
    def __init__(self, provider: str = None, **kwargs):
        """Initialize orchestrator with LLM provider"""
        provider = provider or os.getenv("LLM_PROVIDER", "mock")
        
        self.config = LLMConfig(
            provider=provider,
            api_key=kwargs.get("api_key"),
            model=kwargs.get("model", "gpt-4"),
            temperature=kwargs.get("temperature", 0.1),
            max_tokens=kwargs.get("max_tokens", 1000)
        )
        
        # Initialize provider
        if provider.lower() == "mock":
            self.provider = MockLLMProvider(self.config)
        elif provider.lower() == "openai":
            self.provider = OpenAIProvider(self.config)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        self.provider_name = provider
    
    def analyze(self, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user input and market context"""
        # Extract symbol from context or input
        symbol = context.get("symbol", "SPY")
        if not symbol and "symbol" in user_input.upper():
            # Simple symbol extraction
            words = user_input.upper().split()
            for word in words:
                if len(word) <= 5 and word.isalpha():
                    symbol = word
                    break
        
        # Get market analysis from LLM provider
        analysis = self.provider.analyze_market(symbol, context)
        
        # Add orchestrator metadata
        analysis["orchestrator_version"] = "phase3_v1.0"
        analysis["provider"] = self.provider_name
        analysis["processed_input"] = user_input
        
        return analysis
    
    def synthesize_plan(self, analysis: Dict[str, Any], constraints: Dict[str, Any] = None) -> Dict[str, Any]:
        """Synthesize trading plan from analysis"""
        constraints = constraints or {}
        
        # Get strategy suggestion from provider
        strategy = self.provider.suggest_strategy(analysis, constraints)
        
        # Create trade plan
        plan = {
            "symbol": analysis.get("symbol", "SPY"),
            "thesis": analysis.get("reasoning", "AI-generated market thesis"),
            "strategy_type": strategy.get("strategy_type", "iron_condor"),
            "target_profit": strategy.get("expected_profit"),
            "max_risk": strategy.get("max_risk"),
            "time_horizon": strategy.get("time_horizon", "2 weeks"),
            "confidence": analysis.get("confidence", 0.7),
            "analysis": analysis,
            "constraints": constraints
        }
        
        return plan
    
    def process_request(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Complete request processing pipeline"""
        context = context or {}
        
        try:
            # Step 1: Analyze input and market
            analysis = self.analyze(user_input, context)
            
            # Step 2: Synthesize trading plan
            plan = self.synthesize_plan(analysis, context.get("constraints"))
            
            # Step 3: Return complete response
            return {
                "success": True,
                "analysis": analysis,
                "plan": plan,
                "user_input": user_input,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "user_input": user_input,
                "timestamp": datetime.now().isoformat()
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Check orchestrator health"""
        try:
            # Test with simple analysis
            test_analysis = self.provider.analyze_market("SPY", {})
            
            return {
                "status": "healthy",
                "provider": self.provider_name,
                "config": {
                    "model": self.config.model,
                    "temperature": self.config.temperature
                },
                "test_successful": bool(test_analysis)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "provider": self.provider_name,
                "error": str(e)
            }


# Example usage and testing
if __name__ == "__main__":
    import json
    
    # Test orchestrator
    print("🤖 Testing Phase 3 Orchestrator")
    
    # Test with mock provider
    orchestrator = Orchestrator(provider="mock")
    print(f"✅ Orchestrator initialized with {orchestrator.provider_name} provider")
    
    # Health check
    health = orchestrator.health_check()
    print(f"Health: {health['status']}")
    
    # Test analysis
    response = orchestrator.process_request(
        "I want to trade SPY with a neutral outlook",
        context={"symbol": "SPY", "constraints": {"max_loss": 500}}
    )
    
    if response["success"]:
        print(f"✅ Analysis successful")
        print(f"   Strategy: {response['plan']['strategy_type']}")
        print(f"   Confidence: {response['analysis']['confidence']}")
        print(f"   Reasoning: {response['analysis']['reasoning']}")
    else:
        print(f"❌ Analysis failed: {response['error']}")
    
    # Test with different symbols
    for symbol in ["QQQ", "TSLA", "AAPL"]:
        response = orchestrator.analyze(f"Analyze {symbol}", {"symbol": symbol})
        print(f"   {symbol}: {response['outlook']} ({response['confidence']})")
    
    print("\n🎯 Orchestrator testing complete")