"""Core EMO Options Bot implementation."""

from typing import Optional
import structlog

from ..ai.nlp_processor import NLPProcessor
from ..trading.strategy_engine import StrategyEngine
from ..risk.risk_manager import RiskManager
from ..orders.order_stager import OrderStager
from ..market_data.provider import MarketDataProvider
from ..core.config import Config
from ..core.models import TradingStrategy, RiskAssessment

logger = structlog.get_logger()


class EMOOptionsBot:
    """
    Main EMO Options Bot class.
    
    Orchestrates AI-powered options trading with risk management and order staging.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize EMO Options Bot.
        
        Args:
            config: Configuration object (uses defaults if not provided)
        """
        self.config = config or Config.load()
        
        # Initialize components
        self.nlp_processor = NLPProcessor(
            api_key=self.config.ai.openai_api_key,
            model=self.config.ai.model
        )
        self.strategy_engine = StrategyEngine()
        self.risk_manager = RiskManager(config=self.config.risk)
        self.order_stager = OrderStager(
            require_approval=self.config.trading.require_manual_approval
        )
        self.market_data = MarketDataProvider(
            cache_enabled=self.config.market_data.cache_enabled
        )
        
        logger.info("EMO Options Bot initialized", config=self.config.model_dump())
    
    def process_command(self, command: str) -> dict:
        """
        Process a natural language trading command.
        
        This is the main entry point for the bot. It:
        1. Parses the command using NLP
        2. Analyzes the strategy
        3. Performs risk assessment
        4. Stakes the orders
        
        Args:
            command: Natural language trading command
            
        Returns:
            Dictionary with processing results
        """
        logger.info("Processing command", command=command)
        
        # Step 1: Parse command with NLP
        strategy = self.nlp_processor.parse_command(command)
        
        if not strategy:
            return {
                "success": False,
                "error": "Could not parse command",
                "command": command
            }
        
        logger.info("Strategy parsed", strategy_id=strategy.id, strategy_type=strategy.strategy_type)
        
        # Step 2: Validate and analyze strategy
        is_valid, errors = self.strategy_engine.validate_strategy(strategy)
        
        if not is_valid:
            return {
                "success": False,
                "error": "Strategy validation failed",
                "validation_errors": errors,
                "strategy": strategy.model_dump()
            }
        
        analysis = self.strategy_engine.analyze_strategy(strategy)
        logger.info("Strategy analyzed", analysis=analysis)
        
        # Step 3: Risk assessment
        risk_assessment = self.risk_manager.assess_strategy(strategy)
        logger.info(
            "Risk assessment complete",
            approved=risk_assessment.approved,
            risk_score=risk_assessment.risk_score
        )
        
        if not risk_assessment.approved:
            return {
                "success": False,
                "error": "Strategy failed risk assessment",
                "risk_assessment": risk_assessment.model_dump(),
                "strategy": strategy.model_dump(),
                "analysis": analysis
            }
        
        # Step 4: Stage orders
        strategy_id = self.order_stager.stage_strategy(strategy, risk_assessment)
        logger.info("Strategy staged", strategy_id=strategy_id)
        
        # Save strategy
        self.strategy_engine.save_strategy(strategy)
        
        return {
            "success": True,
            "strategy_id": strategy_id,
            "strategy": strategy.model_dump(),
            "analysis": analysis,
            "risk_assessment": risk_assessment.model_dump(),
            "next_steps": "Review staged orders and approve for execution"
        }
    
    def approve_strategy(self, strategy_id: str) -> dict:
        """
        Approve a staged strategy for execution.
        
        Args:
            strategy_id: Strategy ID to approve
            
        Returns:
            Dictionary with approval results
        """
        success = self.order_stager.approve_strategy(strategy_id)
        
        if not success:
            return {
                "success": False,
                "error": f"Strategy {strategy_id} not found"
            }
        
        logger.info("Strategy approved", strategy_id=strategy_id)
        
        return {
            "success": True,
            "strategy_id": strategy_id,
            "message": "Strategy approved and ready for execution"
        }
    
    def reject_strategy(self, strategy_id: str, reason: str = "") -> dict:
        """
        Reject a staged strategy.
        
        Args:
            strategy_id: Strategy ID to reject
            reason: Reason for rejection
            
        Returns:
            Dictionary with rejection results
        """
        success = self.order_stager.reject_strategy(strategy_id, reason)
        
        if not success:
            return {
                "success": False,
                "error": f"Strategy {strategy_id} not found"
            }
        
        logger.info("Strategy rejected", strategy_id=strategy_id, reason=reason)
        
        return {
            "success": True,
            "strategy_id": strategy_id,
            "message": "Strategy rejected"
        }
    
    def get_staged_strategies(self) -> list:
        """Get all staged strategies."""
        strategies = self.order_stager.get_staged_strategies()
        return [s.model_dump() for s in strategies]
    
    def get_portfolio_summary(self) -> dict:
        """Get current portfolio summary."""
        return self.risk_manager.get_portfolio_summary()
    
    def get_status(self) -> dict:
        """Get bot status and statistics."""
        return {
            "bot_version": "1.0.0",
            "config": {
                "paper_trading": self.config.trading.enable_paper_trading,
                "require_approval": self.config.trading.require_manual_approval,
                "risk_checks_enabled": self.config.risk.enable_risk_checks,
            },
            "orders": self.order_stager.get_order_summary(),
            "portfolio": self.get_portfolio_summary(),
            "strategies_count": len(self.strategy_engine.get_strategies()),
        }
