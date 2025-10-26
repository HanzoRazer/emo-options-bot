# agents/intent_router.py
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Intent:
    kind: str               # e.g. "build_strategy", "diagnose", "status"
    symbol: Optional[str]   # e.g. "SPY"
    strategy: Optional[str] # e.g. "iron_condor"
    params: Dict[str, Any]  # free-form, e.g. {"dte": 7, "wings": 5}

# VERY BASIC keyword router (LLM would live here later)
def parse(text: str) -> Intent:
    t = text.lower()
    symbol = None
    strategy = None
    params: Dict[str, Any] = {}

    # symbols: look for common tickers (extend as needed)
    for s in ["spy", "qqq", "iwm", "dia", "aapl", "msft", "tsla", "nvda", "amzn", "googl"]:
        if f" {s} " in f" {t} " or t.startswith(s + " ") or t.endswith(" " + s):
            symbol = s.upper()
            break

    # strategies
    if "iron condor" in t or "condor" in t:
        strategy = "iron_condor"
    elif "put credit" in t or "bull put" in t:
        strategy = "put_credit_spread"
    elif "call credit" in t or "bear call" in t:
        strategy = "call_credit_spread"
    elif "covered call" in t:
        strategy = "covered_call"
    elif "protective put" in t:
        strategy = "protective_put"
    elif "long straddle" in t or "straddle" in t:
        strategy = "long_straddle"

    # params (toy parsing)
    if "7 dte" in t or "in a week" in t or "weekly" in t:
        params["dte"] = 7
    elif "14 dte" in t or "two weeks" in t or "2 weeks" in t:
        params["dte"] = 14
    elif "30 dte" in t or "monthly" in t or "month" in t:
        params["dte"] = 30
    
    if "wings 5" in t or "5 point" in t:
        params["wings"] = 5
    elif "wings 10" in t or "10 point" in t:
        params["wings"] = 10
    
    # risk level
    if "low risk" in t or "conservative" in t:
        params["risk_level"] = "low"
    elif "high risk" in t or "aggressive" in t:
        params["risk_level"] = "high"
    else:
        params["risk_level"] = "moderate"

    # intent classification
    if strategy:
        kind = "build_strategy"
    elif "status" in t or "how are you" in t or "what's up" in t:
        kind = "status"
    elif "diagnose" in t or "check" in t or "analyze" in t:
        kind = "diagnose"
    else:
        kind = "unknown"

    return Intent(kind=kind, symbol=symbol, strategy=strategy, params=params)