"""
Risk Gates - Phase 3 Implementation
Hard risk limits that cannot be bypassed by LLM output.
These are enforced at the system level before any trade execution.
"""
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

logger = logging.getLogger(__name__)

class RiskViolationType(Enum):
    """Types of risk violations"""
    CAPITAL_LIMIT = "capital_limit"
    DAILY_LOSS = "daily_loss"
    DRAWDOWN = "drawdown"
    POSITION_SIZE = "position_size"
    DELTA_EXPOSURE = "delta_exposure"
    VEGA_EXPOSURE = "vega_exposure"
    THETA_EXPOSURE = "theta_exposure"
    CONCENTRATION = "concentration"
    MARGIN_REQUIREMENT = "margin_requirement"
    LIQUIDITY = "liquidity"
    EVENT_RESTRICTION = "event_restriction"

@dataclass
class RiskViolation:
    """Risk violation details"""
    violation_type: RiskViolationType
    current_value: float
    limit_value: float
    severity: str  # "warning", "error", "critical"
    message: str
    suggested_action: str

@dataclass
class PortfolioMetrics:
    """Current portfolio risk metrics"""
    total_equity: float
    available_cash: float
    total_delta: float
    total_gamma: float
    total_theta: float
    total_vega: float
    daily_pnl: float
    unrealized_pnl: float
    margin_used: float
    positions_count: int
    max_single_position_size: float

class RiskGate:
    """
    Enforces hard risk limits that cannot be overridden by LLM decisions.
    All trades must pass through these gates before execution.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.risk_limits = self._load_risk_limits(config_path)
        self.violation_history: List[RiskViolation] = []
        
    def _load_risk_limits(self, config_path: Optional[str]) -> Dict:
        """Load risk limits from configuration"""
        # Default risk limits - these should be configurable
        default_limits = {
            # Capital and Loss Limits
            "max_capital_at_risk_per_trade_pct": 2.0,  # 2% per trade
            "max_capital_at_risk_portfolio_pct": 10.0,  # 10% total portfolio
            "max_daily_loss_pct": 5.0,  # 5% daily loss limit
            "max_trailing_drawdown_pct": 15.0,  # 15% drawdown from peak
            "max_margin_utilization_pct": 50.0,  # 50% margin utilization
            
            # Position Limits
            "max_single_position_size": 50,  # Max 50 contracts
            "max_positions_per_symbol": 3,  # Max 3 positions per underlying
            "max_total_positions": 20,  # Max 20 open positions
            
            # Greeks Exposure Limits
            "max_portfolio_delta": 500,  # Max 500 delta exposure
            "max_portfolio_gamma": 100,  # Max 100 gamma exposure
            "max_portfolio_theta": -50,  # Max -50 theta exposure (time decay)
            "max_portfolio_vega": 1000,  # Max 1000 vega exposure
            
            # Concentration Limits
            "max_single_symbol_allocation_pct": 15.0,  # 15% per symbol
            "max_sector_allocation_pct": 30.0,  # 30% per sector
            
            # Liquidity Requirements
            "min_option_volume": 100,  # Minimum 100 daily volume
            "min_open_interest": 500,  # Minimum 500 open interest
            "max_bid_ask_spread_pct": 10.0,  # Max 10% bid-ask spread
            
            # Event Restrictions
            "no_trades_before_earnings_days": 2,  # No trades 2 days before earnings
            "no_trades_before_expiration_days": 3,  # No new trades 3 days before expiration
            "blackout_symbols": [],  # Symbols to avoid
            
            # Emergency Limits
            "circuit_breaker_loss_pct": 25.0,  # Emergency stop at 25% loss
            "max_consecutive_losses": 5,  # Stop after 5 consecutive losses
        }
        
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    custom_limits = json.load(f)
                default_limits.update(custom_limits)
            except Exception as e:
                logger.warning(f"Could not load custom risk limits: {e}")
        
        return default_limits
    
    def validate_trade(self, 
                      trade: Dict, 
                      portfolio_metrics: PortfolioMetrics,
                      account_equity: float) -> Tuple[bool, List[RiskViolation]]:
        """
        Validate a trade against all risk gates.
        
        Args:
            trade: Executable trade dictionary
            portfolio_metrics: Current portfolio metrics
            account_equity: Total account equity
            
        Returns:
            (is_valid, violations) - True if trade passes all gates
        """
        violations = []
        
        # 1. Capital at Risk Checks
        violations.extend(self._check_capital_limits(trade, portfolio_metrics, account_equity))
        
        # 2. Daily Loss Limits
        violations.extend(self._check_daily_loss_limits(portfolio_metrics, account_equity))
        
        # 3. Position Size Limits
        violations.extend(self._check_position_limits(trade, portfolio_metrics))
        
        # 4. Greeks Exposure Limits
        violations.extend(self._check_greeks_limits(trade, portfolio_metrics))
        
        # 5. Concentration Limits
        violations.extend(self._check_concentration_limits(trade, portfolio_metrics, account_equity))
        
        # 6. Liquidity Requirements
        violations.extend(self._check_liquidity_requirements(trade))
        
        # 7. Event Restrictions
        violations.extend(self._check_event_restrictions(trade))
        
        # 8. Margin Requirements
        violations.extend(self._check_margin_requirements(trade, portfolio_metrics, account_equity))
        
        # Filter critical violations
        critical_violations = [v for v in violations if v.severity in ["error", "critical"]]
        
        # Log violations
        if violations:
            logger.warning(f"Risk violations found: {len(violations)} total, {len(critical_violations)} critical")
            for violation in violations:
                logger.warning(f"  {violation.violation_type.value}: {violation.message}")
        
        self.violation_history.extend(violations)
        
        return len(critical_violations) == 0, violations
    
    def _check_capital_limits(self, 
                             trade: Dict, 
                             portfolio: PortfolioMetrics, 
                             account_equity: float) -> List[RiskViolation]:
        """Check capital at risk limits"""
        violations = []
        
        # Trade-specific capital at risk
        trade_max_loss = trade.get("risk_constraints", {}).get("max_loss", 0)
        trade_risk_pct = (trade_max_loss / account_equity) * 100
        
        if trade_risk_pct > self.risk_limits["max_capital_at_risk_per_trade_pct"]:
            violations.append(RiskViolation(
                violation_type=RiskViolationType.CAPITAL_LIMIT,
                current_value=trade_risk_pct,
                limit_value=self.risk_limits["max_capital_at_risk_per_trade_pct"],
                severity="error",
                message=f"Trade risk {trade_risk_pct:.1f}% exceeds per-trade limit of {self.risk_limits['max_capital_at_risk_per_trade_pct']:.1f}%",
                suggested_action="Reduce position size or select lower-risk strategy"
            ))
        
        # Portfolio-wide capital at risk
        current_portfolio_risk = abs(portfolio.unrealized_pnl)
        total_risk_with_trade = current_portfolio_risk + trade_max_loss
        total_risk_pct = (total_risk_with_trade / account_equity) * 100
        
        if total_risk_pct > self.risk_limits["max_capital_at_risk_portfolio_pct"]:
            violations.append(RiskViolation(
                violation_type=RiskViolationType.CAPITAL_LIMIT,
                current_value=total_risk_pct,
                limit_value=self.risk_limits["max_capital_at_risk_portfolio_pct"],
                severity="error",
                message=f"Total portfolio risk {total_risk_pct:.1f}% exceeds limit of {self.risk_limits['max_capital_at_risk_portfolio_pct']:.1f}%",
                suggested_action="Close existing positions or reduce trade size"
            ))
        
        return violations
    
    def _check_daily_loss_limits(self, 
                                portfolio: PortfolioMetrics, 
                                account_equity: float) -> List[RiskViolation]:
        """Check daily loss limits"""
        violations = []
        
        daily_loss_pct = abs(portfolio.daily_pnl / account_equity) * 100 if portfolio.daily_pnl < 0 else 0
        
        if daily_loss_pct > self.risk_limits["max_daily_loss_pct"]:
            violations.append(RiskViolation(
                violation_type=RiskViolationType.DAILY_LOSS,
                current_value=daily_loss_pct,
                limit_value=self.risk_limits["max_daily_loss_pct"],
                severity="critical",
                message=f"Daily loss {daily_loss_pct:.1f}% exceeds limit of {self.risk_limits['max_daily_loss_pct']:.1f}%",
                suggested_action="Stop trading for the day"
            ))
        
        return violations
    
    def _check_position_limits(self, trade: Dict, portfolio: PortfolioMetrics) -> List[RiskViolation]:
        """Check position size and count limits"""
        violations = []
        
        # Check position size
        trade_position_size = trade.get("position_size", 1)
        if trade_position_size > self.risk_limits["max_single_position_size"]:
            violations.append(RiskViolation(
                violation_type=RiskViolationType.POSITION_SIZE,
                current_value=trade_position_size,
                limit_value=self.risk_limits["max_single_position_size"],
                severity="error",
                message=f"Position size {trade_position_size} exceeds limit of {self.risk_limits['max_single_position_size']}",
                suggested_action="Reduce position size"
            ))
        
        # Check total positions
        if portfolio.positions_count >= self.risk_limits["max_total_positions"]:
            violations.append(RiskViolation(
                violation_type=RiskViolationType.POSITION_SIZE,
                current_value=portfolio.positions_count,
                limit_value=self.risk_limits["max_total_positions"],
                severity="error",
                message=f"Total positions {portfolio.positions_count} at limit of {self.risk_limits['max_total_positions']}",
                suggested_action="Close existing positions before opening new ones"
            ))
        
        return violations
    
    def _check_greeks_limits(self, trade: Dict, portfolio: PortfolioMetrics) -> List[RiskViolation]:
        """Check Greeks exposure limits"""
        violations = []
        
        trade_metrics = trade.get("metrics", {})
        
        # Delta exposure
        new_total_delta = portfolio.total_delta + trade_metrics.get("total_delta", 0)
        if abs(new_total_delta) > self.risk_limits["max_portfolio_delta"]:
            violations.append(RiskViolation(
                violation_type=RiskViolationType.DELTA_EXPOSURE,
                current_value=abs(new_total_delta),
                limit_value=self.risk_limits["max_portfolio_delta"],
                severity="warning",
                message=f"Total delta exposure {new_total_delta:.1f} exceeds limit of ±{self.risk_limits['max_portfolio_delta']}",
                suggested_action="Consider delta-neutral strategies or hedge existing delta"
            ))
        
        # Vega exposure
        new_total_vega = portfolio.total_vega + trade_metrics.get("total_vega", 0)
        if abs(new_total_vega) > self.risk_limits["max_portfolio_vega"]:
            violations.append(RiskViolation(
                violation_type=RiskViolationType.VEGA_EXPOSURE,
                current_value=abs(new_total_vega),
                limit_value=self.risk_limits["max_portfolio_vega"],
                severity="warning",
                message=f"Total vega exposure {new_total_vega:.1f} exceeds limit of ±{self.risk_limits['max_portfolio_vega']}",
                suggested_action="Reduce volatility exposure or hedge vega"
            ))
        
        # Theta exposure (time decay)
        new_total_theta = portfolio.total_theta + trade_metrics.get("total_theta", 0)
        if new_total_theta < self.risk_limits["max_portfolio_theta"]:  # Theta is negative
            violations.append(RiskViolation(
                violation_type=RiskViolationType.THETA_EXPOSURE,
                current_value=new_total_theta,
                limit_value=self.risk_limits["max_portfolio_theta"],
                severity="warning",
                message=f"Total theta exposure {new_total_theta:.1f} exceeds limit of {self.risk_limits['max_portfolio_theta']}",
                suggested_action="Reduce time decay exposure or close short options"
            ))
        
        return violations
    
    def _check_concentration_limits(self, 
                                   trade: Dict, 
                                   portfolio: PortfolioMetrics, 
                                   account_equity: float) -> List[RiskViolation]:
        """Check concentration limits"""
        violations = []
        
        # Single symbol allocation
        symbol = trade.get("symbol", "")
        trade_value = trade.get("risk_constraints", {}).get("max_loss", 0)
        symbol_allocation_pct = (trade_value / account_equity) * 100
        
        if symbol_allocation_pct > self.risk_limits["max_single_symbol_allocation_pct"]:
            violations.append(RiskViolation(
                violation_type=RiskViolationType.CONCENTRATION,
                current_value=symbol_allocation_pct,
                limit_value=self.risk_limits["max_single_symbol_allocation_pct"],
                severity="warning",
                message=f"Symbol {symbol} allocation {symbol_allocation_pct:.1f}% exceeds limit of {self.risk_limits['max_single_symbol_allocation_pct']:.1f}%",
                suggested_action="Diversify across more symbols"
            ))
        
        return violations
    
    def _check_liquidity_requirements(self, trade: Dict) -> List[RiskViolation]:
        """Check liquidity requirements"""
        violations = []
        
        for leg in trade.get("legs", []):
            if leg.get("instrument") in ["put", "call"]:
                volume = leg.get("volume", 0)
                open_interest = leg.get("open_interest", 0)
                bid = leg.get("bid", 0)
                ask = leg.get("ask", 0)
                
                # Volume check
                if volume < self.risk_limits["min_option_volume"]:
                    violations.append(RiskViolation(
                        violation_type=RiskViolationType.LIQUIDITY,
                        current_value=volume,
                        limit_value=self.risk_limits["min_option_volume"],
                        severity="warning",
                        message=f"Option volume {volume} below minimum {self.risk_limits['min_option_volume']}",
                        suggested_action="Choose more liquid options"
                    ))
                
                # Open interest check
                if open_interest < self.risk_limits["min_open_interest"]:
                    violations.append(RiskViolation(
                        violation_type=RiskViolationType.LIQUIDITY,
                        current_value=open_interest,
                        limit_value=self.risk_limits["min_open_interest"],
                        severity="warning",
                        message=f"Open interest {open_interest} below minimum {self.risk_limits['min_open_interest']}",
                        suggested_action="Choose options with higher open interest"
                    ))
                
                # Bid-ask spread check
                if ask > 0 and bid > 0:
                    spread_pct = ((ask - bid) / ((ask + bid) / 2)) * 100
                    if spread_pct > self.risk_limits["max_bid_ask_spread_pct"]:
                        violations.append(RiskViolation(
                            violation_type=RiskViolationType.LIQUIDITY,
                            current_value=spread_pct,
                            limit_value=self.risk_limits["max_bid_ask_spread_pct"],
                            severity="warning",
                            message=f"Bid-ask spread {spread_pct:.1f}% exceeds limit of {self.risk_limits['max_bid_ask_spread_pct']:.1f}%",
                            suggested_action="Choose more liquid options with tighter spreads"
                        ))
        
        return violations
    
    def _check_event_restrictions(self, trade: Dict) -> List[RiskViolation]:
        """Check event-based restrictions"""
        violations = []
        
        symbol = trade.get("symbol", "")
        expiration = trade.get("expiration")
        
        # Check blackout symbols
        if symbol in self.risk_limits["blackout_symbols"]:
            violations.append(RiskViolation(
                violation_type=RiskViolationType.EVENT_RESTRICTION,
                current_value=1,
                limit_value=0,
                severity="error",
                message=f"Symbol {symbol} is on blackout list",
                suggested_action="Choose different symbol"
            ))
        
        # Check expiration proximity
        if expiration:
            days_to_expiration = (expiration - datetime.now()).days
            if days_to_expiration <= self.risk_limits["no_trades_before_expiration_days"]:
                violations.append(RiskViolation(
                    violation_type=RiskViolationType.EVENT_RESTRICTION,
                    current_value=days_to_expiration,
                    limit_value=self.risk_limits["no_trades_before_expiration_days"],
                    severity="warning",
                    message=f"Only {days_to_expiration} days to expiration",
                    suggested_action="Choose longer-term expiration"
                ))
        
        return violations
    
    def _check_margin_requirements(self, 
                                  trade: Dict, 
                                  portfolio: PortfolioMetrics, 
                                  account_equity: float) -> List[RiskViolation]:
        """Check margin requirements"""
        violations = []
        
        trade_margin = trade.get("metrics", {}).get("margin_requirement", 0)
        total_margin = portfolio.margin_used + trade_margin
        margin_utilization_pct = (total_margin / account_equity) * 100
        
        if margin_utilization_pct > self.risk_limits["max_margin_utilization_pct"]:
            violations.append(RiskViolation(
                violation_type=RiskViolationType.MARGIN_REQUIREMENT,
                current_value=margin_utilization_pct,
                limit_value=self.risk_limits["max_margin_utilization_pct"],
                severity="error",
                message=f"Margin utilization {margin_utilization_pct:.1f}% exceeds limit of {self.risk_limits['max_margin_utilization_pct']:.1f}%",
                suggested_action="Reduce position size or close existing positions"
            ))
        
        return violations
    
    def get_risk_summary(self, portfolio: PortfolioMetrics, account_equity: float) -> Dict:
        """Get current risk summary"""
        return {
            "capital_utilization_pct": (abs(portfolio.unrealized_pnl) / account_equity) * 100,
            "margin_utilization_pct": (portfolio.margin_used / account_equity) * 100,
            "daily_pnl_pct": (portfolio.daily_pnl / account_equity) * 100,
            "total_positions": portfolio.positions_count,
            "delta_exposure": portfolio.total_delta,
            "vega_exposure": portfolio.total_vega,
            "theta_exposure": portfolio.total_theta,
            "recent_violations": len([v for v in self.violation_history[-10:] if v.severity in ["error", "critical"]]),
            "risk_score": self._calculate_risk_score(portfolio, account_equity)
        }
    
    def _calculate_risk_score(self, portfolio: PortfolioMetrics, account_equity: float) -> float:
        """Calculate overall risk score (0-100)"""
        score = 0
        
        # Capital utilization (0-30 points)
        capital_util = (abs(portfolio.unrealized_pnl) / account_equity) * 100
        score += min(30, capital_util * 3)
        
        # Position count (0-20 points)
        position_ratio = portfolio.positions_count / self.risk_limits["max_total_positions"]
        score += min(20, position_ratio * 20)
        
        # Greeks exposure (0-30 points)
        delta_ratio = abs(portfolio.total_delta) / self.risk_limits["max_portfolio_delta"]
        vega_ratio = abs(portfolio.total_vega) / self.risk_limits["max_portfolio_vega"]
        score += min(30, max(delta_ratio, vega_ratio) * 30)
        
        # Recent violations (0-20 points)
        recent_violations = len([v for v in self.violation_history[-5:] if v.severity in ["error", "critical"]])
        score += min(20, recent_violations * 4)
        
        return min(100, score)

# Example usage
if __name__ == "__main__":
    # Example portfolio
    portfolio = PortfolioMetrics(
        total_equity=100000,
        available_cash=80000,
        total_delta=150,
        total_gamma=25,
        total_theta=-15,
        total_vega=300,
        daily_pnl=-1500,
        unrealized_pnl=-2500,
        margin_used=15000,
        positions_count=8,
        max_single_position_size=25
    )
    
    # Example trade
    trade = {
        "symbol": "SPY",
        "strategy_type": "iron_condor",
        "position_size": 10,
        "risk_constraints": {"max_loss": 1500},
        "metrics": {
            "total_delta": 5,
            "total_vega": 50,
            "total_theta": -2,
            "margin_requirement": 5000
        },
        "legs": [
            {"instrument": "put", "volume": 500, "open_interest": 1000, "bid": 1.50, "ask": 1.55}
        ]
    }
    
    # Test risk gates
    risk_gate = RiskGate()
    is_valid, violations = risk_gate.validate_trade(trade, portfolio, 100000)
    
    print(f"Trade valid: {is_valid}")
    for violation in violations:
        print(f"  {violation.severity}: {violation.message}")
    
    print(f"\nRisk Summary: {risk_gate.get_risk_summary(portfolio, 100000)}")