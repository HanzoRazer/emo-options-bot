"""Unit tests for NLP Processor."""

import pytest
from decimal import Decimal
from emo_options_bot.ai.nlp_processor import NLPProcessor
from emo_options_bot.core.models import OptionType, OrderAction, StrategyType


class TestNLPProcessor:
    """Test NLP command parsing."""
    
    def test_initialization(self):
        """Test NLP processor initialization."""
        processor = NLPProcessor()
        assert processor is not None
    
    def test_parse_simple_call_buy(self):
        """Test parsing simple call buy command."""
        processor = NLPProcessor()
        command = "Buy 1 AAPL call at $150"
        
        strategy = processor.parse_command(command)
        
        assert strategy is not None
        assert strategy.strategy_type == StrategyType.SINGLE_OPTION
        assert len(strategy.orders) == 1
        
        order = strategy.orders[0]
        assert order.contract.underlying == "AAPL"
        assert order.contract.option_type == OptionType.CALL
        assert order.contract.strike == Decimal("150")
        assert order.action == OrderAction.BUY_TO_OPEN
        assert order.quantity == 1
    
    def test_parse_simple_put_sell(self):
        """Test parsing simple put sell command."""
        processor = NLPProcessor()
        command = "Sell 2 TSLA put at $200"
        
        strategy = processor.parse_command(command)
        
        assert strategy is not None
        assert strategy.strategy_type == StrategyType.SINGLE_OPTION
        assert len(strategy.orders) == 1
        
        order = strategy.orders[0]
        assert order.contract.underlying == "TSLA"
        assert order.contract.option_type == OptionType.PUT
        assert order.contract.strike == Decimal("200")
        assert order.action == OrderAction.SELL_TO_OPEN
        assert order.quantity == 2
    
    def test_parse_invalid_command(self):
        """Test parsing invalid command."""
        processor = NLPProcessor()
        command = "invalid command with no valid info"
        
        strategy = processor.parse_command(command)
        
        assert strategy is None
    
    def test_parse_without_symbol(self):
        """Test parsing command without symbol."""
        processor = NLPProcessor()
        command = "Buy call at $150"
        
        strategy = processor.parse_command(command)
        
        assert strategy is None
