# agents/enhanced_intent_router.py
"""
Enhanced Intent Router with better parsing, confidence scoring, and extensibility.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple
import re
from enum import Enum

class IntentKind(Enum):
    """Enumeration of supported intent kinds."""
    BUILD_STRATEGY = "build_strategy"
    DIAGNOSE = "diagnose"
    STATUS = "status"
    HELP = "help"
    MODIFY = "modify"
    CANCEL = "cancel"
    UNKNOWN = "unknown"

class RiskLevel(Enum):
    """Enumeration of risk levels."""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"

@dataclass
class Intent:
    """Enhanced intent with confidence scoring and metadata."""
    kind: IntentKind
    symbol: Optional[str] = None
    strategy: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0  # 0.0 to 1.0
    parsed_tokens: List[str] = field(default_factory=list)
    ambiguities: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

class EnhancedIntentRouter:
    """Enhanced intent router with better parsing and confidence scoring."""
    
    def __init__(self):
        """Initialize the enhanced intent router."""
        self.symbols = {
            # Major ETFs
            "spy": "SPY", "qqq": "QQQ", "iwm": "IWM", "dia": "DIA",
            "xlf": "XLF", "xle": "XLE", "xlu": "XLU", "xlk": "XLK",
            "gld": "GLD", "slv": "SLV", "tlt": "TLT", "hya": "HYA",
            
            # Major Stocks
            "aapl": "AAPL", "msft": "MSFT", "googl": "GOOGL", "goog": "GOOGL",
            "amzn": "AMZN", "tsla": "TSLA", "nvda": "NVDA", "meta": "META",
            "nflx": "NFLX", "baba": "BABA", "crm": "CRM", "orcl": "ORCL",
            "amd": "AMD", "intc": "INTC", "pypl": "PYPL", "adbe": "ADBE"
        }
        
        self.strategy_patterns = {
            "iron_condor": [
                r"iron\s+condor", r"condor", r"ic\b", r"four\s+leg",
                r"short\s+strangle.*protection", r"neutral.*income"
            ],
            "put_credit_spread": [
                r"put\s+credit\s+spread", r"bull\s+put\s+spread", r"pcs\b",
                r"sell\s+put.*buy\s+put", r"bullish.*credit"
            ],
            "call_credit_spread": [
                r"call\s+credit\s+spread", r"bear\s+call\s+spread", r"ccs\b",
                r"sell\s+call.*buy\s+call", r"bearish.*credit"
            ],
            "covered_call": [
                r"covered\s+call", r"buy\s+write", r"cc\b",
                r"sell\s+call.*own.*stock", r"income.*stock"
            ],
            "protective_put": [
                r"protective\s+put", r"married\s+put", r"pp\b",
                r"buy\s+put.*own.*stock", r"hedge.*downside"
            ],
            "long_straddle": [
                r"long\s+straddle", r"straddle", r"buy\s+straddle",
                r"volatility\s+play", r"earnings\s+play"
            ],
            "short_straddle": [
                r"short\s+straddle", r"sell\s+straddle",
                r"collect\s+premium.*both"
            ],
            "long_strangle": [
                r"long\s+strangle", r"strangle", r"buy\s+strangle"
            ],
            "butterfly": [
                r"butterfly", r"fly\b", r"three\s+strike"
            ]
        }
        
        self.intent_patterns = {
            IntentKind.BUILD_STRATEGY: [
                r"build", r"create", r"construct", r"make", r"set\s+up",
                r"establish", r"execute", r"enter", r"open"
            ],
            IntentKind.DIAGNOSE: [
                r"diagnose", r"analyze", r"check", r"review", r"assess",
                r"evaluate", r"examine", r"what.*going\s+on"
            ],
            IntentKind.STATUS: [
                r"status", r"how.*doing", r"what.*up", r"health",
                r"running", r"working", r"online"
            ],
            IntentKind.HELP: [
                r"help", r"assist", r"guide", r"how\s+to", r"explain",
                r"what\s+can", r"commands", r"usage"
            ],
            IntentKind.MODIFY: [
                r"modify", r"change", r"adjust", r"update", r"edit",
                r"alter", r"revise"
            ],
            IntentKind.CANCEL: [
                r"cancel", r"abort", r"stop", r"terminate", r"quit",
                r"exit", r"close"
            ]
        }
        
        self.risk_patterns = {
            RiskLevel.LOW: [
                r"low\s+risk", r"conservative", r"safe", r"cautious",
                r"minimal\s+risk", r"protective"
            ],
            RiskLevel.MODERATE: [
                r"moderate\s+risk", r"medium\s+risk", r"balanced",
                r"normal", r"standard", r"average"
            ],
            RiskLevel.HIGH: [
                r"high\s+risk", r"aggressive", r"speculative",
                r"maximum\s+risk", r"risky"
            ]
        }
        
        self.dte_patterns = {
            7: [r"7\s*dte", r"one\s+week", r"1\s+week", r"weekly", r"week"],
            14: [r"14\s*dte", r"two\s+week", r"2\s+week", r"bi.*weekly"],
            30: [r"30\s*dte", r"one\s+month", r"1\s+month", r"monthly", r"month"],
            45: [r"45\s*dte", r"six\s+week", r"6\s+week"],
            60: [r"60\s*dte", r"two\s+month", r"2\s+month"]
        }
        
        self.wings_patterns = {
            5: [r"5\s*point", r"5\s*dollar", r"wings?\s*5", r"narrow"],
            10: [r"10\s*point", r"10\s*dollar", r"wings?\s*10", r"medium"],
            15: [r"15\s*point", r"15\s*dollar", r"wings?\s*15"],
            20: [r"20\s*point", r"20\s*dollar", r"wings?\s*20", r"wide"]
        }
    
    def parse(self, text: str) -> Intent:
        """Enhanced parsing with confidence scoring."""
        if not text or not text.strip():
            return Intent(
                kind=IntentKind.UNKNOWN,
                confidence=0.0,
                suggestions=["Please provide a command"]
            )
        
        text_clean = text.lower().strip()
        tokens = re.findall(r'\b\w+\b', text_clean)
        
        # Parse intent kind
        intent_kind, intent_confidence = self._parse_intent_kind(text_clean)
        
        # Parse symbol
        symbol, symbol_confidence = self._parse_symbol(text_clean, tokens)
        
        # Parse strategy
        strategy, strategy_confidence = self._parse_strategy(text_clean)
        
        # Parse parameters
        params = self._parse_parameters(text_clean)
        
        # Calculate overall confidence
        confidence_scores = [intent_confidence]
        if symbol:
            confidence_scores.append(symbol_confidence)
        if strategy:
            confidence_scores.append(strategy_confidence)
        
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Detect ambiguities and generate suggestions
        ambiguities = self._detect_ambiguities(text_clean, symbol, strategy)
        suggestions = self._generate_suggestions(intent_kind, symbol, strategy, ambiguities)
        
        return Intent(
            kind=intent_kind,
            symbol=symbol,
            strategy=strategy,
            params=params,
            confidence=overall_confidence,
            parsed_tokens=tokens,
            ambiguities=ambiguities,
            suggestions=suggestions
        )
    
    def _parse_intent_kind(self, text: str) -> Tuple[IntentKind, float]:
        """Parse the intent kind with confidence."""
        best_kind = IntentKind.UNKNOWN
        best_score = 0.0
        
        for kind, patterns in self.intent_patterns.items():
            score = 0.0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matches += 1
                    # Weight by pattern strength
                    if len(pattern) > 10:  # More specific patterns get higher weight
                        score += 0.8
                    else:
                        score += 0.6
            
            if matches > 0:
                score = score / len(patterns)  # Normalize by number of patterns
                if score > best_score:
                    best_score = score
                    best_kind = kind
        
        # Special case: if we detect strategy keywords, likely BUILD_STRATEGY
        if best_kind == IntentKind.UNKNOWN:
            for strategy_patterns in self.strategy_patterns.values():
                for pattern in strategy_patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        return IntentKind.BUILD_STRATEGY, 0.7
        
        return best_kind, min(best_score, 1.0)
    
    def _parse_symbol(self, text: str, tokens: List[str]) -> Tuple[Optional[str], float]:
        """Parse symbol with confidence scoring."""
        # Direct token match
        for token in tokens:
            if token in self.symbols:
                return self.symbols[token], 1.0
        
        # Pattern-based matching for symbols in context
        symbol_patterns = [
            (r'\bon\s+(\w+)', 0.9),  # "on SPY"
            (r'(\w+)\s+options?', 0.8),  # "SPY options"
            (r'trade\s+(\w+)', 0.8),  # "trade SPY"
            (r'in\s+(\w+)', 0.7),  # "in SPY"
        ]
        
        for pattern, confidence in symbol_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                symbol_candidate = match.group(1).lower()
                if symbol_candidate in self.symbols:
                    return self.symbols[symbol_candidate], confidence
        
        return None, 0.0
    
    def _parse_strategy(self, text: str) -> Tuple[Optional[str], float]:
        """Parse strategy with confidence scoring."""
        best_strategy = None
        best_score = 0.0
        
        for strategy, patterns in self.strategy_patterns.items():
            score = 0.0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matches += 1
                    # Longer patterns are more specific
                    score += len(pattern) / 20.0
            
            if matches > 0:
                score = min(score / len(patterns), 1.0)
                if score > best_score:
                    best_score = score
                    best_strategy = strategy
        
        return best_strategy, best_score
    
    def _parse_parameters(self, text: str) -> Dict[str, Any]:
        """Parse strategy parameters."""
        params = {}
        
        # Parse risk level
        for risk_level, patterns in self.risk_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    params["risk_level"] = risk_level.value
                    break
            if "risk_level" in params:
                break
        
        # Default risk level if not specified
        if "risk_level" not in params:
            params["risk_level"] = RiskLevel.MODERATE.value
        
        # Parse DTE
        for dte, patterns in self.dte_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    params["dte"] = dte
                    break
            if "dte" in params:
                break
        
        # Default DTE if not specified
        if "dte" not in params:
            params["dte"] = 30  # Default to monthly
        
        # Parse wings
        for wings, patterns in self.wings_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    params["wings"] = wings
                    break
            if "wings" in params:
                break
        
        # Default wings if not specified
        if "wings" not in params:
            params["wings"] = 5  # Default to 5-point wings
        
        # Parse quantity/contracts
        quantity_match = re.search(r'(\d+)\s*contract', text, re.IGNORECASE)
        if quantity_match:
            params["contracts"] = int(quantity_match.group(1))
        else:
            params["contracts"] = 1  # Default to 1 contract
        
        # Parse specific strikes if mentioned
        strike_pattern = r'(\d+(?:\.\d+)?)\s*strike'
        strikes = re.findall(strike_pattern, text, re.IGNORECASE)
        if strikes:
            params["strikes"] = [float(s) for s in strikes]
        
        return params
    
    def _detect_ambiguities(self, text: str, symbol: Optional[str], strategy: Optional[str]) -> List[str]:
        """Detect potential ambiguities in the parsed command."""
        ambiguities = []
        
        # Multiple symbols detected
        symbol_count = sum(1 for token in re.findall(r'\b\w+\b', text) if token.lower() in self.symbols)
        if symbol_count > 1:
            ambiguities.append("Multiple symbols detected - using first match")
        
        # Multiple strategies detected
        strategy_matches = 0
        for patterns in self.strategy_patterns.values():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    strategy_matches += 1
                    break
        
        if strategy_matches > 1:
            ambiguities.append("Multiple strategies detected - using best match")
        
        # Conflicting risk levels
        risk_matches = sum(
            1 for patterns in self.risk_patterns.values()
            for pattern in patterns
            if re.search(pattern, text, re.IGNORECASE)
        )
        
        if risk_matches > 1:
            ambiguities.append("Conflicting risk levels - using first match")
        
        return ambiguities
    
    def _generate_suggestions(
        self, 
        intent_kind: IntentKind, 
        symbol: Optional[str], 
        strategy: Optional[str],
        ambiguities: List[str]
    ) -> List[str]:
        """Generate helpful suggestions for the user."""
        suggestions = []
        
        if intent_kind == IntentKind.BUILD_STRATEGY:
            if not symbol:
                suggestions.append("Consider specifying a symbol (e.g., 'on SPY')")
            if not strategy:
                suggestions.append("Consider specifying a strategy (e.g., 'iron condor')")
        
        elif intent_kind == IntentKind.UNKNOWN:
            suggestions.extend([
                "Try: 'Build an iron condor on SPY'",
                "Try: 'Check system status'", 
                "Try: 'Help' for available commands"
            ])
        
        if ambiguities:
            suggestions.append("Be more specific to avoid ambiguities")
        
        return suggestions

# Enhanced parsing function for backward compatibility
def parse(text: str) -> Intent:
    """Enhanced parsing function (backward compatible)."""
    router = EnhancedIntentRouter()
    return router.parse(text)

# Create global router instance
_global_router = EnhancedIntentRouter()

def parse_enhanced(text: str) -> Intent:
    """Parse with enhanced features."""
    return _global_router.parse(text)