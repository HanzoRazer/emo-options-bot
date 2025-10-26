# agents/enhanced_validators.py
"""
Enhanced Risk Validators with sophisticated analysis and recommendations.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import math
from datetime import datetime, timedelta

from .plan_synthesizer import Plan, Leg

class RiskSeverity(Enum):
    """Risk severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ValidationCategory(Enum):
    """Categories of validation checks."""
    STRUCTURE = "structure"
    STRATEGY = "strategy"
    RISK = "risk"
    MARKET = "market"
    PORTFOLIO = "portfolio"
    LIQUIDITY = "liquidity"

@dataclass
class ValidationIssue:
    """Individual validation issue with detailed information."""
    category: ValidationCategory
    severity: RiskSeverity
    message: str
    recommendation: str = ""
    impact: str = ""
    fix_suggestion: str = ""

@dataclass
class RiskMetrics:
    """Comprehensive risk metrics."""
    max_loss: float = 0.0
    max_profit: float = 0.0
    breakeven_points: List[float] = field(default_factory=list)
    probability_of_profit: float = 0.0
    expected_return: float = 0.0
    risk_reward_ratio: float = 0.0
    gamma_risk: float = 0.0
    theta_decay: float = 0.0
    vega_exposure: float = 0.0
    delta_exposure: float = 0.0

@dataclass
class EnhancedValidation:
    """Enhanced validation result with detailed analysis."""
    ok: bool
    risk_score: float
    position_size_pct: float
    warnings: List[ValidationIssue] = field(default_factory=list)
    errors: List[ValidationIssue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    risk_metrics: Optional[RiskMetrics] = None
    market_conditions: Dict[str, Any] = field(default_factory=dict)
    stress_test_results: Dict[str, float] = field(default_factory=dict)

class EnhancedRiskValidator:
    """Enhanced risk validator with sophisticated analysis."""
    
    def __init__(self):
        """Initialize enhanced validator."""
        self.risk_limits = {
            "max_portfolio_risk_per_trade": 0.02,  # 2%
            "max_symbol_allocation": 0.20,  # 20%
            "min_probability_of_profit": 0.55,  # 55%
            "max_contracts_per_trade": 10,
            "min_days_to_expiry": 3,
            "max_days_to_expiry": 90,
            "min_credit_amount": 0.25,
            "max_wing_width": 25,
            "min_wing_width": 2,
            "max_gamma_risk_score": 7.0,
            "max_overall_risk_score": 8.0
        }
        
        # Symbol classifications
        self.high_vol_symbols = {"TSLA", "NVDA", "AMD", "NFLX", "ROKU", "PELOTON"}
        self.liquid_symbols = {"SPY", "QQQ", "IWM", "DIA", "AAPL", "MSFT", "GOOGL", "AMZN"}
        self.earnings_prone = {"AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "NFLX"}
        
        # Market condition simulators
        self.stress_scenarios = {
            "market_crash": -0.15,  # 15% drop
            "volatility_spike": 2.0,  # 2x volatility
            "low_volume": 0.5,  # 50% volume
            "earnings_surprise": 0.08  # 8% surprise move
        }
    
    def validate_plan(
        self, 
        plan: Plan, 
        portfolio: Optional[Dict] = None,
        market_data: Optional[Dict] = None,
        netliq: float = 100000.0
    ) -> EnhancedValidation:
        """Comprehensive plan validation with enhanced analysis."""
        
        validation = EnhancedValidation(
            ok=True,
            risk_score=0.0,
            position_size_pct=0.0
        )
        
        # Calculate risk metrics
        validation.risk_metrics = self._calculate_risk_metrics(plan, market_data)
        
        # Structure validation
        self._validate_structure(plan, validation)
        
        # Strategy-specific validation
        self._validate_strategy_specific(plan, validation)
        
        # Risk-based validation
        self._validate_risk_limits(plan, validation, netliq)
        
        # Market condition validation
        self._validate_market_conditions(plan, validation, market_data)
        
        # Portfolio impact validation
        if portfolio:
            self._validate_portfolio_impact(plan, validation, portfolio)
        
        # Liquidity validation
        self._validate_liquidity(plan, validation)
        
        # Stress testing
        validation.stress_test_results = self._perform_stress_tests(plan, validation.risk_metrics)
        
        # Generate recommendations
        self._generate_recommendations(plan, validation)
        
        # Calculate final risk score and approval status
        self._finalize_validation(validation)
        
        return validation
    
    def _calculate_risk_metrics(self, plan: Plan, market_data: Optional[Dict] = None) -> RiskMetrics:
        """Calculate comprehensive risk metrics."""
        metrics = RiskMetrics()
        
        # Basic P&L calculations
        if plan.est_credit:
            metrics.max_profit = plan.est_credit * 100 * plan.params.get("contracts", 1)
        elif plan.est_debit:
            metrics.max_profit = float('inf')  # Unlimited for debit strategies
        
        if plan.max_loss and plan.max_loss != float('inf'):
            metrics.max_loss = plan.max_loss
        
        # Calculate breakeven points based on strategy
        metrics.breakeven_points = self._calculate_breakevens(plan)
        
        # Estimate probability of profit (simplified)
        metrics.probability_of_profit = self._estimate_pop(plan, market_data)
        
        # Risk/reward ratio
        if metrics.max_loss > 0 and metrics.max_profit != float('inf'):
            metrics.risk_reward_ratio = metrics.max_profit / metrics.max_loss
        
        # Greeks estimation (simplified)
        metrics.delta_exposure = self._estimate_delta(plan)
        metrics.gamma_risk = self._estimate_gamma_risk(plan)
        metrics.theta_decay = self._estimate_theta(plan)
        metrics.vega_exposure = self._estimate_vega(plan)
        
        return metrics
    
    def _calculate_breakevens(self, plan: Plan) -> List[float]:
        """Calculate breakeven points for the strategy."""
        breakevens = []
        
        if plan.strategy == "iron_condor":
            # Simplified: short strikes +/- net credit
            calls = [l for l in plan.legs if "call" in l.kind]
            puts = [l for l in plan.legs if "put" in l.kind]
            
            if calls and puts:
                short_call = next((l for l in calls if "short" in l.kind), None)
                short_put = next((l for l in puts if "short" in l.kind), None)
                
                if short_call and short_put and plan.est_credit:
                    breakevens.extend([
                        short_put.strike + plan.est_credit,
                        short_call.strike - plan.est_credit
                    ])
        
        elif plan.strategy in ["put_credit_spread", "call_credit_spread"]:
            short_leg = next((l for l in plan.legs if "short" in l.kind), None)
            if short_leg and plan.est_credit:
                if "put" in plan.strategy:
                    breakevens.append(short_leg.strike - plan.est_credit)
                else:
                    breakevens.append(short_leg.strike + plan.est_credit)
        
        return breakevens
    
    def _estimate_pop(self, plan: Plan, market_data: Optional[Dict] = None) -> float:
        """Estimate probability of profit (simplified model)."""
        base_pop = 0.50  # Base 50% chance
        
        # Adjust based on strategy
        strategy_adjustments = {
            "iron_condor": 0.15,  # Neutral strategies favor time decay
            "put_credit_spread": 0.10,  # Bullish bias in markets
            "call_credit_spread": -0.05,  # Bearish harder in bull markets
            "covered_call": 0.20,  # Conservative strategy
            "protective_put": 0.25,  # Defensive strategy
            "long_straddle": -0.15,  # Requires big moves
        }
        
        adjustment = strategy_adjustments.get(plan.strategy, 0.0)
        
        # Adjust based on DTE
        if plan.dte < 7:
            adjustment -= 0.10  # Short-term has higher risk
        elif plan.dte > 45:
            adjustment -= 0.05  # Long-term has time risk
        
        # Adjust based on market conditions
        if market_data:
            vol_regime = market_data.get("volatility_regime", "normal")
            if vol_regime == "high":
                adjustment -= 0.05
            elif vol_regime == "low":
                adjustment += 0.05
        
        return max(0.0, min(1.0, base_pop + adjustment))
    
    def _estimate_delta(self, plan: Plan) -> float:
        """Estimate net delta exposure."""
        delta = 0.0
        
        for leg in plan.legs:
            # Simplified delta estimation
            leg_delta = 0.0
            
            if "call" in leg.kind:
                leg_delta = 0.5 if "short" in leg.kind else -0.5
            elif "put" in leg.kind:
                leg_delta = -0.5 if "short" in leg.kind else 0.5
            
            delta += leg_delta * leg.qty
        
        return delta
    
    def _estimate_gamma_risk(self, plan: Plan) -> float:
        """Estimate gamma risk score (0-10)."""
        gamma_risk = 0.0
        
        # Higher gamma risk for shorter DTE
        if plan.dte < 7:
            gamma_risk += 4.0
        elif plan.dte < 14:
            gamma_risk += 2.0
        elif plan.dte < 30:
            gamma_risk += 1.0
        
        # Higher gamma risk for ATM strategies
        # (simplified - would need current price)
        if plan.strategy in ["iron_condor", "short_straddle"]:
            gamma_risk += 2.0
        
        # Symbol-specific gamma risk
        if plan.symbol in self.high_vol_symbols:
            gamma_risk += 1.5
        
        return min(gamma_risk, 10.0)
    
    def _estimate_theta(self, plan: Plan) -> float:
        """Estimate daily theta decay."""
        # Simplified theta estimation
        if plan.est_credit:
            return plan.est_credit / plan.dte  # Credit per day
        return 0.0
    
    def _estimate_vega(self, plan: Plan) -> float:
        """Estimate vega exposure."""
        # Simplified vega estimation
        vega = 0.0
        
        for leg in plan.legs:
            if "short" in leg.kind:
                vega -= 1.0  # Short options have negative vega
            else:
                vega += 1.0  # Long options have positive vega
        
        return vega
    
    def _validate_structure(self, plan: Plan, validation: EnhancedValidation):
        """Validate basic structure."""
        if not plan.legs:
            validation.errors.append(ValidationIssue(
                category=ValidationCategory.STRUCTURE,
                severity=RiskSeverity.CRITICAL,
                message="Plan has no option legs",
                recommendation="Add option legs to create a valid strategy"
            ))
        
        # Check for valid strikes
        for i, leg in enumerate(plan.legs):
            if leg.strike <= 0:
                validation.errors.append(ValidationIssue(
                    category=ValidationCategory.STRUCTURE,
                    severity=RiskSeverity.HIGH,
                    message=f"Leg {i+1} has invalid strike price: {leg.strike}",
                    recommendation="Ensure all strikes are positive values"
                ))
            
            if leg.qty == 0:
                validation.warnings.append(ValidationIssue(
                    category=ValidationCategory.STRUCTURE,
                    severity=RiskSeverity.MEDIUM,
                    message=f"Leg {i+1} has zero quantity",
                    recommendation="Check if zero quantity is intended"
                ))
    
    def _validate_strategy_specific(self, plan: Plan, validation: EnhancedValidation):
        """Strategy-specific validation rules."""
        
        if plan.strategy == "iron_condor":
            self._validate_iron_condor(plan, validation)
        elif plan.strategy in ["put_credit_spread", "call_credit_spread"]:
            self._validate_credit_spread(plan, validation)
        elif plan.strategy == "covered_call":
            self._validate_covered_call(plan, validation)
        elif plan.strategy == "protective_put":
            self._validate_protective_put(plan, validation)
        elif plan.strategy in ["long_straddle", "short_straddle"]:
            self._validate_straddle(plan, validation)
    
    def _validate_iron_condor(self, plan: Plan, validation: EnhancedValidation):
        """Validate iron condor specific rules."""
        if len(plan.legs) != 4:
            validation.errors.append(ValidationIssue(
                category=ValidationCategory.STRATEGY,
                severity=RiskSeverity.HIGH,
                message=f"Iron condor should have 4 legs, found {len(plan.legs)}",
                recommendation="Ensure iron condor has short call, long call, short put, long put"
            ))
            return
        
        # Check wing symmetry
        calls = [l for l in plan.legs if "call" in l.kind]
        puts = [l for l in plan.legs if "put" in l.kind]
        
        if len(calls) != 2 or len(puts) != 2:
            validation.errors.append(ValidationIssue(
                category=ValidationCategory.STRATEGY,
                severity=RiskSeverity.HIGH,
                message="Iron condor must have 2 calls and 2 puts",
                recommendation="Check leg configuration"
            ))
    
    def _validate_credit_spread(self, plan: Plan, validation: EnhancedValidation):
        """Validate credit spread rules."""
        if len(plan.legs) != 2:
            validation.errors.append(ValidationIssue(
                category=ValidationCategory.STRATEGY,
                severity=RiskSeverity.HIGH,
                message=f"Credit spread should have 2 legs, found {len(plan.legs)}",
                recommendation="Credit spreads require exactly 2 option legs"
            ))
        
        # Check credit amount
        if plan.est_credit and plan.est_credit < self.risk_limits["min_credit_amount"]:
            validation.warnings.append(ValidationIssue(
                category=ValidationCategory.STRATEGY,
                severity=RiskSeverity.MEDIUM,
                message=f"Low credit amount: ${plan.est_credit:.2f}",
                recommendation="Consider wider spreads for better risk/reward",
                impact="Poor risk/reward ratio"
            ))
    
    def _validate_covered_call(self, plan: Plan, validation: EnhancedValidation):
        """Validate covered call rules."""
        if len(plan.legs) != 1:
            validation.warnings.append(ValidationIssue(
                category=ValidationCategory.STRATEGY,
                severity=RiskSeverity.LOW,
                message="Covered call shows only option leg",
                recommendation="Ensure you own 100 shares of underlying stock",
                impact="Strategy requires stock ownership"
            ))
    
    def _validate_protective_put(self, plan: Plan, validation: EnhancedValidation):
        """Validate protective put rules."""
        if len(plan.legs) != 1:
            validation.warnings.append(ValidationIssue(
                category=ValidationCategory.STRATEGY,
                severity=RiskSeverity.LOW,
                message="Protective put shows only option leg",
                recommendation="Ensure you own 100 shares of underlying stock",
                impact="Strategy requires stock ownership"
            ))
    
    def _validate_straddle(self, plan: Plan, validation: EnhancedValidation):
        """Validate straddle rules."""
        if len(plan.legs) != 2:
            validation.errors.append(ValidationIssue(
                category=ValidationCategory.STRATEGY,
                severity=RiskSeverity.HIGH,
                message=f"Straddle should have 2 legs, found {len(plan.legs)}",
                recommendation="Straddles require call and put at same strike"
            ))
    
    def _validate_risk_limits(self, plan: Plan, validation: EnhancedValidation, netliq: float):
        """Validate against risk limits."""
        
        # Calculate position size
        defined_risk = validation.risk_metrics.max_loss if validation.risk_metrics else 0.0
        if defined_risk == 0.0:
            defined_risk = netliq * 0.05  # Assume 5% for undefined risk
        
        validation.position_size_pct = defined_risk / netliq if netliq > 0 else 0.0
        
        # Check position size limits
        max_risk_pct = self.risk_limits["max_portfolio_risk_per_trade"]
        if validation.position_size_pct > max_risk_pct:
            validation.errors.append(ValidationIssue(
                category=ValidationCategory.RISK,
                severity=RiskSeverity.CRITICAL,
                message=f"Position size {validation.position_size_pct:.1%} exceeds limit {max_risk_pct:.1%}",
                recommendation=f"Reduce position size to ${max_risk_pct * netliq:,.0f} or less",
                impact="Excessive portfolio risk concentration"
            ))
        
        # Check probability of profit
        if validation.risk_metrics and validation.risk_metrics.probability_of_profit < self.risk_limits["min_probability_of_profit"]:
            validation.warnings.append(ValidationIssue(
                category=ValidationCategory.RISK,
                severity=RiskSeverity.MEDIUM,
                message=f"Low probability of profit: {validation.risk_metrics.probability_of_profit:.1%}",
                recommendation="Consider more conservative strategies",
                impact="Higher likelihood of loss"
            ))
        
        # Check gamma risk
        if validation.risk_metrics and validation.risk_metrics.gamma_risk > self.risk_limits["max_gamma_risk_score"]:
            validation.warnings.append(ValidationIssue(
                category=ValidationCategory.RISK,
                severity=RiskSeverity.HIGH,
                message=f"High gamma risk: {validation.risk_metrics.gamma_risk:.1f}/10",
                recommendation="Consider longer DTE or different strikes",
                impact="High sensitivity to price movements"
            ))
    
    def _validate_market_conditions(self, plan: Plan, validation: EnhancedValidation, market_data: Optional[Dict]):
        """Validate against current market conditions."""
        
        # High volatility warnings
        if plan.symbol in self.high_vol_symbols:
            validation.warnings.append(ValidationIssue(
                category=ValidationCategory.MARKET,
                severity=RiskSeverity.MEDIUM,
                message=f"{plan.symbol} is a high volatility symbol",
                recommendation="Exercise extra caution and consider smaller position sizes",
                impact="Higher risk due to volatility"
            ))
        
        # Earnings proximity
        if plan.symbol in self.earnings_prone and plan.dte < 30:
            validation.warnings.append(ValidationIssue(
                category=ValidationCategory.MARKET,
                severity=RiskSeverity.MEDIUM,
                message=f"{plan.symbol} may have upcoming earnings within strategy timeframe",
                recommendation="Check earnings calendar and consider longer DTE",
                impact="Earnings can cause significant price movements"
            ))
        
        # DTE validation
        if plan.dte < self.risk_limits["min_days_to_expiry"]:
            validation.errors.append(ValidationIssue(
                category=ValidationCategory.MARKET,
                severity=RiskSeverity.HIGH,
                message=f"DTE {plan.dte} is too short (minimum: {self.risk_limits['min_days_to_expiry']})",
                recommendation="Use longer expiration dates",
                impact="Extreme gamma risk and limited adjustment opportunities"
            ))
    
    def _validate_liquidity(self, plan: Plan, validation: EnhancedValidation):
        """Validate liquidity considerations."""
        
        if plan.symbol not in self.liquid_symbols:
            validation.warnings.append(ValidationIssue(
                category=ValidationCategory.LIQUIDITY,
                severity=RiskSeverity.MEDIUM,
                message=f"{plan.symbol} may have lower options liquidity",
                recommendation="Check bid/ask spreads before execution",
                impact="Wider spreads may increase trading costs"
            ))
    
    def _validate_portfolio_impact(self, plan: Plan, validation: EnhancedValidation, portfolio: Dict):
        """Validate impact on existing portfolio."""
        
        # Symbol concentration
        existing_exposure = portfolio.get("symbol_exposure", {}).get(plan.symbol, 0.0)
        total_exposure = existing_exposure + validation.position_size_pct
        
        if total_exposure > self.risk_limits["max_symbol_allocation"]:
            validation.warnings.append(ValidationIssue(
                category=ValidationCategory.PORTFOLIO,
                severity=RiskSeverity.HIGH,
                message=f"Total {plan.symbol} exposure would be {total_exposure:.1%}",
                recommendation="Consider diversification across multiple symbols",
                impact="Concentration risk in single symbol"
            ))
    
    def _perform_stress_tests(self, plan: Plan, risk_metrics: Optional[RiskMetrics]) -> Dict[str, float]:
        """Perform stress tests on the strategy."""
        stress_results = {}
        
        if not risk_metrics or not risk_metrics.breakeven_points:
            return stress_results
        
        # Simplified stress testing
        for scenario, move in self.stress_scenarios.items():
            if scenario == "market_crash":
                # Estimate P&L at various price levels
                stress_results[scenario] = self._estimate_stress_pnl(plan, move)
            elif scenario == "volatility_spike":
                # Estimate vega impact
                stress_results[scenario] = risk_metrics.vega_exposure * move
        
        return stress_results
    
    def _estimate_stress_pnl(self, plan: Plan, price_move: float) -> float:
        """Estimate P&L under stress scenario."""
        # Simplified stress P&L calculation
        # In practice, would use options pricing models
        
        if plan.strategy in ["iron_condor", "put_credit_spread", "call_credit_spread"]:
            # Credit strategies benefit from small moves, hurt by large moves
            if abs(price_move) > 0.05:  # >5% move
                return -(plan.est_credit or 0.0) * 100  # Likely max loss
            else:
                return (plan.est_credit or 0.0) * 50  # Partial profit
        
        return 0.0
    
    def _generate_recommendations(self, plan: Plan, validation: EnhancedValidation):
        """Generate actionable recommendations."""
        
        recommendations = []
        
        # Based on risk score
        if validation.risk_score > 7.0:
            recommendations.append("Consider reducing position size or choosing more conservative strategies")
        
        # Based on strategy
        if plan.strategy == "iron_condor" and plan.dte < 21:
            recommendations.append("Consider 21+ DTE for iron condors to reduce gamma risk")
        
        # Based on market conditions
        if plan.symbol in self.high_vol_symbols:
            recommendations.append(f"For {plan.symbol}, consider smaller positions due to high volatility")
        
        # Based on validation issues
        high_severity_issues = [
            issue for issue in validation.warnings + validation.errors
            if issue.severity in [RiskSeverity.HIGH, RiskSeverity.CRITICAL]
        ]
        
        if high_severity_issues:
            recommendations.append("Address high-severity validation issues before proceeding")
        
        validation.recommendations = recommendations
    
    def _finalize_validation(self, validation: EnhancedValidation):
        """Calculate final risk score and approval status."""
        
        # Base risk score
        risk_score = 0.0
        
        # Add points for each issue
        for issue in validation.errors:
            if issue.severity == RiskSeverity.CRITICAL:
                risk_score += 4.0
            elif issue.severity == RiskSeverity.HIGH:
                risk_score += 3.0
            elif issue.severity == RiskSeverity.MEDIUM:
                risk_score += 2.0
            else:
                risk_score += 1.0
        
        for issue in validation.warnings:
            if issue.severity == RiskSeverity.HIGH:
                risk_score += 2.0
            elif issue.severity == RiskSeverity.MEDIUM:
                risk_score += 1.0
            else:
                risk_score += 0.5
        
        # Add risk metrics contribution
        if validation.risk_metrics:
            risk_score += validation.risk_metrics.gamma_risk * 0.2
            
            if validation.risk_metrics.probability_of_profit < 0.6:
                risk_score += 1.0
        
        # Position size contribution
        if validation.position_size_pct > 0.015:  # >1.5%
            risk_score += (validation.position_size_pct - 0.015) * 100
        
        validation.risk_score = min(risk_score, 10.0)
        
        # Determine approval status
        validation.ok = (
            len(validation.errors) == 0 and
            validation.risk_score <= self.risk_limits["max_overall_risk_score"]
        )

# Enhanced validation function for backward compatibility
def risk_check(plan: Plan, netliq: float = 100000.0, max_pos_pct: float = 0.02) -> EnhancedValidation:
    """Enhanced risk check function."""
    validator = EnhancedRiskValidator()
    return validator.validate_plan(plan, netliq=netliq)

# Create global validator instance
_global_validator = EnhancedRiskValidator()

def validate_enhanced(plan: Plan, **kwargs) -> EnhancedValidation:
    """Validate with enhanced features."""
    return _global_validator.validate_plan(plan, **kwargs)