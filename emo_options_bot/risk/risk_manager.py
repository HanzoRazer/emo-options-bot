"""Risk management system."""

from typing import Optional, List
from decimal import Decimal
from datetime import datetime, date

from ..core.models import (
    TradingStrategy, Order, Portfolio, Position, RiskAssessment
)
from ..core.config import RiskConfig


class RiskManager:
    """
    Manage trading risk with position limits and exposure tracking.
    
    Validates trades against risk parameters and portfolio limits.
    """
    
    def __init__(self, config: Optional[RiskConfig] = None):
        """Initialize risk manager."""
        self.config = config or RiskConfig()
        self.portfolio = Portfolio()
        self.daily_losses: List[tuple[date, Decimal]] = []
    
    def assess_strategy(self, strategy: TradingStrategy) -> RiskAssessment:
        """
        Assess risk for a trading strategy.
        
        Args:
            strategy: Strategy to assess
            
        Returns:
            RiskAssessment with approval status and details
        """
        assessment = RiskAssessment(
            approved=True,
            max_loss=strategy.max_risk,
        )
        
        if not self.config.enable_risk_checks:
            assessment.warnings.append("Risk checks are disabled")
            return assessment
        
        # Check position size limit
        if strategy.max_risk > self.config.max_position_size:
            assessment.violations.append(
                f"Position size {strategy.max_risk} exceeds limit {self.config.max_position_size}"
            )
            assessment.approved = False
        
        # Check max loss per trade
        if strategy.max_risk > self.config.max_loss_per_trade:
            assessment.violations.append(
                f"Max loss {strategy.max_risk} exceeds per-trade limit {self.config.max_loss_per_trade}"
            )
            assessment.approved = False
        
        # Calculate position exposure
        position_exposure = self._calculate_position_exposure(strategy)
        assessment.position_exposure = position_exposure
        
        # Calculate portfolio exposure
        portfolio_exposure = self._calculate_portfolio_exposure() + position_exposure
        assessment.portfolio_exposure = portfolio_exposure
        
        # Check portfolio exposure limit
        if portfolio_exposure > self.config.max_portfolio_exposure:
            assessment.violations.append(
                f"Portfolio exposure {portfolio_exposure} exceeds limit {self.config.max_portfolio_exposure}"
            )
            assessment.approved = False
        
        # Check daily loss limit
        today_loss = self._get_daily_loss(datetime.now().date())
        if today_loss + strategy.max_risk > self.config.max_loss_per_day:
            assessment.violations.append(
                f"Potential daily loss {today_loss + strategy.max_risk} exceeds limit {self.config.max_loss_per_day}"
            )
            assessment.approved = False
        
        # Calculate risk score (0-100)
        assessment.risk_score = self._calculate_risk_score(strategy, assessment)
        
        # Add warnings based on risk score
        if assessment.risk_score > 75:
            assessment.warnings.append("High risk score - proceed with caution")
        elif assessment.risk_score > 50:
            assessment.warnings.append("Moderate risk score")
        
        return assessment
    
    def update_portfolio(self, portfolio: Portfolio):
        """Update current portfolio state."""
        self.portfolio = portfolio
    
    def record_trade_result(self, pnl: Decimal, trade_date: Optional[date] = None):
        """Record trade result for daily loss tracking."""
        trade_date = trade_date or datetime.now().date()
        self.daily_losses.append((trade_date, pnl))
    
    def get_portfolio_summary(self) -> dict:
        """Get portfolio summary."""
        return {
            "cash": float(self.portfolio.cash),
            "total_value": float(self.portfolio.total_value),
            "positions_count": len(self.portfolio.positions),
            "daily_pnl": float(self.portfolio.daily_pnl),
            "total_pnl": float(self.portfolio.total_pnl),
            "updated_at": self.portfolio.updated_at.isoformat(),
        }
    
    def _calculate_position_exposure(self, strategy: TradingStrategy) -> Decimal:
        """Calculate total position exposure for strategy."""
        return strategy.max_risk
    
    def _calculate_portfolio_exposure(self) -> Decimal:
        """Calculate current portfolio exposure."""
        exposure = Decimal(0)
        
        for position in self.portfolio.positions:
            # Calculate exposure based on position value
            position_value = abs(position.quantity) * position.average_cost * Decimal(100)
            exposure += position_value
        
        return exposure
    
    def _get_daily_loss(self, trade_date: date) -> Decimal:
        """Get total loss for a specific day."""
        daily_loss = Decimal(0)
        
        for loss_date, pnl in self.daily_losses:
            if loss_date == trade_date and pnl < 0:
                daily_loss += abs(pnl)
        
        return daily_loss
    
    def _calculate_risk_score(self, strategy: TradingStrategy, assessment: RiskAssessment) -> float:
        """
        Calculate risk score (0-100).
        
        Higher score = higher risk.
        """
        score = 0.0
        
        # Factor 1: Position size relative to limit (0-40 points)
        if self.config.max_position_size > 0:
            position_ratio = float(strategy.max_risk / self.config.max_position_size)
            score += min(position_ratio * 40, 40)
        
        # Factor 2: Portfolio exposure relative to limit (0-30 points)
        if self.config.max_portfolio_exposure > 0:
            exposure_ratio = float(assessment.portfolio_exposure / self.config.max_portfolio_exposure)
            score += min(exposure_ratio * 30, 30)
        
        # Factor 3: Daily loss relative to limit (0-30 points)
        if self.config.max_loss_per_day > 0:
            today_loss = self._get_daily_loss(datetime.now().date())
            loss_ratio = float((today_loss + strategy.max_risk) / self.config.max_loss_per_day)
            score += min(loss_ratio * 30, 30)
        
        return min(score, 100.0)
    
    def check_margin_requirements(self, strategy: TradingStrategy) -> tuple[bool, Decimal]:
        """
        Check if sufficient margin is available.
        
        Returns:
            Tuple of (has_sufficient_margin, required_margin)
        """
        required_margin = strategy.max_risk
        available_margin = self.portfolio.cash
        
        return available_margin >= required_margin, required_margin
