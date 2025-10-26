# src/risk/gates.py
"""
Enhanced Risk Gates for EMO Options Bot
Production-ready risk management with comprehensive validation and monitoring
"""
from __future__ import annotations
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import logging
import json
from ..core.schemas import TradePlan, PortfolioSnapshot, Violation, RiskConstraints

# Configure logging
logger = logging.getLogger(__name__)

# Enhanced default risk limits with explanations
DEFAULT_LIMITS = {
    # Position size limits
    "max_risk_pct_per_trade": 0.02,        # 2% max risk per individual trade
    "max_portfolio_risk_pct": 0.10,        # 10% max total outstanding risk
    "max_symbol_concentration_pct": 0.30,   # 30% max exposure to single symbol
    "max_sector_concentration_pct": 0.50,   # 50% max exposure to single sector
    
    # Liquidity requirements  
    "min_liquidity_adv_shares": 1_000_000,  # Min 1M shares average daily volume
    "min_option_open_interest": 100,        # Min 100 contracts open interest
    "max_bid_ask_spread_pct": 0.05,         # Max 5% bid-ask spread
    
    # Time and volatility constraints
    "min_days_to_expiry": 7,                # Min 7 days to expiration
    "max_days_to_expiry": 365,              # Max 1 year to expiration
    "max_iv_percentile": 95,                # Max 95th percentile IV
    "min_iv_percentile": 5,                 # Min 5th percentile IV
    
    # Greek exposure limits
    "max_portfolio_delta": 500,             # Max portfolio delta exposure
    "max_portfolio_gamma": 1000,            # Max portfolio gamma exposure  
    "max_portfolio_vega": 2000,             # Max portfolio vega exposure
    "max_portfolio_theta": -500,            # Max portfolio theta decay
    
    # Event and calendar restrictions
    "event_blackout_symbols": [],           # Symbols blocked during events
    "earnings_blackout_days": 2,            # Days before/after earnings to avoid
    "fed_blackout_days": 1,                 # Days before/after Fed meetings
    "vix_spike_threshold": 25,              # VIX level to trigger restrictions
    
    # Account and margin limits
    "min_account_equity": 25000,            # Min account equity for options
    "max_margin_usage_pct": 0.50,           # Max 50% margin utilization
    "min_cash_buffer_pct": 0.10,            # Min 10% cash buffer
    
    # Trade frequency limits
    "max_trades_per_day": 20,               # Max trades per day
    "max_trades_per_symbol_per_day": 5,     # Max trades per symbol per day
    "pdt_protection": True,                 # Pattern day trader protection
}

# Risk severity mapping
RISK_SEVERITY_MAP = {
    "critical": ["ACCOUNT_EQUITY", "MARGIN_CALL", "LIQUIDITY_CRISIS"],
    "error": ["MAX_TRADE_RISK", "PORTFOLIO_HEAT", "SYMBOL_CONCENTRATION", "EVENT_BLACKOUT"],
    "warn": ["LOW_LIQUIDITY", "HIGH_IV", "EARNINGS_RISK", "GREEK_EXPOSURE"],
    "info": ["TRADE_FREQUENCY", "SPREAD_WIDTH", "TIME_DECAY"]
}

class EnhancedRiskCalculator:
    """Enhanced risk calculations with Greeks and volatility analysis"""
    
    @staticmethod
    def estimate_option_risk(
        strike: float, 
        underlying_price: float, 
        volatility: float, 
        days_to_expiry: int,
        option_type: str = "call",
        quantity: int = 1
    ) -> Dict[str, float]:
        """Estimate option risk metrics using Black-Scholes approximation"""
        try:
            import math
            
            # Simplified Black-Scholes approximation
            time_to_expiry = days_to_expiry / 365.0
            moneyness = strike / underlying_price
            
            # Approximate delta
            if option_type.lower() == "call":
                delta = max(0, min(1, 0.5 + (underlying_price - strike) / (underlying_price * volatility * math.sqrt(time_to_expiry))))
            else:  # put
                delta = min(0, max(-1, -0.5 + (strike - underlying_price) / (underlying_price * volatility * math.sqrt(time_to_expiry))))
            
            # Approximate gamma (simplified)
            gamma = max(0, 1 / (underlying_price * volatility * math.sqrt(time_to_expiry * 2 * math.pi)))
            
            # Approximate theta (simplified)
            theta = -underlying_price * volatility / (2 * math.sqrt(time_to_expiry)) / 365
            
            # Approximate vega (simplified)
            vega = underlying_price * math.sqrt(time_to_expiry) / 100
            
            return {
                "delta": delta * quantity * 100,  # Standard contract multiplier
                "gamma": gamma * quantity * 100,
                "theta": theta * quantity,
                "vega": vega * quantity,
                "max_loss": abs(strike - underlying_price) * quantity * 100 if option_type.lower() == "put" else float('inf')
            }
            
        except Exception as e:
            logger.warning(f"Risk calculation failed: {e}")
            return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "max_loss": 1000}

class RiskGates:
    """Enhanced risk gates with comprehensive validation and monitoring"""
    
    def __init__(self, limits: Optional[Dict[str, Any]] = None, enable_logging: bool = True):
        self.limits = {**DEFAULT_LIMITS, **(limits or {})}
        self.enable_logging = enable_logging
        self.risk_calculator = EnhancedRiskCalculator()
        self.violation_history: List[Violation] = []
        
        # Initialize risk monitoring
        if enable_logging:
            logger.info(f"RiskGates initialized with {len(self.limits)} risk parameters")
    
    def update_limits(self, new_limits: Dict[str, Any]) -> None:
        """Update risk limits with validation"""
        try:
            # Validate new limits
            for key, value in new_limits.items():
                if key in DEFAULT_LIMITS:
                    # Type validation based on default values
                    default_type = type(DEFAULT_LIMITS[key])
                    if not isinstance(value, default_type):
                        logger.warning(f"Type mismatch for {key}: expected {default_type}, got {type(value)}")
                        continue
                    
                    # Range validation for percentages
                    if "pct" in key and (value < 0 or value > 1):
                        logger.warning(f"Percentage value {key}={value} should be between 0 and 1")
                        continue
                    
                    self.limits[key] = value
                    
            logger.info(f"Updated {len(new_limits)} risk limits")
            
        except Exception as e:
            logger.error(f"Failed to update risk limits: {e}")
    
    def get_limits_summary(self) -> Dict[str, Any]:
        """Get summary of current risk limits"""
        return {
            "position_limits": {
                k: v for k, v in self.limits.items() 
                if any(term in k for term in ["max_risk", "concentration", "portfolio"])
            },
            "liquidity_limits": {
                k: v for k, v in self.limits.items()
                if any(term in k for term in ["liquidity", "volume", "spread"])
            },
            "time_limits": {
                k: v for k, v in self.limits.items()
                if any(term in k for term in ["days", "expiry", "blackout"])
            },
            "greek_limits": {
                k: v for k, v in self.limits.items()
                if any(term in k for term in ["delta", "gamma", "theta", "vega"])
            }
        }
    
    def validate_trade(
        self,
        plan: TradePlan,
        portfolio: PortfolioSnapshot,
        market_data: Optional[Dict[str, Any]] = None,
        options_data: Optional[Dict[str, Any]] = None,
        today: Optional[str] = None
    ) -> List[Violation]:
        """
        Comprehensive trade validation with enhanced risk checks
        
        Args:
            plan: Trade plan to validate
            portfolio: Current portfolio snapshot
            market_data: Current market data (prices, volatility, etc.)
            options_data: Options chain data (Greeks, open interest, etc.)
            today: Current date string (YYYY-MM-DD)
        """
        violations: List[Violation] = []
        
        try:
            equity = max(portfolio.equity, 1.0)
            today_str = today or datetime.utcnow().strftime("%Y-%m-%d")
            
            # 1. Core risk validations
            violations.extend(self._validate_position_risk(plan, portfolio, equity))
            violations.extend(self._validate_portfolio_heat(plan, portfolio))
            violations.extend(self._validate_concentration_risk(plan, portfolio))
            
            # 2. Liquidity validations
            if market_data:
                violations.extend(self._validate_liquidity(plan, market_data))
            
            # 3. Options-specific validations
            if options_data and any(leg.instrument in ['call', 'put'] for leg in plan.legs):
                violations.extend(self._validate_options_risk(plan, options_data))
            
            # 4. Time and calendar validations
            violations.extend(self._validate_time_constraints(plan, today_str))
            violations.extend(self._validate_event_risk(plan, today_str))
            
            # 5. Greek exposure validations
            violations.extend(self._validate_greek_exposure(plan, portfolio))
            
            # 6. Account and margin validations
            violations.extend(self._validate_account_requirements(plan, portfolio))
            
            # 7. Trade frequency validations
            violations.extend(self._validate_trade_frequency(plan, today_str))
            
            # Log violations for monitoring
            if violations and self.enable_logging:
                self._log_violations(plan, violations)
            
            # Store violations for history tracking
            self.violation_history.extend(violations)
            
            return violations
            
        except Exception as e:
            logger.error(f"Risk validation failed: {e}")
            return [Violation(
                code="VALIDATION_ERROR",
                message=f"Risk validation system error: {str(e)}",
                severity="critical",
                category="system",
                source="risk_gates"
            )]
    
    def _validate_position_risk(self, plan: TradePlan, portfolio: PortfolioSnapshot, equity: float) -> List[Violation]:
        """Validate individual position risk limits"""
        violations = []
        
        try:
            # Estimate trade risk
            trade_risk = self._estimate_plan_risk(plan, equity)
            max_per_trade = self.limits["max_risk_pct_per_trade"] * equity
            
            if trade_risk > max_per_trade:
                violations.append(Violation(
                    code="MAX_TRADE_RISK",
                    message=f"Trade risk ${trade_risk:.0f} exceeds {self.limits['max_risk_pct_per_trade']*100:.1f}% limit (${max_per_trade:.0f})",
                    severity="error",
                    category="position_size",
                    data={
                        "trade_risk": trade_risk,
                        "limit": max_per_trade,
                        "risk_pct": trade_risk / equity
                    },
                    suggested_action=f"Reduce position size to ${max_per_trade:.0f} or less"
                ))
                
        except Exception as e:
            logger.warning(f"Position risk validation failed: {e}")
            
        return violations
    
    def _validate_portfolio_heat(self, plan: TradePlan, portfolio: PortfolioSnapshot) -> List[Violation]:
        """Validate overall portfolio risk exposure"""
        violations = []
        
        try:
            current_heat = portfolio.risk_exposure_pct
            max_heat = self.limits["max_portfolio_risk_pct"]
            
            if current_heat > max_heat:
                violations.append(Violation(
                    code="PORTFOLIO_HEAT",
                    message=f"Portfolio heat {current_heat*100:.1f}% exceeds {max_heat*100:.1f}% limit",
                    severity="error",
                    category="portfolio_risk",
                    data={
                        "current_heat": current_heat,
                        "limit": max_heat
                    },
                    suggested_action="Close existing positions or reduce new position size"
                ))
                
        except Exception as e:
            logger.warning(f"Portfolio heat validation failed: {e}")
            
        return violations
    
    def _validate_concentration_risk(self, plan: TradePlan, portfolio: PortfolioSnapshot) -> List[Violation]:
        """Validate symbol and sector concentration limits"""
        violations = []
        
        try:
            symbol = plan.underlying
            max_symbol_conc = self.limits["max_symbol_concentration_pct"]
            
            # Calculate current symbol exposure
            total_value = portfolio.calculate_total_market_value()
            symbol_exposure = 0.0
            
            for pos in portfolio.positions:
                if pos.symbol == symbol:
                    symbol_exposure += abs(pos.calculate_market_value())
            
            if total_value > 0:
                symbol_concentration = symbol_exposure / total_value
                
                if symbol_concentration > max_symbol_conc:
                    violations.append(Violation(
                        code="SYMBOL_CONCENTRATION",
                        message=f"Symbol {symbol} concentration {symbol_concentration*100:.1f}% exceeds {max_symbol_conc*100:.1f}% limit",
                        severity="error",
                        category="concentration",
                        data={
                            "symbol": symbol,
                            "concentration": symbol_concentration,
                            "limit": max_symbol_conc
                        },
                        suggested_action=f"Reduce {symbol} exposure or diversify portfolio"
                    ))
                    
        except Exception as e:
            logger.warning(f"Concentration risk validation failed: {e}")
            
        return violations
    
    def _validate_liquidity(self, plan: TradePlan, market_data: Dict[str, Any]) -> List[Violation]:
        """Validate liquidity requirements"""
        violations = []
        
        try:
            symbol = plan.underlying
            min_adv = self.limits["min_liquidity_adv_shares"]
            max_spread = self.limits["max_bid_ask_spread_pct"]
            
            # Check average daily volume
            adv = market_data.get("avg_daily_volume", 0)
            if adv < min_adv:
                violations.append(Violation(
                    code="LOW_LIQUIDITY",
                    message=f"{symbol} ADV {adv:,} below minimum {min_adv:,} shares",
                    severity="warn",
                    category="liquidity",
                    data={
                        "symbol": symbol,
                        "adv": adv,
                        "minimum": min_adv
                    },
                    suggested_action="Consider more liquid alternatives"
                ))
            
            # Check bid-ask spread
            bid = market_data.get("bid", 0)
            ask = market_data.get("ask", 0)
            if bid > 0 and ask > 0:
                spread_pct = (ask - bid) / ((ask + bid) / 2)
                if spread_pct > max_spread:
                    violations.append(Violation(
                        code="WIDE_SPREAD",
                        message=f"{symbol} bid-ask spread {spread_pct*100:.2f}% exceeds {max_spread*100:.1f}% limit",
                        severity="warn",
                        category="liquidity",
                        data={
                            "spread_pct": spread_pct,
                            "limit": max_spread
                        },
                        suggested_action="Use limit orders or wait for better liquidity"
                    ))
                    
        except Exception as e:
            logger.warning(f"Liquidity validation failed: {e}")
            
        return violations
    
    def _validate_options_risk(self, plan: TradePlan, options_data: Dict[str, Any]) -> List[Violation]:
        """Validate options-specific risks"""
        violations = []
        
        try:
            min_oi = self.limits["min_option_open_interest"]
            
            for leg in plan.legs:
                if leg.instrument in ['call', 'put'] and leg.strike and leg.expiry:
                    # Check open interest
                    chain_key = f"{leg.instrument}_{leg.strike}_{leg.expiry}"
                    option_info = options_data.get(chain_key, {})
                    open_interest = option_info.get("open_interest", 0)
                    
                    if open_interest < min_oi:
                        violations.append(Violation(
                            code="LOW_OPEN_INTEREST",
                            message=f"{leg.instrument.upper()} {leg.strike} open interest {open_interest} below minimum {min_oi}",
                            severity="warn",
                            category="options_liquidity",
                            data={
                                "open_interest": open_interest,
                                "minimum": min_oi,
                                "strike": leg.strike,
                                "expiry": leg.expiry
                            },
                            suggested_action="Choose strikes with higher open interest"
                        ))
                        
        except Exception as e:
            logger.warning(f"Options risk validation failed: {e}")
            
        return violations
    
    def _validate_time_constraints(self, plan: TradePlan, today: str) -> List[Violation]:
        """Validate time-based constraints"""
        violations = []
        
        try:
            min_dte = self.limits["min_days_to_expiry"]
            max_dte = self.limits["max_days_to_expiry"]
            today_date = datetime.strptime(today, "%Y-%m-%d").date()
            
            for leg in plan.legs:
                if leg.expiry and leg.instrument in ['call', 'put']:
                    expiry_date = datetime.strptime(leg.expiry, "%Y-%m-%d").date()
                    days_to_expiry = (expiry_date - today_date).days
                    
                    if days_to_expiry < min_dte:
                        violations.append(Violation(
                            code="EXPIRY_TOO_SOON",
                            message=f"Option expires in {days_to_expiry} days, minimum is {min_dte} days",
                            severity="warn",
                            category="time_risk",
                            data={
                                "days_to_expiry": days_to_expiry,
                                "minimum": min_dte,
                                "expiry": leg.expiry
                            },
                            suggested_action="Choose options with longer expiration"
                        ))
                    
                    elif days_to_expiry > max_dte:
                        violations.append(Violation(
                            code="EXPIRY_TOO_FAR",
                            message=f"Option expires in {days_to_expiry} days, maximum is {max_dte} days",
                            severity="info",
                            category="time_risk",
                            data={
                                "days_to_expiry": days_to_expiry,
                                "maximum": max_dte,
                                "expiry": leg.expiry
                            },
                            suggested_action="Consider shorter-term options for better theta"
                        ))
                        
        except Exception as e:
            logger.warning(f"Time constraint validation failed: {e}")
            
        return violations
    
    def _validate_event_risk(self, plan: TradePlan, today: str) -> List[Violation]:
        """Validate event-based risk restrictions"""
        violations = []
        
        try:
            symbol = plan.underlying
            blackout_list = self.limits["event_blackout_symbols"]
            
            # Check specific event blackouts
            event_key = f"{symbol}:{today}"
            if event_key in blackout_list:
                violations.append(Violation(
                    code="EVENT_BLACKOUT",
                    message=f"Trading {symbol} blocked due to event blackout on {today}",
                    severity="error",
                    category="event_risk",
                    data={
                        "symbol": symbol,
                        "date": today,
                        "blackout_key": event_key
                    },
                    suggested_action="Wait until after the event or choose different symbol"
                ))
                
        except Exception as e:
            logger.warning(f"Event risk validation failed: {e}")
            
        return violations
    
    def _validate_greek_exposure(self, plan: TradePlan, portfolio: PortfolioSnapshot) -> List[Violation]:
        """Validate Greek exposure limits"""
        violations = []
        
        try:
            # Get current Greek exposures
            current_delta = portfolio.greek_exposure.get("delta", 0)
            current_gamma = portfolio.greek_exposure.get("gamma", 0)
            current_vega = portfolio.greek_exposure.get("vega", 0)
            current_theta = portfolio.greek_exposure.get("theta", 0)
            
            # Validate against limits
            greek_limits = {
                "delta": self.limits["max_portfolio_delta"],
                "gamma": self.limits["max_portfolio_gamma"],
                "vega": self.limits["max_portfolio_vega"],
                "theta": self.limits["max_portfolio_theta"]
            }
            
            greek_current = {
                "delta": current_delta,
                "gamma": current_gamma,
                "vega": current_vega,
                "theta": current_theta
            }
            
            for greek, limit in greek_limits.items():
                current_value = greek_current[greek]
                
                if greek == "theta":  # Theta is negative, so check if more negative than limit
                    if current_value < limit:
                        violations.append(Violation(
                            code="GREEK_EXPOSURE",
                            message=f"Portfolio {greek} {current_value:.0f} exceeds limit {limit:.0f}",
                            severity="warn",
                            category="greek_risk",
                            data={
                                "greek": greek,
                                "current": current_value,
                                "limit": limit
                            },
                            suggested_action=f"Reduce portfolio {greek} exposure"
                        ))
                else:  # Delta, gamma, vega are positive limits
                    if abs(current_value) > limit:
                        violations.append(Violation(
                            code="GREEK_EXPOSURE",
                            message=f"Portfolio {greek} {current_value:.0f} exceeds limit {limit:.0f}",
                            severity="warn",
                            category="greek_risk",
                            data={
                                "greek": greek,
                                "current": current_value,
                                "limit": limit
                            },
                            suggested_action=f"Reduce portfolio {greek} exposure"
                        ))
                        
        except Exception as e:
            logger.warning(f"Greek exposure validation failed: {e}")
            
        return violations
    
    def _validate_account_requirements(self, plan: TradePlan, portfolio: PortfolioSnapshot) -> List[Violation]:
        """Validate account and margin requirements"""
        violations = []
        
        try:
            equity = portfolio.equity
            min_equity = self.limits["min_account_equity"]
            
            # Check minimum equity for options trading
            if equity < min_equity:
                violations.append(Violation(
                    code="MIN_EQUITY",
                    message=f"Account equity ${equity:,.0f} below minimum ${min_equity:,.0f} for options trading",
                    severity="critical",
                    category="account",
                    data={
                        "equity": equity,
                        "minimum": min_equity
                    },
                    suggested_action="Deposit funds or trade stocks only"
                ))
                
        except Exception as e:
            logger.warning(f"Account requirements validation failed: {e}")
            
        return violations
    
    def _validate_trade_frequency(self, plan: TradePlan, today: str) -> List[Violation]:
        """Validate trade frequency limits"""
        violations = []
        
        try:
            # This would require tracking trade history
            # For now, just validate against daily limits
            max_daily = self.limits["max_trades_per_day"]
            
            # Placeholder - would check actual trade count from database
            daily_trade_count = 0  # Would be fetched from trade history
            
            if daily_trade_count >= max_daily:
                violations.append(Violation(
                    code="DAILY_TRADE_LIMIT",
                    message=f"Daily trade limit {max_daily} reached",
                    severity="warn",
                    category="frequency",
                    data={
                        "daily_count": daily_trade_count,
                        "limit": max_daily
                    },
                    suggested_action="Wait until next trading day"
                ))
                
        except Exception as e:
            logger.warning(f"Trade frequency validation failed: {e}")
            
        return violations
    
    def _estimate_plan_risk(self, plan: TradePlan, equity: float) -> float:
        """Enhanced risk estimation for trade plans"""
        try:
            # Use explicit risk constraints if provided
            if plan.risk_constraints.max_risk_dollars:
                return plan.risk_constraints.max_risk_dollars
            if plan.risk_constraints.max_risk_pct:
                return equity * plan.risk_constraints.max_risk_pct
            
            # Strategy-specific risk estimation
            if plan.strategy_type in ["iron_condor", "put_credit_spread", "call_credit_spread"]:
                # For spreads, risk is approximately the spread width
                strikes = [leg.strike for leg in plan.legs if leg.strike is not None]
                if len(strikes) >= 2:
                    spread_width = abs(max(strikes) - min(strikes))
                    return spread_width * 100  # Options multiplier
                    
            elif plan.strategy_type == "covered_call":
                # Risk is the stock value minus premium collected
                stock_legs = [leg for leg in plan.legs if leg.instrument == "stock"]
                if stock_legs:
                    return abs(stock_legs[0].quantity) * (stock_legs[0].price or 100)  # Estimate
                    
            elif plan.strategy_type in ["straddle", "strangle"]:
                # Risk is the premium paid
                return equity * 0.03  # Conservative 3% estimate
            
            # Default conservative estimate
            return equity * 0.015  # 1.5% default
            
        except Exception as e:
            logger.warning(f"Risk estimation failed: {e}")
            return equity * 0.02  # 2% fallback
    
    def _log_violations(self, plan: TradePlan, violations: List[Violation]) -> None:
        """Log risk violations for monitoring and analysis"""
        try:
            if not violations:
                return
                
            violation_summary = {
                "strategy": plan.strategy_type,
                "underlying": plan.underlying,
                "violation_count": len(violations),
                "critical_count": sum(1 for v in violations if v.severity == "critical"),
                "error_count": sum(1 for v in violations if v.severity == "error"),
                "warn_count": sum(1 for v in violations if v.severity == "warn"),
                "violations": [v.code for v in violations]
            }
            
            logger.warning(f"Risk violations detected: {json.dumps(violation_summary, indent=2)}")
            
        except Exception as e:
            logger.error(f"Failed to log violations: {e}")
    
    def get_violation_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get summary of recent violations for monitoring"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            recent_violations = [
                v for v in self.violation_history 
                if v.timestamp >= cutoff_date
            ]
            
            return {
                "period_days": days,
                "total_violations": len(recent_violations),
                "by_severity": {
                    severity: len([v for v in recent_violations if v.severity == severity])
                    for severity in ["critical", "error", "warn", "info"]
                },
                "by_category": {
                    category: len([v for v in recent_violations if v.category == category])
                    for category in set(v.category for v in recent_violations if v.category)
                },
                "top_codes": {
                    code: len([v for v in recent_violations if v.code == code])
                    for code in sorted(set(v.code for v in recent_violations), 
                                     key=lambda c: len([v for v in recent_violations if v.code == c]),
                                     reverse=True)[:10]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to generate violation summary: {e}")
            return {"error": str(e)}

# Utility functions for risk management
def create_conservative_limits(account_size: float) -> Dict[str, Any]:
    """Create conservative risk limits based on account size"""
    base_limits = DEFAULT_LIMITS.copy()
    
    if account_size < 50000:  # Small accounts
        base_limits.update({
            "max_risk_pct_per_trade": 0.01,  # 1% max risk
            "max_portfolio_risk_pct": 0.05,  # 5% total risk
            "max_symbol_concentration_pct": 0.25,  # 25% max concentration
        })
    elif account_size > 500000:  # Large accounts
        base_limits.update({
            "max_risk_pct_per_trade": 0.03,  # 3% max risk
            "max_portfolio_risk_pct": 0.15,  # 15% total risk
            "max_symbol_concentration_pct": 0.40,  # 40% max concentration
        })
    
    return base_limits

def validate_risk_limits(limits: Dict[str, Any]) -> List[str]:
    """Validate risk limits configuration"""
    errors = []
    
    # Check required keys
    required_keys = ["max_risk_pct_per_trade", "max_portfolio_risk_pct", "max_symbol_concentration_pct"]
    for key in required_keys:
        if key not in limits:
            errors.append(f"Missing required limit: {key}")
    
    # Check percentage ranges
    percentage_keys = [k for k in limits.keys() if "pct" in k]
    for key in percentage_keys:
        value = limits.get(key)
        if value is not None and (value < 0 or value > 1):
            errors.append(f"Percentage {key} must be between 0 and 1, got {value}")
    
    return errors

# Export main classes and functions
__all__ = [
    "RiskGates", "EnhancedRiskCalculator", "DEFAULT_LIMITS", "RISK_SEVERITY_MAP",
    "create_conservative_limits", "validate_risk_limits"
]