"""Unit tests for Strategy Engine."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from emo_options_bot.trading.strategy_engine import StrategyEngine
from emo_options_bot.core.models import (
    TradingStrategy, Order, OrderAction, OptionType,
    OptionContract, StrategyType
)


class TestStrategyEngine:
    """Test strategy engine functionality."""
    
    def test_initialization(self):
        """Test strategy engine initialization."""
        engine = StrategyEngine()
        assert engine is not None
        assert len(engine.strategies) == 0
    
    def test_validate_valid_strategy(self):
        """Test validating a valid strategy."""
        engine = StrategyEngine()
        
        contract = OptionContract(
            symbol="AAPL_150_CALL_2024-12-20",
            underlying="AAPL",
            strike=Decimal("150"),
            expiration=(datetime.now() + timedelta(days=30)).date(),
            option_type=OptionType.CALL,
            quantity=1
        )
        
        order = Order(
            contract=contract,
            action=OrderAction.BUY_TO_OPEN,
            quantity=1
        )
        
        strategy = TradingStrategy(
            name="Test Strategy",
            strategy_type=StrategyType.SINGLE_OPTION,
            orders=[order],
            max_risk=Decimal("1000")
        )
        
        is_valid, errors = engine.validate_strategy(strategy)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_strategy_no_orders(self):
        """Test validating strategy with no orders."""
        engine = StrategyEngine()
        
        strategy = TradingStrategy(
            name="Test Strategy",
            strategy_type=StrategyType.SINGLE_OPTION,
            orders=[],
            max_risk=Decimal("1000")
        )
        
        is_valid, errors = engine.validate_strategy(strategy)
        
        assert not is_valid
        assert len(errors) > 0
    
    def test_validate_strategy_expired_contract(self):
        """Test validating strategy with expired contract."""
        engine = StrategyEngine()
        
        contract = OptionContract(
            symbol="AAPL_150_CALL_2020-01-01",
            underlying="AAPL",
            strike=Decimal("150"),
            expiration=datetime(2020, 1, 1).date(),
            option_type=OptionType.CALL,
            quantity=1
        )
        
        order = Order(
            contract=contract,
            action=OrderAction.BUY_TO_OPEN,
            quantity=1
        )
        
        strategy = TradingStrategy(
            name="Test Strategy",
            strategy_type=StrategyType.SINGLE_OPTION,
            orders=[order],
            max_risk=Decimal("1000")
        )
        
        is_valid, errors = engine.validate_strategy(strategy)
        
        assert not is_valid
        assert any("expired" in error.lower() for error in errors)
    
    def test_analyze_strategy(self):
        """Test strategy analysis."""
        engine = StrategyEngine()
        
        contract = OptionContract(
            symbol="AAPL_150_CALL_2024-12-20",
            underlying="AAPL",
            strike=Decimal("150"),
            expiration=(datetime.now() + timedelta(days=30)).date(),
            option_type=OptionType.CALL,
            quantity=1
        )
        
        order = Order(
            contract=contract,
            action=OrderAction.BUY_TO_OPEN,
            quantity=1,
            limit_price=Decimal("5.50")
        )
        
        strategy = TradingStrategy(
            name="Test Strategy",
            strategy_type=StrategyType.SINGLE_OPTION,
            orders=[order],
            max_risk=Decimal("550")
        )
        
        analysis = engine.analyze_strategy(strategy)
        
        assert "strategy_id" in analysis
        assert analysis["strategy_type"] == StrategyType.SINGLE_OPTION
        assert analysis["max_risk"] == Decimal("550")
        assert analysis["legs"] == 1
    
    def test_create_vertical_spread(self):
        """Test creating vertical spread."""
        engine = StrategyEngine()
        
        strategy = engine.create_vertical_spread(
            underlying="SPY",
            option_type=OptionType.CALL,
            long_strike=Decimal("450"),
            short_strike=Decimal("455"),
            expiration=(datetime.now() + timedelta(days=30)).date(),
            quantity=1
        )
        
        assert strategy is not None
        assert strategy.strategy_type == StrategyType.VERTICAL_SPREAD
        assert len(strategy.orders) == 2
        assert strategy.orders[0].action == OrderAction.BUY_TO_OPEN
        assert strategy.orders[1].action == OrderAction.SELL_TO_OPEN
    
    def test_save_and_get_strategies(self):
        """Test saving and retrieving strategies."""
        engine = StrategyEngine()
        
        contract = OptionContract(
            symbol="AAPL_150_CALL_2024-12-20",
            underlying="AAPL",
            strike=Decimal("150"),
            expiration=(datetime.now() + timedelta(days=30)).date(),
            option_type=OptionType.CALL,
            quantity=1
        )
        
        order = Order(
            contract=contract,
            action=OrderAction.BUY_TO_OPEN,
            quantity=1
        )
        
        strategy = TradingStrategy(
            name="Test Strategy",
            strategy_type=StrategyType.SINGLE_OPTION,
            orders=[order],
            max_risk=Decimal("1000")
        )
        
        engine.save_strategy(strategy)
        
        strategies = engine.get_strategies()
        assert len(strategies) == 1
        assert strategies[0].id == strategy.id
