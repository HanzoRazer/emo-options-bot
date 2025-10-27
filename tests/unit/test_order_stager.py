"""Unit tests for Order Stager."""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from emo_options_bot.orders.order_stager import OrderStager
from emo_options_bot.core.models import (
    TradingStrategy, Order, OrderAction, OrderStatus,
    OptionType, OptionContract, StrategyType, RiskAssessment
)


class TestOrderStager:
    """Test order staging functionality."""
    
    def test_initialization(self):
        """Test order stager initialization."""
        stager = OrderStager()
        assert stager is not None
        assert stager.require_approval
    
    def test_stage_order(self):
        """Test staging an order."""
        stager = OrderStager()
        
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
        
        order_id = stager.stage_order(order)
        
        assert order_id == order.id
        assert order.status == OrderStatus.STAGED
        assert order_id in stager.staged_orders
    
    def test_stage_strategy(self):
        """Test staging a strategy."""
        stager = OrderStager()
        
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
        
        risk_assessment = RiskAssessment(approved=True)
        
        strategy_id = stager.stage_strategy(strategy, risk_assessment)
        
        assert strategy_id == strategy.id
        assert strategy_id in stager.staged_strategies
        assert len(stager.staged_orders) == 1
    
    def test_approve_order(self):
        """Test approving an order."""
        stager = OrderStager()
        
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
        
        order_id = stager.stage_order(order)
        success = stager.approve_order(order_id)
        
        assert success
        assert order.status == OrderStatus.APPROVED
    
    def test_approve_nonexistent_order(self):
        """Test approving non-existent order."""
        stager = OrderStager()
        
        success = stager.approve_order("INVALID_ID")
        
        assert not success
    
    def test_reject_order(self):
        """Test rejecting an order."""
        stager = OrderStager()
        
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
        
        order_id = stager.stage_order(order)
        success = stager.reject_order(order_id, "Test rejection")
        
        assert success
        assert order.status == OrderStatus.REJECTED
        assert order_id not in stager.staged_orders
        assert len(stager.order_history) == 1
    
    def test_approve_strategy(self):
        """Test approving a strategy."""
        stager = OrderStager()
        
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
        
        risk_assessment = RiskAssessment(approved=True)
        
        strategy_id = stager.stage_strategy(strategy, risk_assessment)
        success = stager.approve_strategy(strategy_id)
        
        assert success
        assert all(o.status == OrderStatus.APPROVED for o in strategy.orders)
    
    def test_get_staged_orders(self):
        """Test getting staged orders."""
        stager = OrderStager()
        
        contract = OptionContract(
            symbol="AAPL_150_CALL_2024-12-20",
            underlying="AAPL",
            strike=Decimal("150"),
            expiration=(datetime.now() + timedelta(days=30)).date(),
            option_type=OptionType.CALL,
            quantity=1
        )
        
        order1 = Order(
            contract=contract,
            action=OrderAction.BUY_TO_OPEN,
            quantity=1
        )
        
        order2 = Order(
            contract=contract,
            action=OrderAction.BUY_TO_OPEN,
            quantity=2
        )
        
        stager.stage_order(order1)
        stager.stage_order(order2)
        
        staged = stager.get_staged_orders()
        
        assert len(staged) == 2
    
    def test_get_approved_orders(self):
        """Test getting approved orders."""
        stager = OrderStager()
        
        contract = OptionContract(
            symbol="AAPL_150_CALL_2024-12-20",
            underlying="AAPL",
            strike=Decimal("150"),
            expiration=(datetime.now() + timedelta(days=30)).date(),
            option_type=OptionType.CALL,
            quantity=1
        )
        
        order1 = Order(
            contract=contract,
            action=OrderAction.BUY_TO_OPEN,
            quantity=1
        )
        
        order2 = Order(
            contract=contract,
            action=OrderAction.BUY_TO_OPEN,
            quantity=2
        )
        
        stager.stage_order(order1)
        stager.stage_order(order2)
        stager.approve_order(order1.id)
        
        approved = stager.get_approved_orders()
        
        assert len(approved) == 1
        assert approved[0].id == order1.id
    
    def test_mark_as_submitted(self):
        """Test marking order as submitted."""
        stager = OrderStager()
        
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
        
        order_id = stager.stage_order(order)
        stager.approve_order(order_id)
        success = stager.mark_as_submitted(order_id, "BROKER_123")
        
        assert success
        assert order.status == OrderStatus.SUBMITTED
        assert order.metadata["broker_order_id"] == "BROKER_123"
    
    def test_mark_as_filled(self):
        """Test marking order as filled."""
        stager = OrderStager()
        
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
        
        order_id = stager.stage_order(order)
        stager.approve_order(order_id)
        stager.mark_as_submitted(order_id)
        success = stager.mark_as_filled(order_id, Decimal("5.50"), 1)
        
        assert success
        assert order.status == OrderStatus.FILLED
        assert order.filled_price == Decimal("5.50")
        assert order.filled_quantity == 1
        assert order_id not in stager.staged_orders
        assert len(stager.order_history) == 1
