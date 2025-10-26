# src/ai/json_orchestrator.py
"""
Enhanced AI JSON Orchestrator with Production Features
Multi-provider LLM support with structured JSON responses and fallbacks
"""
from __future__ import annotations
import os
import json
import time
import logging
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any, Tuple, Union
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Import optional dependencies
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    anthropic = None
    ANTHROPIC_AVAILABLE = False

@dataclass
class AnalysisPlan:
    """Enhanced analysis plan with validation and metadata"""
    symbol: str
    outlook: str        # "bullish"/"bearish"/"neutral"/"volatile"
    target_days: int
    risk_budget: float  # fraction of equity (e.g. 0.02)
    notes: List[str]
    confidence: float = 0.7
    timestamp: Optional[datetime] = None
    source: str = "ai_analysis"
    
    def __post_init__(self):
        """Validate and enhance analysis plan"""
        # Validate outlook
        valid_outlooks = ["bullish", "bearish", "neutral", "volatile", "unknown"]
        if self.outlook not in valid_outlooks:
            logger.warning(f"Invalid outlook: {self.outlook}, defaulting to 'neutral'")
            self.outlook = "neutral"
        
        # Validate and constrain values
        self.target_days = max(1, min(365, self.target_days))
        self.risk_budget = max(0.001, min(0.2, self.risk_budget))  # 0.1% to 20%
        self.confidence = max(0.0, min(1.0, self.confidence))
        
        # Set timestamp if not provided
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
        
        # Ensure notes is a list
        if not isinstance(self.notes, list):
            self.notes = [str(self.notes)] if self.notes else []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        if self.timestamp:
            result['timestamp'] = self.timestamp.isoformat()
        return result
    
    def is_high_confidence(self) -> bool:
        """Check if analysis has high confidence"""
        return self.confidence >= 0.8
    
    def risk_level(self) -> str:
        """Determine risk level based on budget"""
        if self.risk_budget <= 0.01:
            return "CONSERVATIVE"
        elif self.risk_budget <= 0.03:
            return "MODERATE"
        elif self.risk_budget <= 0.05:
            return "AGGRESSIVE"
        else:
            return "VERY_AGGRESSIVE"

@dataclass
class TradeIdea:
    """Enhanced trade idea with comprehensive parameters"""
    strategy: str               # "iron_condor", "put_credit_spread", etc.
    expiry: Optional[str] = None
    target_delta: Optional[float] = None
    wings_width: Optional[float] = None
    max_loss_dollars: Optional[float] = None
    comments: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validate and enhance trade idea"""
        # Validate strategy
        valid_strategies = [
            "iron_condor", "put_credit_spread", "call_credit_spread",
            "protective_put", "covered_call", "long_call", "long_put",
            "straddle", "strangle", "butterfly", "calendar_spread"
        ]
        
        if self.strategy not in valid_strategies:
            logger.warning(f"Unknown strategy: {self.strategy}")
        
        # Validate delta if provided
        if self.target_delta is not None:
            self.target_delta = max(0.05, min(0.95, abs(self.target_delta)))
        
        # Validate wings width
        if self.wings_width is not None:
            self.wings_width = max(1.0, self.wings_width)
        
        # Ensure comments is a list
        if self.comments is None:
            self.comments = []
        elif not isinstance(self.comments, list):
            self.comments = [str(self.comments)]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
    
    def complexity_score(self) -> int:
        """Calculate strategy complexity (1-5 scale)"""
        complexity_map = {
            "long_call": 1,
            "long_put": 1,
            "covered_call": 2,
            "protective_put": 2,
            "put_credit_spread": 2,
            "call_credit_spread": 2,
            "straddle": 3,
            "strangle": 3,
            "iron_condor": 4,
            "butterfly": 4,
            "calendar_spread": 5
        }
        return complexity_map.get(self.strategy, 3)

# Enhanced system prompts for different providers
OPENAI_SYSTEM_PROMPT = """You are an expert options strategist. Always respond with STRICT JSON format only.

Your response must match this exact schema:
{
 "symbol": "string (underlying ticker)",
 "outlook": "bullish|bearish|neutral|volatile",
 "target_days": "integer (1-365)",
 "risk_budget": "float (0.001-0.2)",
 "notes": ["string", ...],
 "trade": {
   "strategy": "iron_condor|put_credit_spread|call_credit_spread|protective_put|covered_call|long_call|long_put|straddle|strangle",
   "expiry": "YYYY-MM-DD or null",
   "target_delta": "float (0.05-0.95) or null",
   "wings_width": "float (strike width) or null",
   "max_loss_dollars": "float or null",
   "comments": ["string", ...]
 }
}

Respond ONLY with valid JSON. No explanations, no markdown, just JSON."""

ANTHROPIC_SYSTEM_PROMPT = """You are a professional options trading strategist. Respond only in JSON format.

Required JSON structure:
{
 "symbol": "<ticker>",
 "outlook": "<bullish/bearish/neutral/volatile>",
 "target_days": <days_to_expiry>,
 "risk_budget": <risk_as_decimal>,
 "notes": ["<analysis_note>"],
 "trade": {
   "strategy": "<strategy_name>",
   "expiry": "<YYYY-MM-DD>",
   "target_delta": <target_delta>,
   "wings_width": <width_in_strikes>,
   "max_loss_dollars": <max_loss>,
   "comments": ["<comment>"]
 }
}

Return only valid JSON."""

def _create_mock_response(user_text: str) -> Dict[str, Any]:
    """
    Create intelligent mock response based on user input
    Enhanced heuristics for better fallback analysis
    """
    try:
        text_lower = user_text.lower()
        
        # Extract symbol (enhanced detection)
        symbols = ["spy", "qqq", "aapl", "msft", "nvda", "tsla", "amzn", "googl", "meta", "nflx"]
        symbol = "SPY"  # default
        for sym in symbols:
            if sym in text_lower:
                symbol = sym.upper()
                break
        
        # Determine outlook with more sophisticated logic
        bullish_words = ["bull", "up", "rise", "call", "long", "buy", "optimistic", "positive"]
        bearish_words = ["bear", "down", "fall", "put", "short", "sell", "pessimistic", "negative"]
        neutral_words = ["flat", "neutral", "sideways", "range", "income", "theta"]
        volatile_words = ["volatile", "movement", "swing", "straddle", "strangle", "big move"]
        
        outlook_scores = {
            "bullish": sum(1 for word in bullish_words if word in text_lower),
            "bearish": sum(1 for word in bearish_words if word in text_lower),
            "neutral": sum(1 for word in neutral_words if word in text_lower),
            "volatile": sum(1 for word in volatile_words if word in text_lower)
        }
        
        outlook = max(outlook_scores, key=outlook_scores.get)
        confidence = min(0.9, max(0.5, outlook_scores[outlook] * 0.2 + 0.5))
        
        # Determine strategy based on outlook and keywords
        strategy_map = {
            "bullish": {
                "spread": "call_credit_spread",
                "covered": "covered_call", 
                "default": "long_call"
            },
            "bearish": {
                "spread": "put_credit_spread",
                "protective": "protective_put",
                "default": "long_put"
            },
            "neutral": {
                "condor": "iron_condor",
                "spread": "put_credit_spread",
                "default": "iron_condor"
            },
            "volatile": {
                "straddle": "straddle",
                "strangle": "strangle",
                "default": "straddle"
            }
        }
        
        strategy = "iron_condor"  # default
        for keyword, strat in strategy_map[outlook].items():
            if keyword in text_lower:
                strategy = strat
                break
        else:
            strategy = strategy_map[outlook]["default"]
        
        # Determine time frame
        if "day" in text_lower or "daily" in text_lower:
            target_days = 7
        elif "week" in text_lower or "weekly" in text_lower:
            target_days = 14
        elif "month" in text_lower or "monthly" in text_lower:
            target_days = 30
        else:
            target_days = 21  # default ~3 weeks
        
        # Risk budget based on language
        if any(word in text_lower for word in ["conservative", "safe", "small"]):
            risk_budget = 0.01
        elif any(word in text_lower for word in ["aggressive", "large", "big"]):
            risk_budget = 0.05
        else:
            risk_budget = 0.02
        
        # Generate expiry date
        expiry_date = datetime.utcnow() + timedelta(days=target_days)
        # Adjust to next Friday (typical options expiry)
        days_to_friday = (4 - expiry_date.weekday()) % 7
        if days_to_friday == 0 and expiry_date.weekday() != 4:  # If not Friday, get next Friday
            days_to_friday = 7
        expiry_date += timedelta(days=days_to_friday)
        
        return {
            "symbol": symbol,
            "outlook": outlook,
            "target_days": target_days,
            "risk_budget": risk_budget,
            "notes": [
                f"Mock analysis with {confidence:.1%} confidence",
                f"Detected {outlook} outlook for {symbol}",
                "Using fallback heuristic analysis"
            ],
            "trade": {
                "strategy": strategy,
                "expiry": expiry_date.strftime("%Y-%m-%d"),
                "target_delta": 0.2 if outlook in ["bullish", "bearish"] else 0.15,
                "wings_width": 5.0,
                "max_loss_dollars": risk_budget * 50000,  # Assume $50k portfolio
                "comments": [
                    f"Strategy selected based on {outlook} outlook",
                    "Generated using enhanced heuristics",
                    f"Target delta: {0.2 if outlook in ['bullish', 'bearish'] else 0.15}"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error creating mock response: {e}")
        # Ultra-safe fallback
        return {
            "symbol": "SPY",
            "outlook": "neutral",
            "target_days": 21,
            "risk_budget": 0.02,
            "notes": ["Fallback analysis due to processing error"],
            "trade": {
                "strategy": "iron_condor",
                "expiry": None,
                "target_delta": 0.15,
                "wings_width": 5.0,
                "max_loss_dollars": 1000.0,
                "comments": ["Safe default strategy"]
            }
        }

class EnhancedJSONOrchestrator:
    """Enhanced orchestrator with multiple LLM providers and fallbacks"""
    
    def __init__(self, preferred_provider: str = "auto"):
        self.preferred_provider = preferred_provider
        self.available_providers = self._check_available_providers()
        self.call_count = 0
        self.last_call_time = None
        
        logger.info(f"Initialized with providers: {self.available_providers}")
    
    def _check_available_providers(self) -> List[str]:
        """Check which LLM providers are available"""
        providers = []
        
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            providers.append("openai")
        
        if ANTHROPIC_AVAILABLE and os.getenv("ANTHROPIC_API_KEY"):
            providers.append("anthropic")
        
        providers.append("mock")  # Always available as fallback
        
        return providers
    
    def _call_openai(self, user_text: str) -> Dict[str, Any]:
        """Call OpenAI API with error handling"""
        try:
            if not OPENAI_AVAILABLE:
                raise ValueError("OpenAI not available")
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found")
            
            client = openai.OpenAI(api_key=api_key)
            
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": OPENAI_SYSTEM_PROMPT},
                    {"role": "user", "content": user_text}
                ],
                temperature=0.1,
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            raw_content = response.choices[0].message.content
            if not raw_content:
                raise ValueError("Empty response from OpenAI")
            
            # Parse and validate JSON
            data = json.loads(raw_content)
            
            # Add metadata
            data["_provider"] = "openai"
            data["_model"] = response.model
            
            return data
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def _call_anthropic(self, user_text: str) -> Dict[str, Any]:
        """Call Anthropic API with error handling"""
        try:
            if not ANTHROPIC_AVAILABLE:
                raise ValueError("Anthropic not available")
            
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("Anthropic API key not found")
            
            client = anthropic.Anthropic(api_key=api_key)
            
            response = client.messages.create(
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
                max_tokens=1000,
                temperature=0.1,
                system=ANTHROPIC_SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": user_text}
                ]
            )
            
            raw_content = response.content[0].text if response.content else ""
            if not raw_content:
                raise ValueError("Empty response from Anthropic")
            
            # Parse JSON (Anthropic sometimes wraps in markdown)
            if "```json" in raw_content:
                start = raw_content.find("```json") + 7
                end = raw_content.find("```", start)
                raw_content = raw_content[start:end].strip()
            
            data = json.loads(raw_content)
            
            # Add metadata
            data["_provider"] = "anthropic"
            data["_model"] = response.model
            
            return data
            
        except Exception as e:
            logger.error(f"Anthropic API call failed: {e}")
            raise
    
    def analyze_request(self, user_text: str) -> Dict[str, Any]:
        """
        Analyze user request with provider fallback
        
        Args:
            user_text: User's trading request
        
        Returns:
            Structured analysis dictionary
        """
        if not user_text or not user_text.strip():
            raise ValueError("Empty user request")
        
        self.call_count += 1
        self.last_call_time = datetime.utcnow()
        
        # Determine provider order
        if self.preferred_provider == "auto":
            provider_order = self.available_providers
        elif self.preferred_provider in self.available_providers:
            provider_order = [self.preferred_provider] + [p for p in self.available_providers if p != self.preferred_provider]
        else:
            provider_order = self.available_providers
        
        last_error = None
        
        for provider in provider_order:
            try:
                logger.debug(f"Trying provider: {provider}")
                
                if provider == "openai":
                    result = self._call_openai(user_text)
                elif provider == "anthropic":
                    result = self._call_anthropic(user_text)
                elif provider == "mock":
                    result = _create_mock_response(user_text)
                    result["_provider"] = "mock"
                else:
                    continue
                
                # Validate result has required fields
                required_fields = ["symbol", "outlook", "target_days", "risk_budget", "trade"]
                if all(field in result for field in required_fields):
                    logger.info(f"Successfully analyzed request using {provider}")
                    return result
                else:
                    raise ValueError(f"Missing required fields in response: {required_fields}")
                
            except Exception as e:
                last_error = e
                logger.warning(f"Provider {provider} failed: {e}")
                continue
        
        # All providers failed
        logger.error("All providers failed, using emergency fallback")
        fallback = _create_mock_response(user_text)
        fallback["_provider"] = "emergency_fallback"
        fallback["_error"] = str(last_error) if last_error else "Unknown error"
        return fallback

# Global orchestrator instance
_orchestrator = None

def get_orchestrator() -> EnhancedJSONOrchestrator:
    """Get global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = EnhancedJSONOrchestrator()
    return _orchestrator

def analyze_request_to_json(user_text: str) -> Tuple[AnalysisPlan, TradeIdea]:
    """
    Enhanced analysis function with comprehensive error handling
    
    Args:
        user_text: User's trading request
    
    Returns:
        Tuple of (AnalysisPlan, TradeIdea)
    """
    try:
        orchestrator = get_orchestrator()
        data = orchestrator.analyze_request(user_text)
        
        # Create AnalysisPlan
        ap = AnalysisPlan(
            symbol=data.get("symbol", "SPY"),
            outlook=data.get("outlook", "neutral"),
            target_days=int(data.get("target_days", 21)),
            risk_budget=float(data.get("risk_budget", 0.02)),
            notes=list(data.get("notes", [])),
            confidence=data.get("confidence", 0.7),
            source=data.get("_provider", "unknown")
        )
        
        # Create TradeIdea
        trade_data = data.get("trade", {})
        ti = TradeIdea(
            strategy=trade_data.get("strategy", "iron_condor"),
            expiry=trade_data.get("expiry"),
            target_delta=trade_data.get("target_delta"),
            wings_width=trade_data.get("wings_width"),
            max_loss_dollars=trade_data.get("max_loss_dollars"),
            comments=trade_data.get("comments", [])
        )
        
        logger.info(f"Analysis complete: {ap.symbol} {ap.outlook} -> {ti.strategy}")
        return ap, ti
        
    except Exception as e:
        logger.error(f"Error in analyze_request_to_json: {e}")
        
        # Emergency fallback
        ap = AnalysisPlan(
            symbol="SPY",
            outlook="neutral", 
            target_days=21,
            risk_budget=0.02,
            notes=[f"Emergency fallback due to error: {str(e)}"],
            confidence=0.5,
            source="emergency"
        )
        
        ti = TradeIdea(
            strategy="iron_condor",
            expiry=None,
            target_delta=0.15,
            wings_width=5.0,
            max_loss_dollars=1000.0,
            comments=["Safe default strategy"]
        )
        
        return ap, ti

def test_providers() -> Dict[str, Any]:
    """Test all available providers"""
    orchestrator = get_orchestrator()
    test_request = "I'm bullish on SPY and want a low-risk strategy"
    
    results = {}
    
    for provider in orchestrator.available_providers:
        try:
            # Temporarily set preferred provider
            old_preferred = orchestrator.preferred_provider
            orchestrator.preferred_provider = provider
            
            start_time = time.time()
            result = orchestrator.analyze_request(test_request)
            end_time = time.time()
            
            results[provider] = {
                "status": "success",
                "response_time": round(end_time - start_time, 2),
                "symbol": result.get("symbol"),
                "strategy": result.get("trade", {}).get("strategy"),
                "provider_used": result.get("_provider")
            }
            
            # Restore preferred provider
            orchestrator.preferred_provider = old_preferred
            
        except Exception as e:
            results[provider] = {
                "status": "failed",
                "error": str(e)
            }
    
    return results

# Legacy compatibility
def _mock_llm(prompt: str) -> dict:
    """Legacy mock function for compatibility"""
    return _create_mock_response(prompt)

# Export main components
__all__ = [
    "AnalysisPlan",
    "TradeIdea", 
    "EnhancedJSONOrchestrator",
    "analyze_request_to_json",
    "get_orchestrator",
    "test_providers"
]