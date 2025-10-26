#!/usr/bin/env python3
"""
LLM Trade Plan Generator
Converts natural language trading descriptions into structured JSON plans
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import os

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Try to import our modules, fall back to mock implementations
try:
    from ai.json_orchestrator import EnhancedJSONOrchestrator
    HAS_AI_MODULE = True
except ImportError:
    print("Warning: AI module not available, using mock analysis")
    HAS_AI_MODULE = False

try:
    from risk.math import Leg, iron_condor_risk, vertical_spread_risk
    HAS_RISK_MODULE = True
except ImportError:
    print("Warning: Risk module not available, using basic validation")
    HAS_RISK_MODULE = False

# Mock implementations for fallback
class MockLeg:
    def __init__(self, strike, option_type, action, quantity, premium):
        self.strike = strike
        self.option_type = option_type
        self.action = action
        self.quantity = quantity
        self.premium = premium

class MockRiskProfile:
    def __init__(self, max_loss, max_profit, breakeven_lower=0, breakeven_upper=0):
        self.max_loss = max_loss
        self.max_profit = max_profit
        self.breakeven_lower = breakeven_lower
        self.breakeven_upper = breakeven_upper

def mock_iron_condor_risk(legs):
    """Mock risk calculation for iron condor"""
    return MockRiskProfile(max_loss=500, max_profit=100, breakeven_lower=440, breakeven_upper=460)

def parse_args():
    parser = argparse.ArgumentParser(description="Generate trade plans from natural language")
    parser.add_argument("--prompt", required=True, help="Natural language trading description")
    parser.add_argument("--symbol", default="SPY", help="Trading symbol (default: SPY)")
    parser.add_argument("--output", default="ops/staged_orders/PLAN.json", help="Output file path")
    parser.add_argument("--expiration-days", type=int, default=45, help="Days to expiration (default: 45)")
    parser.add_argument("--max-risk", type=float, default=1000, help="Maximum risk amount (default: 1000)")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without saving")
    return parser.parse_args()

def generate_expiration_date(days_out: int) -> str:
    """Generate option expiration date"""
    target_date = datetime.now() + timedelta(days=days_out)
    # Find next Friday (option expiration day)
    days_ahead = 4 - target_date.weekday()  # Friday is weekday 4
    if days_ahead <= 0:  # Target date is Friday or after
        days_ahead += 7
    expiration = target_date + timedelta(days=days_ahead)
    return expiration.strftime("%Y-%m-%d")

def create_iron_condor_plan(symbol: str, expiration: str, max_risk: float, spot_price: float = None) -> dict:
    """Create an iron condor trade plan"""
    if spot_price is None:
        # Mock spot price for demonstration
        spot_price = 450.0 if symbol == "SPY" else 100.0
    
    # Iron condor strikes (conservative)
    put_sell_strike = spot_price * 0.95  # 5% OTM
    put_buy_strike = put_sell_strike - 5  # $5 spread
    call_sell_strike = spot_price * 1.05  # 5% OTM
    call_buy_strike = call_sell_strike + 5  # $5 spread
    
    plan = {
        "strategy_type": "iron_condor",
        "symbol": symbol,
        "expiration": expiration,
        "spot_price": spot_price,
        "legs": [
            {
                "action": "sell",
                "instrument": "put",
                "strike": round(put_sell_strike),
                "quantity": 1
            },
            {
                "action": "buy", 
                "instrument": "put",
                "strike": round(put_buy_strike),
                "quantity": 1
            },
            {
                "action": "sell",
                "instrument": "call", 
                "strike": round(call_sell_strike),
                "quantity": 1
            },
            {
                "action": "buy",
                "instrument": "call",
                "strike": round(call_buy_strike),
                "quantity": 1
            }
        ],
        "risk_constraints": {
            "max_loss": max_risk,
            "max_trade_risk_pct": 0.02,
            "max_position_size": max_risk * 10
        },
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "generator": "llm_trade_plan.py",
            "prompt": f"Iron condor on {symbol}",
            "status": "draft"
        },
        "notes": f"Generated iron condor plan for {symbol}"
    }
    
    return plan

def create_vertical_spread_plan(symbol: str, expiration: str, max_risk: float, direction: str = "bullish") -> dict:
    """Create a vertical spread trade plan"""
    spot_price = 450.0 if symbol == "SPY" else 100.0
    
    if direction == "bullish":
        # Bull put spread
        sell_strike = spot_price * 0.95
        buy_strike = sell_strike - 5
        instrument = "put"
    else:
        # Bear call spread  
        sell_strike = spot_price * 1.05
        buy_strike = sell_strike + 5
        instrument = "call"
    
    plan = {
        "strategy_type": f"{direction}_vertical_spread",
        "symbol": symbol,
        "expiration": expiration,
        "spot_price": spot_price,
        "legs": [
            {
                "action": "sell",
                "instrument": instrument,
                "strike": round(sell_strike),
                "quantity": 1
            },
            {
                "action": "buy",
                "instrument": instrument, 
                "strike": round(buy_strike),
                "quantity": 1
            }
        ],
        "risk_constraints": {
            "max_loss": max_risk,
            "max_trade_risk_pct": 0.02
        },
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "generator": "llm_trade_plan.py",
            "status": "draft"
        },
        "notes": f"Generated {direction} vertical spread for {symbol}"
    }
    
    return plan

def analyze_prompt_with_llm(prompt: str, symbol: str) -> dict:
    """Use LLM to analyze the prompt and suggest strategy"""
    if not HAS_AI_MODULE:
        # Mock analysis when AI module not available
        prompt_lower = prompt.lower()
        if "iron condor" in prompt_lower:
            return {"strategy": "iron_condor", "outlook": "neutral", "confidence": 75, "source": "mock"}
        elif "bull" in prompt_lower:
            return {"strategy": "bullish_vertical_spread", "outlook": "bullish", "confidence": 70, "source": "mock"}
        elif "bear" in prompt_lower:
            return {"strategy": "bearish_vertical_spread", "outlook": "bearish", "confidence": 70, "source": "mock"}
        else:
            return {"strategy": "iron_condor", "outlook": "neutral", "confidence": 50, "source": "mock"}
    
    try:
        orchestrator = EnhancedJSONOrchestrator()
        
        analysis_prompt = f"""
        Analyze this trading request and suggest an appropriate options strategy:
        
        Request: "{prompt}"
        Symbol: {symbol}
        
        Consider:
        - Risk tolerance mentioned
        - Market outlook implied
        - Strategy complexity desired
        - Time horizon
        
        Respond with strategy recommendation and key parameters.
        """
        
        result = orchestrator.get_analysis(analysis_prompt, symbol)
        return result
        
    except Exception as e:
        print(f"Warning: LLM analysis failed: {e}")
        return {"strategy": "iron_condor", "outlook": "neutral", "confidence": 50, "source": "fallback"}

def main():
    args = parse_args()
    
    print("(R) Generating trade plan from prompt: '{}'".format(args.prompt))
    print("(S) Symbol: {}".format(args.symbol))
    print("(C) Expiration: {} days out".format(args.expiration_days))
    print("($) Max Risk: ${}".format(args.max_risk))
    print()
    
    # Generate expiration date
    expiration = generate_expiration_date(args.expiration_days)
    
    # Analyze prompt with LLM (if available)
    llm_analysis = analyze_prompt_with_llm(args.prompt, args.symbol)
    print("(AI) LLM Analysis: {} strategy suggested".format(llm_analysis.get('strategy', 'iron_condor')))
    
    # Generate trade plan based on analysis
    prompt_lower = args.prompt.lower()
    
    if "iron condor" in prompt_lower or "neutral" in prompt_lower:
        plan = create_iron_condor_plan(args.symbol, expiration, args.max_risk)
    elif "bull" in prompt_lower or "bullish" in prompt_lower:
        plan = create_vertical_spread_plan(args.symbol, expiration, args.max_risk, "bullish")
    elif "bear" in prompt_lower or "bearish" in prompt_lower:
        plan = create_vertical_spread_plan(args.symbol, expiration, args.max_risk, "bearish")
    else:
        # Default to iron condor for unknown strategies
        plan = create_iron_condor_plan(args.symbol, expiration, args.max_risk)
    
    # Add LLM analysis to metadata
    plan["metadata"]["llm_analysis"] = llm_analysis
    plan["metadata"]["original_prompt"] = args.prompt
    
    # Display plan
    print("Generated Trade Plan:")
    print(json.dumps(plan, indent=2))
    
    if args.dry_run:
        print("\nDry run mode - plan not saved")
        return 0
    
    # Save to file
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(plan, f, indent=2)
    
    print("\nTrade plan saved to: {}".format(output_path))
    print("Next step: python tools/validate_trade_plan.py --file {}".format(output_path))
    
    return 0

if __name__ == "__main__":
    sys.exit(main())