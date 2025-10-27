"""Data models for EMO Options Bot."""

from typing import Optional, Literal, Dict, Any
from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field
from enum import Enum


class OptionType(str, Enum):
    """Option type."""
    CALL = "CALL"
    PUT = "PUT"


class OrderAction(str, Enum):
    """Order action."""
    BUY = "BUY"
    SELL = "SELL"
    BUY_TO_OPEN = "BUY_TO_OPEN"
    SELL_TO_CLOSE = "SELL_TO_CLOSE"
    BUY_TO_CLOSE = "BUY_TO_CLOSE"
    SELL_TO_OPEN = "SELL_TO_OPEN"


class OrderStatus(str, Enum):
    """Order status."""
    PENDING = "PENDING"
    STAGED = "STAGED"
    APPROVED = "APPROVED"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class StrategyType(str, Enum):
    """Trading strategy type."""
    SINGLE_OPTION = "SINGLE_OPTION"
    VERTICAL_SPREAD = "VERTICAL_SPREAD"
    IRON_CONDOR = "IRON_CONDOR"
    BUTTERFLY = "BUTTERFLY"
    STRADDLE = "STRADDLE"
    STRANGLE = "STRANGLE"
    CUSTOM = "CUSTOM"


class OptionContract(BaseModel):
    """Option contract specification."""
    symbol: str
    underlying: str
    strike: Decimal
    expiration: date
    option_type: OptionType
    quantity: int = 1
    
    def __str__(self) -> str:
        return f"{self.underlying} {self.strike} {self.option_type.value} {self.expiration}"


class Order(BaseModel):
    """Trading order."""
    id: str = Field(default_factory=lambda: f"ORD_{datetime.now().strftime('%Y%m%d%H%M%S%f')}")
    contract: OptionContract
    action: OrderAction
    quantity: int
    limit_price: Optional[Decimal] = None
    status: OrderStatus = OrderStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    filled_price: Optional[Decimal] = None
    filled_quantity: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TradingStrategy(BaseModel):
    """Trading strategy specification."""
    id: str = Field(default_factory=lambda: f"STRAT_{datetime.now().strftime('%Y%m%d%H%M%S%f')}")
    name: str
    strategy_type: StrategyType
    orders: list[Order]
    max_risk: Decimal
    max_profit: Optional[Decimal] = None
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Position(BaseModel):
    """Current position."""
    contract: OptionContract
    quantity: int
    average_cost: Decimal
    current_price: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    realized_pnl: Decimal = Decimal(0)


class Portfolio(BaseModel):
    """Portfolio state."""
    cash: Decimal = Decimal(100000)
    positions: list[Position] = Field(default_factory=list)
    total_value: Decimal = Decimal(100000)
    daily_pnl: Decimal = Decimal(0)
    total_pnl: Decimal = Decimal(0)
    updated_at: datetime = Field(default_factory=datetime.now)


class RiskAssessment(BaseModel):
    """Risk assessment result."""
    approved: bool
    risk_score: float = 0.0
    warnings: list[str] = Field(default_factory=list)
    violations: list[str] = Field(default_factory=list)
    max_loss: Decimal = Decimal(0)
    position_exposure: Decimal = Decimal(0)
    portfolio_exposure: Decimal = Decimal(0)
