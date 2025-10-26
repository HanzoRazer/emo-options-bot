"""
Signals-based strategy framework for EMO Options Bot.
This module provides a complementary approach to the existing options strategies.
"""

from .base import BaseStrategy, Signal
from .iron_condor import IronCondor
from .put_credit_spread import PutCreditSpread
from .manager import StrategyManager

__all__ = [
    "BaseStrategy", 
    "Signal", 
    "IronCondor", 
    "PutCreditSpread", 
    "StrategyManager"
]