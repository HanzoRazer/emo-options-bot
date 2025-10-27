"""
EMO Options Bot - AI-Powered Intelligent Trading System

An enterprise-grade, AI-driven options trading platform that transforms
natural language into intelligent trading strategies with built-in risk
management and order staging capabilities.
"""

__version__ = "1.0.0"
__author__ = "Ross Echols"
__license__ = "MIT"

from .ai.nlp_processor import NLPProcessor
from .trading.strategy_engine import StrategyEngine
from .risk.risk_manager import RiskManager
from .orders.order_stager import OrderStager
from .core.bot import EMOOptionsBot

__all__ = [
    "NLPProcessor",
    "StrategyEngine",
    "RiskManager",
    "OrderStager",
    "EMOOptionsBot",
]
