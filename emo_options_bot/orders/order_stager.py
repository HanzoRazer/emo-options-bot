"""Order staging and validation system."""

from typing import List, Optional, Dict
from datetime import datetime
from decimal import Decimal

from ..core.models import (
    Order, OrderStatus, TradingStrategy, RiskAssessment
)


class OrderStager:
    """
    Stage and validate orders before execution.
    
    Manages order workflow from creation to execution approval.
    """
    
    def __init__(self, require_approval: bool = True):
        """Initialize order stager."""
        self.require_approval = require_approval
        self.staged_orders: Dict[str, Order] = {}
        self.staged_strategies: Dict[str, TradingStrategy] = {}
        self.order_history: List[Order] = []
    
    def stage_order(self, order: Order) -> str:
        """
        Stage an order for review.
        
        Args:
            order: Order to stage
            
        Returns:
            Order ID
        """
        order.status = OrderStatus.STAGED
        order.updated_at = datetime.now()
        self.staged_orders[order.id] = order
        
        return order.id
    
    def stage_strategy(self, strategy: TradingStrategy, risk_assessment: RiskAssessment) -> str:
        """
        Stage a complete trading strategy.
        
        Args:
            strategy: Trading strategy to stage
            risk_assessment: Risk assessment for the strategy
            
        Returns:
            Strategy ID
        """
        # Stage all orders in the strategy
        for order in strategy.orders:
            order.status = OrderStatus.STAGED
            order.updated_at = datetime.now()
            order.metadata["risk_assessment"] = risk_assessment.model_dump()
            self.staged_orders[order.id] = order
        
        self.staged_strategies[strategy.id] = strategy
        
        return strategy.id
    
    def approve_order(self, order_id: str) -> bool:
        """
        Approve a staged order for execution.
        
        Args:
            order_id: ID of order to approve
            
        Returns:
            True if approved successfully
        """
        if order_id not in self.staged_orders:
            return False
        
        order = self.staged_orders[order_id]
        order.status = OrderStatus.APPROVED
        order.updated_at = datetime.now()
        
        return True
    
    def approve_strategy(self, strategy_id: str) -> bool:
        """
        Approve all orders in a strategy.
        
        Args:
            strategy_id: ID of strategy to approve
            
        Returns:
            True if approved successfully
        """
        if strategy_id not in self.staged_strategies:
            return False
        
        strategy = self.staged_strategies[strategy_id]
        
        for order in strategy.orders:
            if order.id in self.staged_orders:
                self.approve_order(order.id)
        
        return True
    
    def reject_order(self, order_id: str, reason: str = "") -> bool:
        """
        Reject a staged order.
        
        Args:
            order_id: ID of order to reject
            reason: Reason for rejection
            
        Returns:
            True if rejected successfully
        """
        if order_id not in self.staged_orders:
            return False
        
        order = self.staged_orders[order_id]
        order.status = OrderStatus.REJECTED
        order.updated_at = datetime.now()
        order.metadata["rejection_reason"] = reason
        
        # Move to history
        self.order_history.append(order)
        del self.staged_orders[order_id]
        
        return True
    
    def reject_strategy(self, strategy_id: str, reason: str = "") -> bool:
        """
        Reject all orders in a strategy.
        
        Args:
            strategy_id: ID of strategy to reject
            reason: Reason for rejection
            
        Returns:
            True if rejected successfully
        """
        if strategy_id not in self.staged_strategies:
            return False
        
        strategy = self.staged_strategies[strategy_id]
        
        for order in strategy.orders:
            if order.id in self.staged_orders:
                self.reject_order(order.id, reason)
        
        del self.staged_strategies[strategy_id]
        
        return True
    
    def get_staged_orders(self) -> List[Order]:
        """Get all staged orders."""
        return list(self.staged_orders.values())
    
    def get_staged_strategies(self) -> List[TradingStrategy]:
        """Get all staged strategies."""
        return list(self.staged_strategies.values())
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get specific order by ID."""
        return self.staged_orders.get(order_id)
    
    def get_strategy(self, strategy_id: str) -> Optional[TradingStrategy]:
        """Get specific strategy by ID."""
        return self.staged_strategies.get(strategy_id)
    
    def get_approved_orders(self) -> List[Order]:
        """Get all approved orders ready for execution."""
        return [
            order for order in self.staged_orders.values()
            if order.status == OrderStatus.APPROVED
        ]
    
    def mark_as_submitted(self, order_id: str, broker_order_id: Optional[str] = None) -> bool:
        """
        Mark order as submitted to broker.
        
        Args:
            order_id: Order ID
            broker_order_id: Broker's order ID
            
        Returns:
            True if successful
        """
        if order_id not in self.staged_orders:
            return False
        
        order = self.staged_orders[order_id]
        order.status = OrderStatus.SUBMITTED
        order.updated_at = datetime.now()
        
        if broker_order_id:
            order.metadata["broker_order_id"] = broker_order_id
        
        return True
    
    def mark_as_filled(
        self,
        order_id: str,
        filled_price: Decimal,
        filled_quantity: int
    ) -> bool:
        """
        Mark order as filled.
        
        Args:
            order_id: Order ID
            filled_price: Price at which order was filled
            filled_quantity: Quantity filled
            
        Returns:
            True if successful
        """
        if order_id not in self.staged_orders:
            return False
        
        order = self.staged_orders[order_id]
        order.status = OrderStatus.FILLED
        order.filled_price = filled_price
        order.filled_quantity = filled_quantity
        order.updated_at = datetime.now()
        
        # Move to history
        self.order_history.append(order)
        del self.staged_orders[order_id]
        
        return True
    
    def get_order_summary(self) -> dict:
        """Get summary of staged orders."""
        statuses = {}
        
        for order in self.staged_orders.values():
            status = order.status.value
            statuses[status] = statuses.get(status, 0) + 1
        
        return {
            "total_staged": len(self.staged_orders),
            "total_strategies": len(self.staged_strategies),
            "by_status": statuses,
            "history_count": len(self.order_history),
        }
