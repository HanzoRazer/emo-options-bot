"""
Phase 3 Gates - Risk management and validation gates
Provides risk assessment and trade validation functionality
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from decimal import Decimal
from dataclasses import dataclass

# Import schemas if available
try:
    from schemas import RiskAssessment, RiskViolation, RiskLevel, Portfolio, OptionsOrder
except ImportError:
    # Fallback for development
    RiskAssessment = Dict[str, Any]
    RiskViolation = Dict[str, Any]
    RiskLevel = str
    Portfolio = Dict[str, Any]
    OptionsOrder = Dict[str, Any]


@dataclass
class RiskConfig:
    """Risk management configuration"""
    max_per_trade_risk: float = 0.02  # 2% of portfolio per trade
    max_portfolio_risk: float = 0.10  # 10% total portfolio risk
    max_position_size: int = 1000      # Maximum position size
    max_single_leg_delta: float = 0.50 # Maximum delta exposure per leg
    min_liquidity_threshold: int = 100  # Minimum daily volume
    max_margin_utilization: float = 0.75 # 75% max margin usage


class RiskGate:
    """Primary risk validation gate"""
    
    def __init__(self, max_per_trade_risk: float = 0.02, max_portfolio_risk: float = 0.10, **kwargs):
        """Initialize risk gate with configuration"""
        self.config = RiskConfig(
            max_per_trade_risk=max_per_trade_risk,
            max_portfolio_risk=max_portfolio_risk,
            **kwargs
        )
        self.violations_count = 0
    
    def validate_trade(self, trade: Dict[str, Any], portfolio: Dict[str, Any], 
                      account_equity: float) -> Dict[str, Any]:
        """Validate trade against risk parameters"""
        violations = []
        
        # Calculate trade risk metrics
        max_loss = trade.get("max_loss", 0)
        notional_value = trade.get("notional", 0)
        legs = trade.get("legs", [])
        
        # Risk checks
        violations.extend(self._check_position_size(trade, account_equity))
        violations.extend(self._check_portfolio_concentration(trade, portfolio, account_equity))
        violations.extend(self._check_max_loss_limits(max_loss, account_equity))
        violations.extend(self._check_strategy_risk(trade))
        violations.extend(self._check_liquidity(trade))
        
        # Calculate overall risk score (0-100)
        risk_score = self._calculate_risk_score(trade, portfolio, account_equity)
        
        # Determine overall risk level
        if risk_score < 25:
            risk_level = "low"
        elif risk_score < 50:
            risk_level = "medium"
        elif risk_score < 75:
            risk_level = "high"
        else:
            risk_level = "critical"
        
        return {
            "violations": violations,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "max_loss": max_loss,
            "portfolio_impact": (max_loss / account_equity) if account_equity > 0 else 0,
            "approved": len(violations) == 0 and risk_score < 75
        }
    
    def _check_position_size(self, trade: Dict[str, Any], account_equity: float) -> List[Dict[str, Any]]:
        """Check position size limits"""
        violations = []
        
        max_loss = trade.get("max_loss", 0)
        per_trade_limit = account_equity * self.config.max_per_trade_risk
        
        if max_loss > per_trade_limit:
            violations.append({
                "rule": "max_per_trade_risk",
                "severity": "high",
                "message": f"Trade risk ${max_loss:.2f} exceeds limit ${per_trade_limit:.2f}",
                "current_value": max_loss,
                "limit_value": per_trade_limit
            })
        
        return violations
    
    def _check_portfolio_concentration(self, trade: Dict[str, Any], portfolio: Dict[str, Any], 
                                     account_equity: float) -> List[Dict[str, Any]]:
        """Check portfolio concentration limits"""
        violations = []
        
        current_risk = portfolio.get("total_risk", 0.0)
        trade_risk = trade.get("max_loss", 0) / account_equity if account_equity > 0 else 0
        total_risk = current_risk + trade_risk
        
        if total_risk > self.config.max_portfolio_risk:
            violations.append({
                "rule": "max_portfolio_risk",
                "severity": "critical",
                "message": f"Total portfolio risk {total_risk:.1%} exceeds limit {self.config.max_portfolio_risk:.1%}",
                "current_value": total_risk,
                "limit_value": self.config.max_portfolio_risk
            })
        
        return violations
    
    def _check_max_loss_limits(self, max_loss: float, account_equity: float) -> List[Dict[str, Any]]:
        """Check absolute max loss limits"""
        violations = []
        
        # Hard limit: no single trade can risk more than 5% of portfolio
        absolute_limit = account_equity * 0.05
        
        if max_loss > absolute_limit:
            violations.append({
                "rule": "absolute_max_loss",
                "severity": "critical",
                "message": f"Max loss ${max_loss:.2f} exceeds absolute limit ${absolute_limit:.2f}",
                "current_value": max_loss,
                "limit_value": absolute_limit
            })
        
        return violations
    
    def _check_strategy_risk(self, trade: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check strategy-specific risk factors"""
        violations = []
        
        strategy_type = trade.get("strategy_type", "").lower()
        legs = trade.get("legs", [])
        
        # Check for undefined risk strategies
        unlimited_risk_strategies = ["short_call", "short_put", "naked_call", "naked_put"]
        
        if strategy_type in unlimited_risk_strategies:
            violations.append({
                "rule": "unlimited_risk_strategy",
                "severity": "critical",
                "message": f"Strategy {strategy_type} has unlimited risk potential",
                "current_value": strategy_type,
                "limit_value": "defined_risk_only"
            })
        
        # Check for complex strategies without proper hedging
        if len(legs) > 4:
            violations.append({
                "rule": "complex_strategy",
                "severity": "medium",
                "message": f"Strategy has {len(legs)} legs, review complexity",
                "current_value": len(legs),
                "limit_value": 4
            })
        
        return violations
    
    def _check_liquidity(self, trade: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check liquidity requirements"""
        violations = []
        
        # Mock liquidity check - in real implementation would check actual volume/OI
        symbol = trade.get("symbol", "")
        
        # Simple check: warn for less liquid symbols
        low_liquidity_symbols = ["SPY", "QQQ", "IWM"]  # Reverse logic for demo
        
        if symbol not in ["SPY", "QQQ", "AAPL", "TSLA", "MSFT", "AMZN"]:
            violations.append({
                "rule": "liquidity_check",
                "severity": "medium",
                "message": f"Symbol {symbol} may have lower liquidity",
                "current_value": symbol,
                "limit_value": "high_liquidity_required"
            })
        
        return violations
    
    def _calculate_risk_score(self, trade: Dict[str, Any], portfolio: Dict[str, Any], 
                            account_equity: float) -> float:
        """Calculate overall risk score (0-100)"""
        score = 0
        
        # Base score from max loss percentage
        max_loss = trade.get("max_loss", 0)
        loss_pct = (max_loss / account_equity) if account_equity > 0 else 0
        score += loss_pct * 1000  # Convert to 0-100 scale
        
        # Strategy complexity penalty
        legs = trade.get("legs", [])
        if len(legs) > 2:
            score += len(legs) * 5
        
        # Portfolio concentration penalty
        current_risk = portfolio.get("total_risk", 0.0)
        score += current_risk * 50
        
        # Symbol liquidity factor
        symbol = trade.get("symbol", "")
        if symbol not in ["SPY", "QQQ", "AAPL"]:
            score += 10
        
        return min(score, 100)  # Cap at 100
    
    def health_check(self) -> Dict[str, Any]:
        """Check risk gate health"""
        try:
            # Test validation with mock data
            test_trade = {
                "max_loss": 100,
                "notional": 1000,
                "legs": [{"action": "buy", "quantity": 1}],
                "strategy_type": "long_call",
                "symbol": "SPY"
            }
            
            test_portfolio = {"total_risk": 0.05}
            test_equity = 10000
            
            result = self.validate_trade(test_trade, test_portfolio, test_equity)
            
            return {
                "status": "healthy",
                "config": {
                    "max_per_trade_risk": self.config.max_per_trade_risk,
                    "max_portfolio_risk": self.config.max_portfolio_risk
                },
                "test_successful": "violations" in result
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Convenience function for simple validation
def validate_trade(trade: Dict[str, Any], portfolio: Dict[str, Any], account_equity: float) -> Dict[str, Any]:
    """Simple trade validation function"""
    gate = RiskGate()
    return gate.validate_trade(trade, portfolio, account_equity)


# Portfolio risk calculation utilities
def calculate_portfolio_risk(positions: List[Dict[str, Any]], account_equity: float) -> float:
    """Calculate total portfolio risk as percentage"""
    total_risk = sum(pos.get("max_loss", 0) for pos in positions)
    return total_risk / account_equity if account_equity > 0 else 0


def get_risk_limits() -> Dict[str, float]:
    """Get current risk limit configuration"""
    config = RiskConfig()
    return {
        "max_per_trade_risk": config.max_per_trade_risk,
        "max_portfolio_risk": config.max_portfolio_risk,
        "max_position_size": config.max_position_size,
        "max_margin_utilization": config.max_margin_utilization
    }


# Example usage and testing
if __name__ == "__main__":
    print("🛡️ Testing Phase 3 Risk Gates")
    
    # Initialize risk gate
    risk_gate = RiskGate(max_per_trade_risk=0.02, max_portfolio_risk=0.10)
    print("✅ Risk gate initialized")
    
    # Health check
    health = risk_gate.health_check()
    print(f"Health: {health['status']}")
    
    # Test different risk scenarios
    test_scenarios = [
        {
            "name": "Low Risk Trade",
            "trade": {
                "max_loss": 200,
                "notional": 10000,
                "legs": [{"action": "buy", "quantity": 1}],
                "strategy_type": "long_call",
                "symbol": "SPY"
            },
            "portfolio": {"total_risk": 0.03},
            "account_equity": 20000
        },
        {
            "name": "High Risk Trade", 
            "trade": {
                "max_loss": 1500,
                "notional": 15000,
                "legs": [{"action": "sell", "quantity": 5}],
                "strategy_type": "short_call",
                "symbol": "TSLA"
            },
            "portfolio": {"total_risk": 0.08},
            "account_equity": 20000
        },
        {
            "name": "Portfolio Limit Test",
            "trade": {
                "max_loss": 500,
                "notional": 8000,
                "legs": [{"action": "buy", "quantity": 2}],
                "strategy_type": "iron_condor",
                "symbol": "QQQ"
            },
            "portfolio": {"total_risk": 0.09},
            "account_equity": 15000
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n🎯 {scenario['name']}")
        result = risk_gate.validate_trade(
            scenario["trade"], 
            scenario["portfolio"], 
            scenario["account_equity"]
        )
        
        print(f"   Risk Score: {result['risk_score']:.1f}")
        print(f"   Risk Level: {result['risk_level']}")
        print(f"   Approved: {'✅' if result['approved'] else '❌'}")
        print(f"   Violations: {len(result['violations'])}")
        
        for violation in result['violations']:
            print(f"     - {violation['rule']}: {violation['message']}")
    
    print("\n🛡️ Risk Gates testing complete")