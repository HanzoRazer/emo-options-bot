# EMO Logic Package
"""
Risk management and position sizing logic for EMO Options Bot
Professional-grade trading controls and portfolio management
"""

from .risk_manager import RiskManager, PortfolioSnapshot, Position, OrderIntent
from .position_sizer import equity_size_by_vol, credit_spread_contracts, correlation_scale

__all__ = [
    "RiskManager", 
    "PortfolioSnapshot", 
    "Position", 
    "OrderIntent",
    "equity_size_by_vol", 
    "credit_spread_contracts", 
    "correlation_scale"
]