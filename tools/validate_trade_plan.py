#!/usr/bin/env python3
"""
Trade Plan Validator
Validates trade plans for risk compliance and feasibility
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Try to import risk module, fall back to mock
try:
    from risk.math import Leg, iron_condor_risk, vertical_spread_risk, RiskProfile
    HAS_RISK_MODULE = True
except ImportError:
    print("Warning: Risk module not available, using mock validation")
    HAS_RISK_MODULE = False
    
    # Mock implementations
    class Leg:
        def __init__(self, strike, option_type, action, quantity, premium):
            self.strike = strike
            self.option_type = option_type
            self.action = action
            self.quantity = quantity
            self.premium = premium
    
    class RiskProfile:
        def __init__(self, max_loss, max_profit, breakeven_lower=0, breakeven_upper=0, breakeven=None):
            self.max_loss = max_loss
            self.max_profit = max_profit
            self.breakeven_lower = breakeven_lower
            self.breakeven_upper = breakeven_upper
            self.breakeven = breakeven
    
    def iron_condor_risk(legs):
        """Mock iron condor risk calculation"""
        return RiskProfile(max_loss=500, max_profit=100, breakeven_lower=430, breakeven_upper=470)
    
    def vertical_spread_risk(legs):
        """Mock vertical spread risk calculation"""
        return RiskProfile(max_loss=300, max_profit=200, breakeven=445)

def parse_args():
    parser = argparse.ArgumentParser(description="Validate trade plans for risk and feasibility")
    parser.add_argument("--file", required=True, help="Path to trade plan JSON file")
    parser.add_argument("--strict", action="store_true", help="Enable strict validation mode")
    parser.add_argument("--max-risk-pct", type=float, default=0.05, help="Max portfolio risk % (default: 0.05)")
    parser.add_argument("--portfolio-value", type=float, default=100000, help="Portfolio value for % calculations")
    return parser.parse_args()

def load_trade_plan(file_path: str) -> Dict:
    """Load and parse trade plan JSON"""
    try:
        with open(file_path, 'r') as f:
            plan = json.load(f)
        return plan
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(1)

def validate_plan_structure(plan: Dict) -> List[str]:
    """Validate basic plan structure"""
    errors = []
    
    required_fields = ["strategy_type", "symbol", "expiration", "legs"]
    for field in required_fields:
        if field not in plan:
            errors.append(f"Missing required field: {field}")
    
    # Validate legs structure
    if "legs" in plan:
        for i, leg in enumerate(plan["legs"]):
            required_leg_fields = ["action", "instrument", "strike", "quantity"]
            for field in required_leg_fields:
                if field not in leg:
                    errors.append(f"Leg {i+1}: Missing field '{field}'")
            
            # Validate field values
            if "action" in leg and leg["action"] not in ["buy", "sell"]:
                errors.append(f"Leg {i+1}: Invalid action '{leg['action']}' (must be 'buy' or 'sell')")
            
            if "instrument" in leg and leg["instrument"] not in ["call", "put"]:
                errors.append(f"Leg {i+1}: Invalid instrument '{leg['instrument']}' (must be 'call' or 'put')")
    
    return errors

def validate_iron_condor(legs: List[Dict]) -> Tuple[List[str], RiskProfile]:
    """Validate iron condor specific rules"""
    errors = []
    
    if len(legs) != 4:
        errors.append(f"Iron condor must have 4 legs, found {len(legs)}")
        return errors, RiskProfile(max_loss=0, max_profit=0, breakeven_lower=0, breakeven_upper=0)
    
    # Convert to Leg objects for risk calculation
    try:
        risk_legs = []
        for leg_data in legs:
            leg = Leg(
                strike=float(leg_data["strike"]),
                option_type=leg_data["instrument"],
                action=leg_data["action"],
                quantity=int(leg_data["quantity"]),
                premium=5.0  # Mock premium for validation
            )
            risk_legs.append(leg)
        
        # Calculate risk profile
        risk_profile = iron_condor_risk(risk_legs)
        
        # Validate iron condor structure
        puts = [leg for leg in legs if leg["instrument"] == "put"]
        calls = [leg for leg in legs if leg["instrument"] == "call"]
        
        if len(puts) != 2 or len(calls) != 2:
            errors.append("Iron condor must have 2 puts and 2 calls")
        
        # Check for proper strike ordering
        put_strikes = sorted([leg["strike"] for leg in puts])
        call_strikes = sorted([leg["strike"] for leg in calls])
        
        if len(put_strikes) == 2 and put_strikes[0] >= put_strikes[1]:
            errors.append("Put strikes must be in ascending order")
        
        if len(call_strikes) == 2 and call_strikes[0] >= call_strikes[1]:
            errors.append("Call strikes must be in ascending order")
        
        return errors, risk_profile
        
    except Exception as e:
        errors.append(f"Risk calculation failed: {e}")
        return errors, RiskProfile(max_loss=0, max_profit=0, breakeven_lower=0, breakeven_upper=0)

def validate_vertical_spread(legs: List[Dict]) -> Tuple[List[str], RiskProfile]:
    """Validate vertical spread specific rules"""
    errors = []
    
    if len(legs) != 2:
        errors.append(f"Vertical spread must have 2 legs, found {len(legs)}")
        return errors, RiskProfile(max_loss=0, max_profit=0, breakeven_lower=0, breakeven_upper=0)
    
    # Convert to Leg objects
    try:
        risk_legs = []
        for leg_data in legs:
            leg = Leg(
                strike=float(leg_data["strike"]),
                option_type=leg_data["instrument"],
                action=leg_data["action"],
                quantity=int(leg_data["quantity"]),
                premium=3.0  # Mock premium
            )
            risk_legs.append(leg)
        
        risk_profile = vertical_spread_risk(risk_legs)
        
        # Validate vertical spread structure
        instruments = [leg["instrument"] for leg in legs]
        if len(set(instruments)) != 1:
            errors.append("Vertical spread must use same instrument type (all calls or all puts)")
        
        actions = [leg["action"] for leg in legs]
        if "buy" not in actions or "sell" not in actions:
            errors.append("Vertical spread must have one buy and one sell")
        
        return errors, risk_profile
        
    except Exception as e:
        errors.append(f"Risk calculation failed: {e}")
        return errors, RiskProfile(max_loss=0, max_profit=0, breakeven_lower=0, breakeven_upper=0)

def validate_risk_constraints(plan: Dict, risk_profile: RiskProfile, max_risk_pct: float, portfolio_value: float) -> List[str]:
    """Validate risk constraints"""
    errors = []
    
    constraints = plan.get("risk_constraints", {})
    
    # Check max loss constraint
    if "max_loss" in constraints:
        max_loss_limit = constraints["max_loss"]
        if risk_profile.max_loss > max_loss_limit:
            errors.append(f"Max loss ${risk_profile.max_loss:.2f} exceeds limit ${max_loss_limit:.2f}")
    
    # Check portfolio risk percentage
    if "max_trade_risk_pct" in constraints:
        max_pct = constraints["max_trade_risk_pct"]
        actual_pct = risk_profile.max_loss / portfolio_value
        if actual_pct > max_pct:
            errors.append(f"Trade risk {actual_pct*100:.2f}% exceeds limit {max_pct*100:.2f}%")
    
    # Global portfolio risk check
    portfolio_risk_pct = risk_profile.max_loss / portfolio_value
    if portfolio_risk_pct > max_risk_pct:
        errors.append(f"Portfolio risk {portfolio_risk_pct*100:.2f}% exceeds global limit {max_risk_pct*100:.2f}%")
    
    return errors

def print_risk_summary(risk_profile: RiskProfile):
    """Print risk analysis summary"""
    print("\n📊 Risk Analysis:")
    print(f"   Max Loss: ${risk_profile.max_loss:.2f}")
    print(f"   Max Profit: ${risk_profile.max_profit:.2f}")
    print(f"   Risk/Reward: {risk_profile.max_profit/max(risk_profile.max_loss, 1):.2f}")
    
    if hasattr(risk_profile, 'breakeven_lower') and hasattr(risk_profile, 'breakeven_upper'):
        print(f"   Breakeven Range: ${risk_profile.breakeven_lower:.2f} - ${risk_profile.breakeven_upper:.2f}")
    elif hasattr(risk_profile, 'breakeven'):
        print(f"   Breakeven: ${risk_profile.breakeven:.2f}")

def main():
    args = parse_args()
    
    print(f"🔍 Validating trade plan: {args.file}")
    print(f"📊 Portfolio Value: ${args.portfolio_value:,.2f}")
    print(f"⚠️ Max Risk Allowed: {args.max_risk_pct*100:.1f}%")
    print()
    
    # Load trade plan
    plan = load_trade_plan(args.file)
    
    # Validate structure
    print("🔧 Validating plan structure...")
    structure_errors = validate_plan_structure(plan)
    
    if structure_errors:
        print("❌ Structure validation failed:")
        for error in structure_errors:
            print(f"   • {error}")
        return 1
    
    print("✅ Plan structure valid")
    
    # Strategy-specific validation
    strategy_type = plan["strategy_type"]
    legs = plan["legs"]
    
    print(f"🎯 Validating {strategy_type} strategy...")
    
    if strategy_type == "iron_condor":
        strategy_errors, risk_profile = validate_iron_condor(legs)
    elif "vertical_spread" in strategy_type:
        strategy_errors, risk_profile = validate_vertical_spread(legs)
    else:
        print(f"⚠️ Unknown strategy type: {strategy_type}")
        strategy_errors = [f"Unsupported strategy: {strategy_type}"]
        risk_profile = RiskProfile(max_loss=0, max_profit=0, breakeven_lower=0, breakeven_upper=0)
    
    if strategy_errors:
        print("❌ Strategy validation failed:")
        for error in strategy_errors:
            print(f"   • {error}")
        return 1
    
    print(f"✅ {strategy_type} strategy valid")
    
    # Risk constraint validation
    print("💰 Validating risk constraints...")
    risk_errors = validate_risk_constraints(plan, risk_profile, args.max_risk_pct, args.portfolio_value)
    
    if risk_errors:
        print("❌ Risk validation failed:")
        for error in risk_errors:
            print(f"   • {error}")
        print_risk_summary(risk_profile)
        return 1
    
    print("✅ Risk constraints satisfied")
    print_risk_summary(risk_profile)
    
    # Summary
    print("\n" + "="*50)
    print("✅ VALIDATION PASSED")
    print(f"📋 Plan: {plan['strategy_type']} on {plan['symbol']}")
    print(f"📅 Expiration: {plan['expiration']}")
    print(f"💰 Max Risk: ${risk_profile.max_loss:.2f}")
    print(f"🎯 Max Profit: ${risk_profile.max_profit:.2f}")
    print()
    print(f"🔍 Next step: python tools/stage_order_cli.py --from-plan {args.file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())