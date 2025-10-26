"""
Validator - Risk Checks and Safety Validation for Trading Plans
Comprehensive validation of trading plans before execution.
"""

from typing import Dict, Any, List
from ..logic.risk_manager import RiskManager, PortfolioSnapshot

class TradingPlanValidator:
    """Validates trading plans against risk rules and business logic."""
    
    def __init__(self, risk_manager: RiskManager = None):
        """
        Initialize validator with risk manager.
        
        Args:
            risk_manager: Risk manager instance for portfolio-level checks
        """
        self.risk_manager = risk_manager or RiskManager()
        
        # Validation rules configuration
        self.max_legs_per_strategy = 6
        self.max_contracts_per_trade = 50
        self.min_dte = 1
        self.max_dte = 365
        
    def validate_plan(self, plan: Dict[str, Any], portfolio: PortfolioSnapshot = None) -> List[str]:
        """
        Comprehensive validation of a trading plan.
        
        Args:
            plan: Trading plan to validate
            portfolio: Current portfolio for context (optional)
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Basic structure validation
        errors.extend(self._validate_structure(plan))
        
        # Strategy-specific validation
        errors.extend(self._validate_strategy_logic(plan))
        
        # Risk management validation
        errors.extend(self._validate_risk_limits(plan))
        
        # Portfolio-level validation (if portfolio provided)
        if portfolio:
            errors.extend(self._validate_portfolio_impact(plan, portfolio))
        
        # Market data validation
        errors.extend(self._validate_market_data(plan))
        
        # Position sizing validation
        errors.extend(self._validate_sizing(plan))
        
        return errors
    
    def _validate_structure(self, plan: Dict[str, Any]) -> List[str]:
        """Validate basic plan structure."""
        errors = []
        
        # Required fields
        required_fields = ["request_id", "symbol", "strategy", "expiry", "legs", "sizing"]
        for field in required_fields:
            if field not in plan:
                errors.append(f"Missing required field: {field}")
        
        # Validate legs structure
        if "legs" in plan:
            legs = plan["legs"]
            if not isinstance(legs, list) or len(legs) == 0:
                errors.append("Plan must have at least one leg")
            else:
                for i, leg in enumerate(legs):
                    leg_errors = self._validate_leg_structure(leg, i)
                    errors.extend(leg_errors)
        
        return errors
    
    def _validate_leg_structure(self, leg: Dict[str, Any], index: int) -> List[str]:
        """Validate individual leg structure."""
        errors = []
        
        required_leg_fields = ["side", "type", "strike", "qty"]
        for field in required_leg_fields:
            if field not in leg:
                errors.append(f"Leg {index}: Missing required field '{field}'")
        
        # Validate field values
        if "side" in leg and leg["side"] not in ["buy", "sell"]:
            errors.append(f"Leg {index}: Invalid side '{leg['side']}', must be 'buy' or 'sell'")
        
        if "type" in leg and leg["type"] not in ["call", "put"]:
            errors.append(f"Leg {index}: Invalid type '{leg['type']}', must be 'call' or 'put'")
        
        if "strike" in leg:
            try:
                strike = float(leg["strike"])
                if strike <= 0:
                    errors.append(f"Leg {index}: Strike price must be positive")
            except (ValueError, TypeError):
                errors.append(f"Leg {index}: Invalid strike price")
        
        if "qty" in leg:
            try:
                qty = int(leg["qty"])
                if qty <= 0:
                    errors.append(f"Leg {index}: Quantity must be positive")
            except (ValueError, TypeError):
                errors.append(f"Leg {index}: Invalid quantity")
        
        return errors
    
    def _validate_strategy_logic(self, plan: Dict[str, Any]) -> List[str]:
        """Validate strategy-specific logic."""
        errors = []
        
        strategy = plan.get("strategy", "")
        legs = plan.get("legs", [])
        
        # Check leg count limits
        if len(legs) > self.max_legs_per_strategy:
            errors.append(f"Strategy has {len(legs)} legs, maximum allowed is {self.max_legs_per_strategy}")
        
        # Strategy-specific validations
        if strategy == "iron_condor":
            errors.extend(self._validate_iron_condor(legs))
        elif strategy == "put_credit_spread":
            errors.extend(self._validate_put_credit_spread(legs))
        elif strategy == "covered_call":
            errors.extend(self._validate_covered_call(legs))
        elif strategy == "long_straddle":
            errors.extend(self._validate_long_straddle(legs))
        
        return errors
    
    def _validate_iron_condor(self, legs: List[Dict[str, Any]]) -> List[str]:
        """Validate iron condor strategy structure."""
        errors = []
        
        if len(legs) != 4:
            errors.append("Iron condor must have exactly 4 legs")
            return errors
        
        # Check for proper iron condor structure
        calls = [leg for leg in legs if leg.get("type") == "call"]
        puts = [leg for leg in legs if leg.get("type") == "put"]
        
        if len(calls) != 2 or len(puts) != 2:
            errors.append("Iron condor must have 2 calls and 2 puts")
        
        # Check for one buy and one sell of each type
        call_sides = [leg.get("side") for leg in calls]
        put_sides = [leg.get("side") for leg in puts]
        
        if "buy" not in call_sides or "sell" not in call_sides:
            errors.append("Iron condor must buy and sell calls")
        
        if "buy" not in put_sides or "sell" not in put_sides:
            errors.append("Iron condor must buy and sell puts")
        
        return errors
    
    def _validate_put_credit_spread(self, legs: List[Dict[str, Any]]) -> List[str]:
        """Validate put credit spread structure."""
        errors = []
        
        if len(legs) != 2:
            errors.append("Put credit spread must have exactly 2 legs")
            return errors
        
        # Both legs must be puts
        if not all(leg.get("type") == "put" for leg in legs):
            errors.append("Put credit spread must have only put options")
        
        # One buy, one sell
        sides = [leg.get("side") for leg in legs]
        if "buy" not in sides or "sell" not in sides:
            errors.append("Put credit spread must have one buy and one sell")
        
        return errors
    
    def _validate_covered_call(self, legs: List[Dict[str, Any]]) -> List[str]:
        """Validate covered call structure."""
        errors = []
        
        if len(legs) != 1:
            errors.append("Covered call must have exactly 1 option leg (assumes stock ownership)")
            return errors
        
        leg = legs[0]
        if leg.get("type") != "call":
            errors.append("Covered call must sell a call option")
        
        if leg.get("side") != "sell":
            errors.append("Covered call must sell the call option")
        
        return errors
    
    def _validate_long_straddle(self, legs: List[Dict[str, Any]]) -> List[str]:
        """Validate long straddle structure."""
        errors = []
        
        if len(legs) != 2:
            errors.append("Long straddle must have exactly 2 legs")
            return errors
        
        # One call, one put
        types = [leg.get("type") for leg in legs]
        if "call" not in types or "put" not in types:
            errors.append("Long straddle must have one call and one put")
        
        # Both must be buys
        if not all(leg.get("side") == "buy" for leg in legs):
            errors.append("Long straddle must buy both options")
        
        # Same strike price
        strikes = [leg.get("strike") for leg in legs]
        if len(set(strikes)) > 1:
            errors.append("Long straddle must have same strike price for both legs")
        
        return errors
    
    def _validate_risk_limits(self, plan: Dict[str, Any]) -> List[str]:
        """Validate against risk limits."""
        errors = []
        
        # Check portfolio risk limit
        max_risk = plan.get("max_risk", 0)
        if max_risk > 0.1:  # 10% portfolio risk limit
            errors.append(f"Portfolio risk {max_risk:.1%} exceeds 10% limit")
        
        # Check defined risk requirement
        risk_tags = plan.get("risk_tags", [])
        if "undefined_risk" in risk_tags:
            # Check if undefined risk is allowed
            sizing = plan.get("sizing", {})
            if sizing.get("risk_defined_only", True):
                errors.append("Undefined risk strategy not allowed per constraints")
        
        # Check position size limits
        sizing = plan.get("sizing", {})
        contracts = sizing.get("contracts", 0)
        if contracts > self.max_contracts_per_trade:
            errors.append(f"Position size {contracts} contracts exceeds limit of {self.max_contracts_per_trade}")
        
        return errors
    
    def _validate_portfolio_impact(self, plan: Dict[str, Any], portfolio: PortfolioSnapshot) -> List[str]:
        """Validate plan's impact on portfolio using risk manager."""
        errors = []
        
        try:
            # Use existing risk manager validation
            from ..strategies.base import OrderIntent  # Import existing order type
            
            # Convert plan to order intent for validation
            order_intent = self._plan_to_order_intent(plan)
            
            # Use risk manager validation
            is_approved, violations = self.risk_manager.validate_order(order_intent, portfolio)
            
            if not is_approved:
                errors.extend([f"Risk manager violation: {v}" for v in violations])
        
        except Exception as e:
            errors.append(f"Portfolio validation error: {str(e)}")
        
        return errors
    
    def _plan_to_order_intent(self, plan: Dict[str, Any]) -> 'OrderIntent':
        """Convert trading plan to order intent for risk validation."""
        # Simplified conversion - in practice this would be more sophisticated
        from ..strategies.base import OrderIntent
        
        symbol = plan.get("symbol", "UNKNOWN")
        max_risk = plan.get("sizing", {}).get("max_risk_dollars", 1000)
        
        return OrderIntent(
            symbol=symbol,
            side="sell",  # Simplified
            qty=1,
            type="complex",
            meta={
                "strategy": plan.get("strategy", "unknown"),
                "max_risk": max_risk,
                "plan_id": plan.get("request_id")
            }
        )
    
    def _validate_market_data(self, plan: Dict[str, Any]) -> List[str]:
        """Validate market data and timing."""
        errors = []
        
        # Validate expiry date
        expiry = plan.get("expiry")
        if expiry:
            try:
                from datetime import datetime
                expiry_date = datetime.strptime(expiry, "%Y-%m-%d")
                today = datetime.now()
                
                dte = (expiry_date - today).days
                
                if dte < self.min_dte:
                    errors.append(f"Expiry too soon: {dte} days (minimum {self.min_dte})")
                elif dte > self.max_dte:
                    errors.append(f"Expiry too far: {dte} days (maximum {self.max_dte})")
            
            except ValueError:
                errors.append(f"Invalid expiry date format: {expiry}")
        
        # Validate strikes vs current price
        market_ctx = plan.get("market_context", {})
        current_price = market_ctx.get("current_price")
        
        if current_price:
            legs = plan.get("legs", [])
            for i, leg in enumerate(legs):
                strike = leg.get("strike", 0)
                if strike > 0:
                    # Check for reasonable strike prices (within 50% of current)
                    if strike < current_price * 0.5 or strike > current_price * 1.5:
                        errors.append(f"Leg {i}: Strike {strike} seems unreasonable vs current price {current_price}")
        
        return errors
    
    def _validate_sizing(self, plan: Dict[str, Any]) -> List[str]:
        """Validate position sizing logic."""
        errors = []
        
        sizing = plan.get("sizing", {})
        
        # Check for required sizing fields
        if "max_risk_per_trade" not in sizing:
            errors.append("Missing max_risk_per_trade in sizing")
        
        if "contracts" not in sizing:
            errors.append("Missing contracts in sizing")
        
        # Validate sizing logic
        max_risk_pct = sizing.get("max_risk_per_trade", 0)
        contracts = sizing.get("contracts", 0)
        risk_per_contract = sizing.get("risk_per_contract", 0)
        
        if max_risk_pct > 0 and contracts > 0 and risk_per_contract > 0:
            # Check if total risk makes sense
            total_risk = contracts * risk_per_contract
            portfolio_value = plan.get("market_context", {}).get("portfolio_value", 100000)
            actual_risk_pct = total_risk / portfolio_value
            
            if actual_risk_pct > max_risk_pct * 1.1:  # 10% tolerance
                errors.append(f"Actual risk {actual_risk_pct:.1%} exceeds target {max_risk_pct:.1%}")
        
        return errors
    
    def check_defined_risk(self, plan: Dict[str, Any]) -> List[str]:
        """Check if strategy has defined risk characteristics."""
        errors = []
        
        risk_tags = plan.get("risk_tags", [])
        if "undefined_risk" in risk_tags:
            errors.append("Strategy has undefined risk - requires additional approval")
        
        return errors


# Convenience function for backward compatibility
def validate_plan(plan: Dict[str, Any], portfolio: PortfolioSnapshot = None) -> List[str]:
    """
    Validate a trading plan.
    
    Args:
        plan: Trading plan to validate
        portfolio: Optional portfolio context
        
    Returns:
        List of validation errors
    """
    validator = TradingPlanValidator()
    return validator.validate_plan(plan, portfolio)