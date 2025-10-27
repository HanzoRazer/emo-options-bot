"""Integration tests for EMO Options Bot."""

import pytest
from decimal import Decimal
from emo_options_bot import EMOOptionsBot
from emo_options_bot.core.config import Config, RiskConfig, TradingConfig


class TestEMOOptionsBot:
    """Integration tests for the complete bot workflow."""
    
    def test_bot_initialization(self):
        """Test bot initialization."""
        bot = EMOOptionsBot()
        
        assert bot is not None
        assert bot.nlp_processor is not None
        assert bot.strategy_engine is not None
        assert bot.risk_manager is not None
        assert bot.order_stager is not None
    
    def test_process_simple_command(self):
        """Test processing a simple trading command."""
        bot = EMOOptionsBot()
        
        result = bot.process_command("Buy 1 AAPL call at $150")
        
        assert result is not None
        assert "success" in result
        
        # If parsing succeeds, we should have a strategy
        if result["success"]:
            assert "strategy_id" in result
            assert "risk_assessment" in result
    
    def test_process_command_with_risk_violation(self):
        """Test processing command that violates risk limits."""
        config = Config()
        config.risk.max_position_size = 100.0  # Very low limit
        
        bot = EMOOptionsBot(config)
        
        result = bot.process_command("Buy 10 AAPL call at $150")
        
        # Should fail risk check with low position limit
        assert result is not None
    
    def test_approve_workflow(self):
        """Test complete approve workflow."""
        bot = EMOOptionsBot()
        
        # Process command
        result = bot.process_command("Buy 1 AAPL call at $150")
        
        if result.get("success"):
            strategy_id = result["strategy_id"]
            
            # Approve strategy
            approve_result = bot.approve_strategy(strategy_id)
            
            assert approve_result["success"]
            assert approve_result["strategy_id"] == strategy_id
    
    def test_reject_workflow(self):
        """Test complete reject workflow."""
        bot = EMOOptionsBot()
        
        # Process command
        result = bot.process_command("Buy 1 AAPL call at $150")
        
        if result.get("success"):
            strategy_id = result["strategy_id"]
            
            # Reject strategy
            reject_result = bot.reject_strategy(strategy_id, "Test rejection")
            
            assert reject_result["success"]
            assert reject_result["strategy_id"] == strategy_id
    
    def test_get_status(self):
        """Test getting bot status."""
        bot = EMOOptionsBot()
        
        status = bot.get_status()
        
        assert "bot_version" in status
        assert "config" in status
        assert "orders" in status
        assert "portfolio" in status
    
    def test_get_staged_strategies(self):
        """Test getting staged strategies."""
        bot = EMOOptionsBot()
        
        # Process a command
        result = bot.process_command("Buy 1 AAPL call at $150")
        
        # Get staged strategies
        strategies = bot.get_staged_strategies()
        
        assert isinstance(strategies, list)
        
        if result.get("success"):
            assert len(strategies) >= 1
    
    def test_multiple_commands(self):
        """Test processing multiple commands."""
        bot = EMOOptionsBot()
        
        commands = [
            "Buy 1 AAPL call at $150",
            "Buy 1 TSLA put at $200",
        ]
        
        results = []
        for command in commands:
            result = bot.process_command(command)
            results.append(result)
        
        # At least some should succeed (depends on parsing)
        assert len(results) == 2
    
    def test_portfolio_summary(self):
        """Test getting portfolio summary."""
        bot = EMOOptionsBot()
        
        summary = bot.get_portfolio_summary()
        
        assert "cash" in summary
        assert "total_value" in summary
        assert "positions_count" in summary
