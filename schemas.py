"""
Phase 3 Schemas - Pydantic models for data validation
Provides standardized data structures for the EMO Options Bot Phase 3 system
"""

from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator


# ============================================================================
# Enums for standardized values
# ============================================================================

class OrderSide(str, Enum):
    """Order side enumeration"""
    BUY = "buy"
    SELL = "sell"

class OrderType(str, Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OptionType(str, Enum):
    """Option instrument type"""
    CALL = "call"
    PUT = "put"

class StrategyType(str, Enum):
    """Options strategy types"""
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    SHORT_CALL = "short_call"
    SHORT_PUT = "short_put"
    IRON_CONDOR = "iron_condor"
    PUT_CREDIT_SPREAD = "put_credit_spread"
    CALL_CREDIT_SPREAD = "call_credit_spread"
    STRADDLE = "straddle"
    STRANGLE = "strangle"
    COVERED_CALL = "covered_call"

class OrderStatus(str, Enum):
    """Order status enumeration"""
    STAGED = "staged"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUBMITTED = "submitted"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class RiskLevel(str, Enum):
    """Risk level classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# Core Data Models
# ============================================================================

class MarketConditions(BaseModel):
    """Current market conditions and metrics"""
    symbol: str
    current_price: Decimal
    iv_percentile: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class OptionLeg(BaseModel):
    """Individual option leg in a strategy"""
    action: OrderSide  # buy or sell
    instrument: OptionType  # call or put
    strike: Decimal
    expiry: date
    quantity: int
    premium: Optional[Decimal] = None
    
    @field_validator('quantity')
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v

class RiskConstraints(BaseModel):
    """Risk management constraints"""
    max_loss: Optional[Decimal] = None
    max_position_size: Optional[int] = None
    max_portfolio_concentration: Optional[float] = None
    required_margin: Optional[Decimal] = None
    
    @field_validator('max_portfolio_concentration')
    @classmethod
    def concentration_range(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Portfolio concentration must be between 0 and 1')
        return v

class TradePlan(BaseModel):
    """High-level trade plan from AI analysis"""
    symbol: str
    thesis: str  # market outlook/reasoning
    strategy_type: StrategyType
    target_profit: Optional[Decimal] = None
    max_risk: Optional[Decimal] = None
    time_horizon: Optional[str] = None
    confidence: Optional[float] = None  # 0-1 confidence score
    
    @field_validator('confidence')
    @classmethod
    def confidence_range(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Confidence must be between 0 and 1')
        return v

class OptionsOrder(BaseModel):
    """Complete options order structure"""
    symbol: str
    strategy_type: StrategyType
    legs: List[OptionLeg]
    risk_constraints: Optional[RiskConstraints] = None
    order_type: OrderType = OrderType.LIMIT
    time_in_force: str = "GTC"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('legs')
    @classmethod
    def legs_not_empty(cls, v):
        if not v:
            raise ValueError('Order must have at least one leg')
        return v
    
    @model_validator(mode='after')
    def validate_strategy_legs(self):
        """Validate that legs match the strategy type"""
        strategy = self.strategy_type
        legs = self.legs
        
        if strategy == StrategyType.IRON_CONDOR and len(legs) != 4:
            raise ValueError('Iron condor must have exactly 4 legs')
        elif strategy in [StrategyType.PUT_CREDIT_SPREAD, StrategyType.CALL_CREDIT_SPREAD] and len(legs) != 2:
            raise ValueError('Credit spreads must have exactly 2 legs')
        elif strategy in [StrategyType.LONG_CALL, StrategyType.LONG_PUT, StrategyType.SHORT_CALL, StrategyType.SHORT_PUT] and len(legs) != 1:
            raise ValueError('Single leg strategies must have exactly 1 leg')
        
        return self

class OrderValidation(BaseModel):
    """Order validation results"""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    risk_score: Optional[float] = None  # 0-100 risk score
    estimated_margin: Optional[Decimal] = None

class RiskViolation(BaseModel):
    """Risk violation details"""
    rule: str
    severity: RiskLevel
    message: str
    current_value: Optional[Union[float, Decimal]] = None
    limit_value: Optional[Union[float, Decimal]] = None

class RiskAssessment(BaseModel):
    """Comprehensive risk assessment"""
    overall_risk: RiskLevel
    risk_score: float  # 0-100
    violations: List[RiskViolation] = Field(default_factory=list)
    max_loss: Optional[Decimal] = None
    required_margin: Optional[Decimal] = None
    portfolio_impact: Optional[float] = None  # % of portfolio
    
    @field_validator('risk_score')
    @classmethod
    def risk_score_range(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Risk score must be between 0 and 100')
        return v

class Portfolio(BaseModel):
    """Portfolio state for risk calculations"""
    total_equity: Decimal
    available_cash: Decimal
    current_positions: List[Dict[str, Any]] = Field(default_factory=list)
    total_risk: float = 0.0  # Current portfolio risk as percentage
    
    @field_validator('total_risk')
    @classmethod
    def risk_percentage(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Total risk must be between 0 and 1')
        return v


# ============================================================================
# Analysis and Synthesis Models
# ============================================================================

class MarketAnalysis(BaseModel):
    """LLM-generated market analysis"""
    symbol: str
    outlook: str  # bullish, bearish, neutral, volatile
    reasoning: str
    time_horizon: str
    confidence: float
    key_factors: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.now)

class StrategyRecommendation(BaseModel):
    """Synthesized strategy recommendation"""
    strategy_type: StrategyType
    rationale: str
    expected_profit: Optional[Decimal] = None
    max_risk: Optional[Decimal] = None
    probability_of_profit: Optional[float] = None
    legs: List[OptionLeg]
    
    @field_validator('probability_of_profit')
    @classmethod
    def pop_range(cls, v):
        if v is not None and (v < 0 or v > 1):
            raise ValueError('Probability of profit must be between 0 and 1')
        return v


# ============================================================================
# Voice Interface Models
# ============================================================================

class VoiceCommand(BaseModel):
    """Voice command input"""
    text: str
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.now)
    
    @field_validator('confidence')
    @classmethod
    def confidence_range_voice(cls, v):
        if v < 0 or v > 1:
            raise ValueError('Confidence must be between 0 and 1')
        return v

class VoiceResponse(BaseModel):
    """Voice response output"""
    text: str
    audio_url: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# ============================================================================
# Integration Models
# ============================================================================

class Phase3Request(BaseModel):
    """Complete Phase 3 system request"""
    user_input: str  # Natural language request
    context: Dict[str, Any] = Field(default_factory=dict)
    voice_mode: bool = False
    max_risk: Optional[Decimal] = None
    portfolio_constraints: Optional[Dict[str, Any]] = None

class Phase3Response(BaseModel):
    """Complete Phase 3 system response"""
    success: bool
    message: str
    order: Optional[OptionsOrder] = None
    analysis: Optional[MarketAnalysis] = None
    risk_assessment: Optional[RiskAssessment] = None
    voice_response: Optional[VoiceResponse] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Example usage and validation
# ============================================================================

def create_sample_iron_condor() -> OptionsOrder:
    """Create a sample iron condor order for testing"""
    return OptionsOrder(
        symbol="SPY",
        strategy_type=StrategyType.IRON_CONDOR,
        legs=[
            OptionLeg(action=OrderSide.SELL, instrument=OptionType.PUT, strike=Decimal("440"), expiry=date(2025, 1, 17), quantity=1),
            OptionLeg(action=OrderSide.BUY, instrument=OptionType.PUT, strike=Decimal("435"), expiry=date(2025, 1, 17), quantity=1),
            OptionLeg(action=OrderSide.SELL, instrument=OptionType.CALL, strike=Decimal("460"), expiry=date(2025, 1, 17), quantity=1),
            OptionLeg(action=OrderSide.BUY, instrument=OptionType.CALL, strike=Decimal("465"), expiry=date(2025, 1, 17), quantity=1),
        ],
        risk_constraints=RiskConstraints(max_loss=Decimal("500")),
        metadata={"created_by": "phase3_test"}
    )

if __name__ == "__main__":
    # Test schema validation
    try:
        order = create_sample_iron_condor()
        print("✅ Schema validation successful")
        print(f"Order: {order.symbol} {order.strategy_type} with {len(order.legs)} legs")
        
        # Test JSON serialization
        json_data = order.json()
        print(f"✅ JSON serialization successful ({len(json_data)} chars)")
        
        # Test deserialization
        rebuilt = OptionsOrder.parse_raw(json_data)
        print(f"✅ JSON deserialization successful: {rebuilt.symbol}")
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")