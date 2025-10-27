"""Unit tests for Risk Manager."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from emo_options_bot.risk.risk_manager import RiskManager
from emo_options_bot.core.config import RiskConfig
from emo_options_bot.core.models import (
    TradingStrategy, Order, OrderAction, OptionType,
    OptionContract, StrategyType, Portfolio
)


class TestRiskManager:
    """Test risk management functionality."""
    
    def test_initialization(self):
        """Test risk manager initialization."""
        manager = RiskManager()
        assert manager is not None
        assert manager.config is not None
    
    def test_initialization_with_config(self):
        """Test risk manager initialization with custom config."""
        config = RiskConfig(
            max_position_size=5000.0,
            max_portfolio_exposure=25000.0
        )
        
        manager = RiskManager(config)
        
        assert manager.config.max_position_size == 5000.0
        assert manager.config.max_portfolio_exposure == 25000.0
    
    def test_assess_strategy_within_limits(self):
        """Test assessing strategy within risk limits."""
        manager = RiskManager()
        
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
            max_risk=Decimal("500")
        )
        
        assessment = manager.assess_strategy(strategy)
        
        assert assessment.approved
        assert assessment.max_loss == Decimal("500")
        assert len(assessment.violations) == 0
    
    def test_assess_strategy_exceeds_position_limit(self):
        """Test assessing strategy that exceeds position limit."""
        config = RiskConfig(max_position_size=100.0)
        manager = RiskManager(config)
        
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
            max_risk=Decimal("500")
        )
        
        assessment = manager.assess_strategy(strategy)
        
        assert not assessment.approved
        assert len(assessment.violations) > 0
        assert any("position size" in v.lower() for v in assessment.violations)
    
    def test_assess_strategy_risk_checks_disabled(self):
        """Test assessing strategy with risk checks disabled."""
        config = RiskConfig(enable_risk_checks=False)
        manager = RiskManager(config)
        
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
            max_risk=Decimal("99999")
        )
        
        assessment = manager.assess_strategy(strategy)
        
        assert assessment.approved
        assert any("disabled" in w.lower() for w in assessment.warnings)
    
    def test_update_portfolio(self):
        """Test updating portfolio."""
        manager = RiskManager()
        
        portfolio = Portfolio(
            cash=Decimal("50000"),
            total_value=Decimal("60000")
        )
        
        manager.update_portfolio(portfolio)
        
        assert manager.portfolio.cash == Decimal("50000")
        assert manager.portfolio.total_value == Decimal("60000")
    
    def test_record_trade_result(self):
        """Test recording trade result."""
        manager = RiskManager()
        
        manager.record_trade_result(Decimal("-100"))
        
        assert len(manager.daily_losses) == 1
    
    def test_get_portfolio_summary(self):
        """Test getting portfolio summary."""
        manager = RiskManager()
        
        portfolio = Portfolio(
            cash=Decimal("50000"),
            total_value=Decimal("60000"),
            daily_pnl=Decimal("1000")
        )
        
        manager.update_portfolio(portfolio)
        
        summary = manager.get_portfolio_summary()
        
        assert "cash" in summary
        assert "total_value" in summary
        assert summary["cash"] == 50000.0
        assert summary["total_value"] == 60000.0
    
    def test_check_margin_requirements(self):
        """Test checking margin requirements."""
        manager = RiskManager()
        
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
            max_risk=Decimal("500")
        )
        
        has_margin, required = manager.check_margin_requirements(strategy)
        
        assert has_margin  # Default portfolio has 100000 cash
        assert required == Decimal("500")
