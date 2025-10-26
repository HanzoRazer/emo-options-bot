"""
LLM Orchestrator for EMO Options Bot Phase 3
Converts natural language intent into structured trade plans with reasoning.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from llm.schemas import (
    TradePlan, OutlookType, StrategyType, ConfidenceLevel, RiskLevel,
    DataCitation, Constraint, Rationale, Mitigation, serialize_model
)
from i18n.lang import t

class LLMProvider:
    """Abstract base for LLM providers."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
    def complete(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Complete a chat conversation with optional tool calls."""
        raise NotImplementedError
        
class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        super().__init__(api_key, model)
        if not HAS_OPENAI:
            raise ImportError("OpenAI package not installed. Run: pip install openai")
        
        if not self.api_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable.")
        
        openai.api_key = self.api_key
        
    def complete(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Complete using OpenAI API."""
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,  # Low temperature for consistent outputs
                "max_tokens": 2000
            }
            
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            
            response = openai.ChatCompletion.create(**kwargs)
            
            return {
                "content": response.choices[0].message.content,
                "tool_calls": getattr(response.choices[0].message, "tool_calls", None),
                "model": response.model,
                "usage": response.usage._asdict() if response.usage else {},
                "finish_reason": response.choices[0].finish_reason
            }
        except Exception as e:
            return {"error": str(e)}

class MockProvider(LLMProvider):
    """Mock provider for testing and development."""
    
    def complete(self, messages: List[Dict[str, str]], tools: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Mock completion for testing."""
        # Extract user intent from last message
        user_message = messages[-1]["content"].lower()
        
        # Simple intent detection for demo
        if "spy" in user_message:
            symbol = "SPY"
        elif "qqq" in user_message:
            symbol = "QQQ"
        elif "aapl" in user_message:
            symbol = "AAPL"
        else:
            symbol = "SPY"
            
        outlook = "neutral"
        if "bullish" in user_message or "up" in user_message:
            outlook = "bullish"
        elif "bearish" in user_message or "down" in user_message:
            outlook = "bearish"
            
        # Generate mock trade plan
        mock_plan = {
            "symbol": symbol,
            "outlook": outlook,
            "strategy_type": "iron_condor",
            "horizon_days": 30,
            "risk_level": "moderate",
            "constraints": {
                "max_loss_pct": 2.0,
                "max_margin": 5000,
                "avoid_earnings": True
            },
            "rationale": {
                "summary": f"Mock analysis suggests {outlook} outlook for {symbol} over 30 days",
                "key_factors": ["Mock IV rank", "Mock technical signals", "Mock market regime"],
                "data_citations": [
                    {
                        "source": "mock_iv_data",
                        "value": 0.25,
                        "timestamp": datetime.utcnow().isoformat(),
                        "confidence": 0.85
                    }
                ],
                "what_could_go_wrong": [
                    {
                        "risk": "Market shock",
                        "mitigation": "Position sizing and stop losses",
                        "probability": 0.15,
                        "impact": "High"
                    }
                ],
                "confidence": "medium"
            },
            "model_version": "mock-v1.0",
            "prompt_hash": "mock-hash-123"
        }
        
        return {
            "content": json.dumps(mock_plan, indent=2),
            "model": "mock-gpt-4",
            "usage": {"total_tokens": 500},
            "finish_reason": "stop"
        }

class ToolRegistry:
    """Registry of tools available to the LLM."""
    
    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.tool_schemas: List[Dict] = []
        
    def register_tool(self, name: str, func: Callable, schema: Dict):
        """Register a tool with its function and schema."""
        self.tools[name] = func
        self.tool_schemas.append(schema)
        
    def call_tool(self, name: str, **kwargs) -> Any:
        """Call a registered tool."""
        if name not in self.tools:
            raise ValueError(f"Tool {name} not registered")
        return self.tools[name](**kwargs)

class LLMOrchestrator:
    """Main LLM orchestrator for trade planning."""
    
    def __init__(self, provider: Optional[LLMProvider] = None, lang: str = "en"):
        self.provider = provider or self._create_default_provider()
        self.lang = lang
        self.tools = ToolRegistry()
        self._setup_tools()
        
        # Load prompt templates
        self.prompt_dir = Path(__file__).parent / "prompt_kits"
        self.prompt_dir.mkdir(exist_ok=True)
        
    def _create_default_provider(self) -> LLMProvider:
        """Create default LLM provider based on environment."""
        provider_type = os.getenv("EMO_LLM_PROVIDER", "mock").lower()
        
        if provider_type == "openai" and HAS_OPENAI:
            return OpenAIProvider()
        else:
            return MockProvider()
            
    def _setup_tools(self):
        """Setup available tools for the LLM."""
        # Market data tool
        self.tools.register_tool(
            "get_market_data",
            self._get_market_data,
            {
                "type": "function",
                "function": {
                    "name": "get_market_data",
                    "description": "Get current market data for a symbol",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Trading symbol"},
                            "data_type": {"type": "string", "enum": ["price", "iv_rank", "volume"]}
                        },
                        "required": ["symbol", "data_type"]
                    }
                }
            }
        )
        
        # IV rank tool
        self.tools.register_tool(
            "get_iv_rank",
            self._get_iv_rank,
            {
                "type": "function", 
                "function": {
                    "name": "get_iv_rank",
                    "description": "Get implied volatility rank for a symbol",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string", "description": "Trading symbol"}
                        },
                        "required": ["symbol"]
                    }
                }
            }
        )
        
    def _get_market_data(self, symbol: str, data_type: str) -> Dict[str, Any]:
        """Mock market data retrieval."""
        # In production, this would connect to real data sources
        mock_data = {
            "SPY": {"price": 450.0, "iv_rank": 0.35, "volume": 50000000},
            "QQQ": {"price": 380.0, "iv_rank": 0.42, "volume": 30000000}, 
            "AAPL": {"price": 175.0, "iv_rank": 0.28, "volume": 40000000}
        }
        
        return {
            "symbol": symbol,
            "data_type": data_type,
            "value": mock_data.get(symbol, {}).get(data_type, 0),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "mock_data"
        }
        
    def _get_iv_rank(self, symbol: str) -> Dict[str, Any]:
        """Get IV rank for symbol."""
        return self._get_market_data(symbol, "iv_rank")
        
    def _load_prompt_template(self, template_name: str) -> str:
        """Load a prompt template from file."""
        template_path = self.prompt_dir / f"{template_name}.md"
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")
        else:
            # Return default template
            return self._get_default_template(template_name)
            
    def _get_default_template(self, template_name: str) -> str:
        """Get default prompt templates."""
        templates = {
            "system": """You are an expert options trading advisor for EMO Options Bot. 
Your role is to analyze market conditions and generate structured trade plans.

CRITICAL REQUIREMENTS:
1. Always output valid JSON matching the TradePlan schema
2. Cite all data sources with timestamps
3. Include risk analysis with specific mitigations
4. Be conservative with position sizing
5. Avoid trades through earnings unless explicitly requested

Current market regime and available data will be provided via tool calls.""",

            "trade_analysis": """Analyze the following trading request and generate a detailed TradePlan:

User Request: {user_request}

Please:
1. Use available tools to gather market data
2. Assess market outlook and volatility regime
3. Select appropriate strategy for the outlook
4. Size position conservatively
5. Identify key risks and mitigations
6. Output as valid TradePlan JSON

Be thorough in your analysis and cite specific data points."""
        }
        
        return templates.get(template_name, "Default template not found.")
        
    def _hash_prompt(self, prompt: str) -> str:
        """Generate hash of prompt for audit trail."""
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]
        
    def plan_trade(self, user_request: str) -> Dict[str, Any]:
        """Convert user request into structured trade plan."""
        try:
            # Load prompt templates
            system_prompt = self._load_prompt_template("system")
            analysis_prompt = self._load_prompt_template("trade_analysis").format(
                user_request=user_request
            )
            
            # Build conversation
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": analysis_prompt}
            ]
            
            # Get LLM response with tools
            response = self.provider.complete(messages, self.tools.tool_schemas)
            
            if "error" in response:
                return {
                    "success": False,
                    "error": response["error"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Parse response
            try:
                # If there were tool calls, handle them
                if response.get("tool_calls"):
                    # Process tool calls and get final response
                    # This is simplified - full implementation would handle multiple rounds
                    pass
                
                # Parse the trade plan
                content = response["content"]
                if content.startswith("```json"):
                    content = content.split("```json")[1].split("```")[0]
                elif content.startswith("```"):
                    content = content.split("```")[1].split("```")[0]
                    
                plan_data = json.loads(content)
                
                # Add metadata
                plan_data.update({
                    "model_version": response.get("model", "unknown"),
                    "prompt_hash": self._hash_prompt(analysis_prompt),
                    "created_at": datetime.utcnow().isoformat()
                })
                
                # Validate against schema
                trade_plan = TradePlan.model_validate(plan_data)
                
                return {
                    "success": True,
                    "trade_plan": trade_plan,
                    "raw_response": response,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except (json.JSONDecodeError, ValueError) as e:
                return {
                    "success": False,
                    "error": f"Failed to parse LLM response: {e}",
                    "raw_content": response.get("content", ""),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Orchestrator error: {e}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    def explain_plan(self, trade_plan: TradePlan) -> str:
        """Generate human-readable explanation of trade plan."""
        explanation = f"""
🎯 TRADE PLAN: {trade_plan.strategy_type.value.upper()} on {trade_plan.symbol}

📊 Market Outlook: {trade_plan.outlook.value.title()}
⏰ Time Horizon: {trade_plan.horizon_days} days
🎲 Risk Level: {trade_plan.risk_level.value.title()}

💡 Reasoning:
{trade_plan.rationale.summary}

🔑 Key Factors:
""" + "\n".join([f"• {factor}" for factor in trade_plan.rationale.key_factors])

        if trade_plan.rationale.data_citations:
            explanation += "\n\n📈 Supporting Data:\n"
            for citation in trade_plan.rationale.data_citations:
                explanation += f"• {citation.source}: {citation.value} (confidence: {citation.confidence:.0%})\n"

        if trade_plan.rationale.what_could_go_wrong:
            explanation += "\n⚠️ Risk Analysis:\n"
            for risk in trade_plan.rationale.what_could_go_wrong:
                explanation += f"• {risk.risk} ({risk.probability:.0%} chance): {risk.mitigation}\n"

        explanation += f"\n🎯 Confidence: {trade_plan.rationale.confidence.value.title()}"
        
        return explanation

def create_orchestrator(provider_type: str = "auto", lang: str = "en") -> LLMOrchestrator:
    """Factory function to create LLM orchestrator."""
    if provider_type == "auto":
        provider_type = os.getenv("EMO_LLM_PROVIDER", "mock")
        
    if provider_type == "openai":
        provider = OpenAIProvider()
    else:
        provider = MockProvider()
        
    return LLMOrchestrator(provider, lang)