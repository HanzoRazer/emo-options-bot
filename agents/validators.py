# agents/validators.py
from dataclasses import dataclass
from typing import List, Tuple, Dict
from .plan_synthesizer import Plan, Leg

@dataclass
class Validation:
    ok: bool
    warnings: List[str]
    errors: List[str]
    risk_score: float = 0.0  # 0-10 scale
    position_size_pct: float = 0.0

def risk_check(plan: Plan, netliq: float = 100000.0, max_pos_pct: float = 0.02) -> Validation:
    warnings, errors = [], []
    risk_score = 0.0
    
    # Calculate defined risk from leg structure
    defined_risk = 0.0
    
    # Better risk calculation: infer width from paired legs
    widths: List[float] = []
    calls = [l for l in plan.legs if "call" in l.kind]
    puts = [l for l in plan.legs if "put" in l.kind]
    
    if len(calls) >= 2:
        short_calls = [l for l in calls if l.kind == "short_call"]
        long_calls = [l for l in calls if l.kind == "long_call"]
        if short_calls and long_calls:
            sc = short_calls[0].strike
            lc = long_calls[0].strike
            widths.append(abs(lc - sc))
    
    if len(puts) >= 2:
        short_puts = [l for l in puts if l.kind == "short_put"]
        long_puts = [l for l in puts if l.kind == "long_put"]
        if short_puts and long_puts:
            sp = short_puts[0].strike
            lp = long_puts[0].strike
            widths.append(abs(sp - lp))

    if widths:
        # $100 per point per 1 lot for spreads
        defined_risk = max(widths) * 100
    elif plan.est_debit:
        # For debit strategies, max loss is the debit paid
        defined_risk = plan.est_debit * 100
    elif plan.max_loss and plan.max_loss != float('inf'):
        defined_risk = plan.max_loss
    else:
        # For undefined risk strategies (like covered calls)
        defined_risk = netliq * 0.10  # Assume 10% portfolio risk

    # Position sizing validation
    position_size_pct = defined_risk / netliq if netliq > 0 else 0
    max_pos = netliq * max_pos_pct
    
    if defined_risk > max_pos:
        errors.append(f"Defined risk ${defined_risk:,.0f} exceeds {max_pos_pct*100:.1f}% of net liq (${max_pos:,.0f}).")
        risk_score += 3.0

    # Credit/debit validation
    if plan.est_credit is not None and plan.est_credit < 0.25:
        warnings.append(f"Credit is small (${plan.est_credit:.2f}) — risk/reward may be poor.")
        risk_score += 1.0
    
    if plan.est_debit is not None and plan.est_debit > netliq * 0.05:
        warnings.append(f"Debit ${plan.est_debit:.2f} is large relative to account size.")
        risk_score += 2.0

    # DTE validation
    if plan.dte < 3:
        errors.append(f"DTE {plan.dte} is too short - high gamma risk.")
        risk_score += 4.0
    elif plan.dte < 7:
        warnings.append(f"DTE {plan.dte} is short - monitor gamma risk.")
        risk_score += 1.5

    if plan.dte > 60:
        warnings.append(f"DTE {plan.dte} is long - high theta decay time.")
        risk_score += 0.5

    # Risk level validation
    if plan.risk_level == "high":
        risk_score += 2.0
        if position_size_pct > 0.01:  # 1% max for high risk
            errors.append("High risk strategies limited to 1% position size.")
    elif plan.risk_level == "low":
        risk_score -= 1.0  # Bonus for conservative approach
        if position_size_pct > 0.03:  # 3% max for low risk
            warnings.append("Even low risk strategies should be sized appropriately.")

    # Strategy-specific validations
    if plan.strategy == "iron_condor":
        # Check wing sizes
        if widths and min(widths) < 3:
            warnings.append("Narrow condor wings may have poor fills.")
        if widths and max(widths) > 20:
            warnings.append("Wide condor wings increase capital requirements.")
            
    elif plan.strategy in ["put_credit_spread", "call_credit_spread"]:
        if widths and widths[0] < 2:
            warnings.append("Very narrow spreads may have poor risk/reward.")
        if widths and widths[0] > 15:
            warnings.append("Wide spreads tie up significant capital.")
            
    elif plan.strategy == "covered_call":
        warnings.append("Covered call limits upside if stock moves significantly higher.")
        
    elif plan.strategy == "protective_put":
        if plan.est_debit and plan.est_debit > 3.0:
            warnings.append("Expensive protective puts may not be cost-effective.")
            
    elif plan.strategy == "long_straddle":
        risk_score += 1.5  # Inherently higher risk
        warnings.append("Long straddle requires significant movement to profit.")

    # Symbol-specific validations
    high_vol_symbols = ["TSLA", "NVDA", "MEME"]  # Add more as needed
    if plan.symbol in high_vol_symbols:
        warnings.append(f"{plan.symbol} is a high volatility symbol - exercise extra caution.")
        risk_score += 1.0

    # Final risk score capping
    risk_score = min(risk_score, 10.0)
    risk_score = max(risk_score, 0.0)

    # Additional position concentration check
    # In a real system, this would check existing positions
    symbol_concentration_warning = False
    if position_size_pct > 0.15:  # 15% in any single symbol
        warnings.append(f"Large position concentration in {plan.symbol} - consider diversification.")
        symbol_concentration_warning = True

    # Liquidity warnings for less common symbols
    major_symbols = ["SPY", "QQQ", "IWM", "DIA", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"]
    if plan.symbol not in major_symbols:
        warnings.append(f"{plan.symbol} may have lower options liquidity - check bid/ask spreads.")

    return Validation(
        ok=(len(errors) == 0), 
        warnings=warnings, 
        errors=errors,
        risk_score=risk_score,
        position_size_pct=position_size_pct
    )

def portfolio_impact_check(plan: Plan, existing_positions: List[Dict] = None, netliq: float = 100000.0) -> Validation:
    """Additional validation for portfolio-level impact"""
    warnings, errors = [], []
    
    if existing_positions is None:
        existing_positions = []
    
    # Check for similar positions
    similar_positions = [
        pos for pos in existing_positions 
        if pos.get('symbol') == plan.symbol and pos.get('strategy') == plan.strategy
    ]
    
    if len(similar_positions) > 0:
        warnings.append(f"Already have {len(similar_positions)} similar position(s) in {plan.symbol}")
    
    # Check total portfolio Greeks exposure (simplified)
    total_delta_exposure = sum(pos.get('delta', 0) for pos in existing_positions)
    if abs(total_delta_exposure) > 0.5:  # More than 50 delta equivalent
        warnings.append("Portfolio has significant directional bias - consider hedging")
    
    return Validation(
        ok=(len(errors) == 0),
        warnings=warnings,
        errors=errors
    )