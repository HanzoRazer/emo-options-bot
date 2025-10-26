"""LLM Orchestrator (Phase 3)
Safe to import without OpenAI: falls back to mock outputs."""
from __future__ import annotations
import os
from typing import Optional
from .schemas import MarketView

class Orchestrator:
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or os.getenv("EMO_LLM_PROVIDER", "mock")
        self._openai = None
        if self.provider.lower() == "openai":
            try:
                import openai  # type: ignore
                openai.api_key = os.getenv("OPENAI_API_KEY","")
                self._openai = openai
            except Exception:
                self.provider = "mock"

    def analyze(self, natural_text: str) -> MarketView:
        # Very light mock "NLP": pick a symbol + outlook from text
        text = natural_text.lower()
        sym = "SPY"
        for s in ["SPY","QQQ","AAPL","MSFT","IWM","DIA"]:
            if s.lower() in text:
                sym = s
                break
        outlook = "neutral"
        if "sideways" in text or "range" in text:
            outlook = "range"
        elif "volatile" in text or "volatility" in text:
            outlook = "volatile"
        elif "bull" in text or "up" in text:
            outlook = "bullish"
        elif "bear" in text or "down" in text:
            outlook = "bearish"
        return MarketView(symbol=sym, outlook=outlook, horizon_days=7, confidence=0.55, notes="mock-llm")
    "openai": False,
    "anthropic": False,
    "ollama": False
}

# OpenAI detection
try:
    import openai
    if os.getenv("OPENAI_API_KEY"):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        _PROVIDERS_AVAILABLE["openai"] = True
        logger.info("OpenAI provider initialized successfully")
except ImportError:
    logger.info("OpenAI not available (missing openai package)")
except Exception as e:
    logger.warning(f"OpenAI initialization failed: {e}")

# Anthropic detection
try:
    import anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        _PROVIDERS_AVAILABLE["anthropic"] = True
        logger.info("Anthropic provider initialized successfully")
except ImportError:
    logger.info("Anthropic not available (missing anthropic package)")
except Exception as e:
    logger.warning(f"Anthropic initialization failed: {e}")

# Ollama detection (local LLM)
try:
    import requests
    # Test if Ollama is running locally
    response = requests.get("http://localhost:11434/api/tags", timeout=2)
    if response.status_code == 200:
        _PROVIDERS_AVAILABLE["ollama"] = True
        logger.info("Ollama provider detected and available")
except Exception:
    logger.info("Ollama not available (not running or unreachable)")

# Enhanced system prompts for different analysis types
SYSTEM_PROMPTS = {
    "analysis": """You are an expert options trading analyst for the EMO Options Bot. 
Analyze market conditions and provide structured trading recommendations.

Focus on:
- Liquid US equities and ETFs (SPY, QQQ, IWM, DIA, major stocks)
- Professional options strategies (Iron Condor, Put Credit Spreads, Covered Calls, etc.)
- Risk management and position sizing
- Current market volatility and sentiment

Always provide structured analysis with clear risk parameters and confidence levels.
Be conservative with risk assessment and realistic about profit expectations.""",

    "risk_assessment": """You are a risk management specialist for options trading.
Evaluate proposed trades for risk exposure, compliance, and portfolio impact.

Consider:
- Maximum loss scenarios
- Portfolio concentration risk
- Volatility exposure (vega risk)
- Time decay characteristics (theta)
- Market correlation risks

Provide specific risk metrics and recommended position sizes.""",

    "market_outlook": """You are a market analysis expert focusing on options-relevant factors.
Analyze current market conditions, volatility environment, and key catalysts.

Evaluate:
- Implied volatility levels vs historical volatility
- Upcoming earnings, events, and economic data
- Market sentiment and positioning
- Sector rotation and momentum factors

Provide actionable insights for options strategy selection."""
}

class LLMProvider:
    """Base class for LLM providers with common interface"""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.request_count = 0
        self.error_count = 0
        self.last_request_time = None
    
    def is_available(self) -> bool:
        """Check if provider is available and configured"""
        return _PROVIDERS_AVAILABLE.get(self.provider_name, False)
    
    def call_llm(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """Make LLM call - to be implemented by subclasses"""
        raise NotImplementedError
    
    def track_request(self, success: bool = True):
        """Track request metrics"""
        self.request_count += 1
        self.last_request_time = datetime.utcnow()
        if not success:
            self.error_count += 1

class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation"""
    
    def __init__(self):
        super().__init__("openai")
        self.client = None
        if self.is_available():
            try:
                self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def call_llm(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """Make OpenAI API call"""
        if not self.client:
            return None
            
        try:
            model = kwargs.get("model", "gpt-4o-mini")
            temperature = kwargs.get("temperature", 0.2)
            max_tokens = kwargs.get("max_tokens", 1500)
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=30.0
            )
            
            self.track_request(success=True)
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            self.track_request(success=False)
            return None

class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation"""
    
    def __init__(self):
        super().__init__("anthropic")
        self.client = None
        if self.is_available():
            try:
                self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
    
    def call_llm(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """Make Anthropic API call"""
        if not self.client:
            return None
            
        try:
            model = kwargs.get("model", "claude-3-haiku-20240307")
            max_tokens = kwargs.get("max_tokens", 1500)
            
            # Convert messages format for Anthropic
            system_msg = ""
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    user_messages.append(msg)
            
            response = self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_msg,
                messages=user_messages,
                timeout=30.0
            )
            
            self.track_request(success=True)
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            self.track_request(success=False)
            return None

class OllamaProvider(LLMProvider):
    """Local Ollama provider implementation"""
    
    def __init__(self):
        super().__init__("ollama")
        self.base_url = "http://localhost:11434"
    
    def call_llm(self, messages: List[Dict[str, str]], **kwargs) -> Optional[str]:
        """Make Ollama API call"""
        if not self.is_available():
            return None
            
        try:
            import requests
            
            model = kwargs.get("model", "llama3.2")
            
            # Convert messages to prompt for Ollama
            prompt = ""
            for msg in messages:
                if msg["role"] == "system":
                    prompt += f"System: {msg['content']}\n\n"
                elif msg["role"] == "user":
                    prompt += f"User: {msg['content']}\n\n"
                elif msg["role"] == "assistant":
                    prompt += f"Assistant: {msg['content']}\n\n"
            
            prompt += "Assistant: "
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get("temperature", 0.2),
                        "num_predict": kwargs.get("max_tokens", 1500)
                    }
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                self.track_request(success=True)
                return result.get("response", "")
            else:
                self.track_request(success=False)
                return None
                
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            self.track_request(success=False)
            return None

def _extract_json_from_response(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON from LLM response with multiple fallback patterns"""
    if not text:
        return None
    
    # Try to find JSON blocks
    json_patterns = [
        r'```json\s*(\{.*?\})\s*```',
        r'```\s*(\{.*?\})\s*```',
        r'(\{.*?\})',
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
    
    return None

def _heuristic_analysis(prompt: str, equity: float = 10000.0) -> AnalysisPlan:
    """Enhanced heuristic analysis with better pattern matching"""
    p = prompt.lower().strip()
    
    # Enhanced pattern matching for market outlook
    outlook = "neutral"
    strategy_hint: Optional[StrategyType] = None
    confidence = 0.5
    
    # Sentiment analysis patterns
    bullish_patterns = [
        "bullish", "bull", "up", "rally", "breakout", "momentum", "call", 
        "long", "buy", "upside", "growth", "positive"
    ]
    bearish_patterns = [
        "bearish", "bear", "down", "selloff", "dump", "crash", "put", 
        "short", "sell", "downside", "decline", "negative"
    ]
    neutral_patterns = [
        "sideways", "range", "bound", "chop", "consolidation", "theta", 
        "iron condor", "credit spread"
    ]
    volatile_patterns = [
        "volatile", "volatility", "big move", "wild", "explosive", "straddle", 
        "strangle", "vix", "uncertain"
    ]
    
    # Score each outlook
    scores = {
        "bullish": sum(1 for pattern in bullish_patterns if pattern in p),
        "bearish": sum(1 for pattern in bearish_patterns if pattern in p),
        "neutral": sum(1 for pattern in neutral_patterns if pattern in p),
        "volatile": sum(1 for pattern in volatile_patterns if pattern in p)
    }
    
    # Determine outlook based on highest score
    if max(scores.values()) > 0:
        outlook = max(scores, key=scores.get)
        confidence = min(0.8, 0.4 + (scores[outlook] * 0.1))
    
    # Strategy mapping based on outlook
    strategy_mapping = {
        "neutral": "iron_condor",
        "volatile": "straddle", 
        "bearish": "put_credit_spread",
        "bullish": "covered_call"
    }
    strategy_hint = strategy_mapping.get(outlook)
    
    # Symbol detection with expanded list
    underlying = "SPY"  # Default
    symbols = [
        "SPY", "QQQ", "IWM", "DIA", "AAPL", "MSFT", "NVDA", "TSLA", 
        "AMZN", "GOOGL", "META", "NFLX", "AMD", "INTC", "CRM", "UBER"
    ]
    
    for symbol in symbols:
        if symbol.lower() in p:
            underlying = symbol
            break
    
    # Enhanced risk constraints based on equity
    risk_constraints = create_default_risk_constraints(equity)
    
    # Time horizon detection
    time_horizon_days = 30  # Default
    if any(word in p for word in ["weekly", "week", "short"]):
        time_horizon_days = 7
    elif any(word in p for word in ["monthly", "month", "medium"]):
        time_horizon_days = 30
    elif any(word in p for word in ["quarterly", "quarter", "long"]):
        time_horizon_days = 90
    
    risk_constraints.time_horizon_days = time_horizon_days
    
    # Key catalysts detection
    catalysts = []
    catalyst_keywords = {
        "earnings": "earnings announcement",
        "fed": "Federal Reserve meeting",
        "cpi": "CPI data release",
        "jobs": "jobs report",
        "gdp": "GDP data",
        "election": "election event"
    }
    
    for keyword, description in catalyst_keywords.items():
        if keyword in p:
            catalysts.append(description)
    
    return AnalysisPlan(
        intent="Market analysis based on user input",
        thesis=prompt.strip()[:200] + "..." if len(prompt.strip()) > 200 else prompt.strip(),
        underlying=underlying,
        outlook=outlook,
        strategy_hint=strategy_hint,
        risk=risk_constraints,
        confidence=confidence,
        key_catalysts=catalysts,
        key_risks=["Market volatility", "Timing risk", "Liquidity risk"],
        notes="Generated by enhanced heuristic analysis",
        source="heuristic",
        model_version="heuristic_v2.0"
    )

class LLMOrchestrator:
    """Enhanced LLM orchestrator with multiple providers and robust fallbacks"""
    
    def __init__(self, provider: str = "auto", equity: float = 10000.0):
        self.equity = equity
        self.providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(), 
            "ollama": OllamaProvider()
        }
        
        # Determine active provider
        if provider == "auto":
            # Use first available provider
            for name, prov in self.providers.items():
                if prov.is_available():
                    self.active_provider = name
                    break
            else:
                self.active_provider = "heuristic"
        elif provider in self.providers and self.providers[provider].is_available():
            self.active_provider = provider
        else:
            self.active_provider = "heuristic"
        
        logger.info(f"LLM Orchestrator initialized with provider: {self.active_provider}")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        available = [name for name, prov in self.providers.items() if prov.is_available()]
        available.append("heuristic")  # Always available
        return available
    
    def get_provider_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get provider usage statistics"""
        stats = {}
        for name, prov in self.providers.items():
            stats[name] = {
                "available": prov.is_available(),
                "requests": prov.request_count,
                "errors": prov.error_count,
                "last_request": prov.last_request_time,
                "error_rate": prov.error_count / max(prov.request_count, 1)
            }
        return stats
    
    def analyze_intent(self, user_prompt: str, analysis_type: str = "analysis") -> AnalysisPlan:
        """
        Analyze user intent and generate structured trading plan
        
        Args:
            user_prompt: User's trading request/question
            analysis_type: Type of analysis (analysis, risk_assessment, market_outlook)
        """
        if not user_prompt or not user_prompt.strip():
            logger.warning("Empty prompt provided to analyze_intent")
            return _heuristic_analysis("General market analysis", self.equity)
        
        # Use heuristic analysis if no LLM providers available
        if self.active_provider == "heuristic":
            return _heuristic_analysis(user_prompt, self.equity)
        
        # Try LLM analysis with fallback to heuristic
        try:
            return self._llm_analysis(user_prompt, analysis_type)
        except Exception as e:
            logger.error(f"LLM analysis failed, falling back to heuristic: {e}")
            return _heuristic_analysis(user_prompt, self.equity)
    
    def _llm_analysis(self, user_prompt: str, analysis_type: str) -> AnalysisPlan:
        """Perform LLM-based analysis with structured output"""
        
        # Build structured prompt for JSON response
        system_prompt = SYSTEM_PROMPTS.get(analysis_type, SYSTEM_PROMPTS["analysis"])
        
        structured_prompt = f"""
{system_prompt}

Please analyze this trading request and respond with a JSON object containing:
{{
    "intent": "Brief description of trading intent",
    "thesis": "Investment thesis (1-2 sentences)",
    "underlying": "Primary symbol (e.g., SPY, QQQ, AAPL)",
    "outlook": "bullish|bearish|neutral|volatile",
    "confidence": 0.7,
    "strategy_hint": "iron_condor|put_credit_spread|covered_call|straddle|null",
    "risk_pct": 0.02,
    "time_horizon_days": 30,
    "key_catalysts": ["catalyst1", "catalyst2"],
    "key_risks": ["risk1", "risk2"],
    "notes": "Additional analysis notes"
}}

User request: {user_prompt}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": structured_prompt}
        ]
        
        # Try primary provider
        provider = self.providers.get(self.active_provider)
        if provider:
            response = provider.call_llm(messages)
            if response:
                # Try to parse structured response
                parsed = self._parse_llm_response(response, user_prompt)
                if parsed:
                    return parsed
        
        # Fallback to other providers
        for name, prov in self.providers.items():
            if name != self.active_provider and prov.is_available():
                logger.info(f"Trying fallback provider: {name}")
                response = prov.call_llm(messages)
                if response:
                    parsed = self._parse_llm_response(response, user_prompt)
                    if parsed:
                        return parsed
        
        # Final fallback to heuristic
        logger.warning("All LLM providers failed, using heuristic analysis")
        return _heuristic_analysis(user_prompt, self.equity)
    
    def _parse_llm_response(self, response: str, original_prompt: str) -> Optional[AnalysisPlan]:
        """Parse LLM response into AnalysisPlan"""
        try:
            # Extract JSON from response
            data = _extract_json_from_response(response)
            if not data:
                # Try to parse the response as structured text
                return self._parse_text_response(response, original_prompt)
            
            # Build AnalysisPlan from parsed data
            risk_constraints = create_default_risk_constraints(self.equity)
            
            # Update risk constraints from LLM data
            if "risk_pct" in data:
                risk_constraints.max_risk_pct = min(float(data["risk_pct"]), 0.25)  # Cap at 25%
            if "time_horizon_days" in data:
                risk_constraints.time_horizon_days = int(data["time_horizon_days"])
            
            return AnalysisPlan(
                intent=data.get("intent", "LLM analysis"),
                thesis=data.get("thesis", original_prompt[:200]),
                underlying=data.get("underlying", "SPY").upper(),
                outlook=data.get("outlook", "neutral"),
                confidence=min(max(float(data.get("confidence", 0.6)), 0.1), 0.95),
                strategy_hint=data.get("strategy_hint"),
                risk=risk_constraints,
                key_catalysts=data.get("key_catalysts", []),
                key_risks=data.get("key_risks", ["Market risk", "Timing risk"]),
                notes=data.get("notes", "LLM-generated analysis"),
                source=f"llm_{self.active_provider}",
                model_version=f"{self.active_provider}_v1.0"
            )
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None
    
    def _parse_text_response(self, response: str, original_prompt: str) -> Optional[AnalysisPlan]:
        """Parse unstructured text response using pattern matching"""
        try:
            # This is a simplified text parser - can be enhanced
            return _heuristic_analysis(original_prompt + " " + response, self.equity)
        except Exception as e:
            logger.error(f"Failed to parse text response: {e}")
            return None

# Utility functions
def test_llm_providers() -> Dict[str, bool]:
    """Test all LLM providers and return availability status"""
    orchestrator = LLMOrchestrator()
    results = {}
    
    for provider_name in ["openai", "anthropic", "ollama"]:
        try:
            test_orchestrator = LLMOrchestrator(provider=provider_name)
            # Quick test prompt
            result = test_orchestrator.analyze_intent("Test market analysis for SPY")
            results[provider_name] = result is not None and result.underlying == "SPY"
        except Exception as e:
            logger.debug(f"Provider {provider_name} test failed: {e}")
            results[provider_name] = False
    
    results["heuristic"] = True  # Always available
    return results

def get_recommended_provider() -> str:
    """Get recommended LLM provider based on availability and performance"""
    available = test_llm_providers()
    
    # Preference order: OpenAI -> Anthropic -> Ollama -> Heuristic
    preferences = ["openai", "anthropic", "ollama", "heuristic"]
    
    for provider in preferences:
        if available.get(provider, False):
            return provider
    
    return "heuristic"  # Fallback

# Export main classes and functions
__all__ = [
    "LLMOrchestrator", "LLMProvider", "OpenAIProvider", "AnthropicProvider", "OllamaProvider",
    "test_llm_providers", "get_recommended_provider"
]