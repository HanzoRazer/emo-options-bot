"""
AI Trading Agents Package
Voice-driven AI trading assistant with natural language understanding.
"""

from .ai_agent import AITradingAgent, create_ai_agent, start_voice_trading_assistant
from .nlu_router import NLURouter
from .planner import TradingPlanner
from .approval_flow import ApprovalFlow, ApprovalAction, get_approval_flow
from .voice_interface import VoiceInterface, VoiceCommandProcessor
from .strategy_translator import StrategyTranslator
from .validator import TradingPlanValidator
from .intent_schema import validate_intent, INTENT_SCHEMA

__all__ = [
    # Main agent
    "AITradingAgent",
    "create_ai_agent", 
    "start_voice_trading_assistant",
    
    # Core components
    "NLURouter",
    "TradingPlanner", 
    "ApprovalFlow",
    "VoiceInterface",
    "VoiceCommandProcessor",
    "StrategyTranslator",
    "TradingPlanValidator",
    
    # Utilities
    "ApprovalAction",
    "get_approval_flow",
    "validate_intent",
    "INTENT_SCHEMA"
]

# Package info
__version__ = "1.0.0"
__author__ = "EMO Options Bot"
__description__ = "Voice-driven AI trading assistant with natural language understanding"