"""
LLM Schemas for EMO Options Bot Phase 3
Pydantic models for structured LLM I/O with validation.
"""

from __future__ import annotations
from datetime import datetime, date
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
import json

class OutlookType(str, Enum):
    """Market outlook types."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    VOLATILE = "volatile"
    CALM = "calm"

class StrategyType(str, Enum):
    """Available strategy types."""
    IRON_CONDOR = "iron_condor"
    PUT_CREDIT_SPREAD = "put_credit_spread"
    CALL_CREDIT_SPREAD = "call_credit_spread"
    COVERED_CALL = "covered_call"
    PROTECTIVE_PUT = "protective_put"
    LONG_STRADDLE = "long_straddle"
    SHORT_STRADDLE = "short_straddle"
    LONG_STRANGLE = "long_strangle"
    SHORT_STRANGLE = "short_strangle"
    COLLAR = "collar"

class ConfidenceLevel(str, Enum):
    """Confidence levels for decisions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class RiskLevel(str, Enum):
    """Risk levels for trades."""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    SPECULATIVE = "speculative"

class DataCitation(BaseModel):
    """Citation for data sources used in decision making."""
    source: str = Field(..., description="Data source name")
    value: Union[float, str, int] = Field(..., description="Actual value")
    timestamp: datetime = Field(..., description="When data was retrieved")
    confidence: float = Field(ge=0.0, le=1.0, description="Data quality confidence")
    
class Constraint(BaseModel):
    """Trading constraints and limits."""
    max_loss_pct: Optional[float] = Field(None, ge=0.0, le=100.0, description="Max loss as % of account")
    max_margin: Optional[float] = Field(None, ge=0.0, description="Maximum margin requirement")
    max_positions: Optional[int] = Field(None, ge=1, description="Max open positions")
    avoid_earnings: bool = Field(True, description="Avoid trades through earnings")
    min_days_to_expiry: Optional[int] = Field(None, ge=0, description="Minimum DTE")
    max_days_to_expiry: Optional[int] = Field(None, ge=0, description="Maximum DTE")
    min_liquidity: Optional[float] = Field(None, ge=0.0, description="Minimum option volume/OI")

class RiskMetrics(BaseModel):
    """Risk assessment metrics."""
    max_loss: float = Field(..., description="Maximum possible loss")
    probability_of_profit: Optional[float] = Field(None, ge=0.0, le=1.0, description="Estimated PoP")
    breakeven_points: List[float] = Field(default_factory=list, description="Breakeven prices")
    theta_decay: Optional[float] = Field(None, description="Daily theta decay")
    vega_exposure: Optional[float] = Field(None, description="IV sensitivity")
    delta_exposure: Optional[float] = Field(None, description="Directional exposure")
    
class Mitigation(BaseModel):
    """Risk mitigation strategy."""
    risk: str = Field(..., description="Identified risk")
    mitigation: str = Field(..., description="How to mitigate the risk")
    probability: float = Field(ge=0.0, le=1.0, description="Probability of risk occurring")
    impact: str = Field(..., description="Impact if risk occurs")

class Rationale(BaseModel):
    """Reasoning and rationale for trade decisions."""
    summary: str = Field(..., description="Brief summary of reasoning")
    key_factors: List[str] = Field(..., description="Key decision factors")
    data_citations: List[DataCitation] = Field(..., description="Supporting data")
    assumptions: List[str] = Field(default_factory=list, description="Key assumptions")
    what_could_go_wrong: List[Mitigation] = Field(..., description="Risk analysis")
    confidence: ConfidenceLevel = Field(..., description="Overall confidence level")
    alternative_strategies: List[str] = Field(default_factory=list, description="Alternative approaches considered")

class TradePlan(BaseModel):
    """High-level trade plan from LLM orchestrator."""
    symbol: str = Field(..., description="Trading symbol")
    outlook: OutlookType = Field(..., description="Market outlook")
    strategy_type: StrategyType = Field(..., description="Recommended strategy")
    horizon_days: int = Field(..., ge=1, le=365, description="Trade horizon in days")
    risk_level: RiskLevel = Field(..., description="Risk assessment")
    constraints: Constraint = Field(..., description="Trading constraints")
    rationale: Rationale = Field(..., description="Decision reasoning")
    target_return: Optional[float] = Field(None, description="Expected return %")
    notes: str = Field(default="", description="Additional notes")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    model_version: str = Field(..., description="LLM model version used")
    prompt_hash: str = Field(..., description="Hash of prompt used")
    
class OptionLeg(BaseModel):
    """Individual option leg in a strategy."""
    side: str = Field(..., regex="^(buy|sell)$", description="Buy or sell")
    option_type: str = Field(..., regex="^(call|put)$", description="Call or put")
    strike: float = Field(..., gt=0, description="Strike price")
    expiry: date = Field(..., description="Expiration date")
    quantity: int = Field(..., gt=0, description="Number of contracts")
    premium: Optional[float] = Field(None, description="Premium price")
    
class ExitRule(BaseModel):
    """Exit rules for position management."""
    take_profit: Optional[float] = Field(None, ge=0.0, le=1.0, description="Take profit at % of max profit")
    stop_loss: Optional[float] = Field(None, ge=1.0, description="Stop loss at multiple of credit")
    time_decay: Optional[int] = Field(None, ge=1, description="Exit at DTE threshold")
    delta_threshold: Optional[float] = Field(None, description="Exit if delta exceeds threshold")
    
class StrategySpec(BaseModel):
    """Detailed strategy specification for execution."""
    strategy_type: StrategyType = Field(..., description="Strategy type")
    legs: List[OptionLeg] = Field(..., description="Option legs")
    max_risk: float = Field(..., description="Maximum risk amount")
    target_credit: Optional[float] = Field(None, description="Target credit received")
    exit_rules: ExitRule = Field(..., description="Exit management rules")
    
    # Risk metrics
    risk_metrics: RiskMetrics = Field(..., description="Computed risk metrics")
    
    # Validation and approval
    validated: bool = Field(False, description="Passed validation checks")
    approved: bool = Field(False, description="Human approved")
    risk_gate_passed: bool = Field(False, description="Passed risk gate checks")
    
    # Metadata
    created_from_plan: Optional[str] = Field(None, description="Source TradePlan ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class BacktestRequest(BaseModel):
    """Request for strategy backtesting."""
    strategy_spec: StrategySpec = Field(..., description="Strategy to backtest")
    start_date: date = Field(..., description="Backtest start date")
    end_date: date = Field(..., description="Backtest end date")
    initial_capital: float = Field(default=100000, gt=0, description="Starting capital")
    symbols: List[str] = Field(..., description="Symbols to test on")
    
class BacktestResult(BaseModel):
    """Results from strategy backtesting."""
    total_return: float = Field(..., description="Total return %")
    win_rate: float = Field(..., ge=0.0, le=1.0, description="Win rate")
    profit_factor: float = Field(..., description="Profit factor")
    max_drawdown: float = Field(..., description="Maximum drawdown %")
    sharpe_ratio: Optional[float] = Field(None, description="Sharpe ratio")
    total_trades: int = Field(..., ge=0, description="Number of trades")
    
class AuditEntry(BaseModel):
    """Audit trail entry for decisions and actions."""
    entry_id: str = Field(..., description="Unique audit entry ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action: str = Field(..., description="Action taken")
    user_id: Optional[str] = Field(None, description="User who triggered action")
    inputs: Dict[str, Any] = Field(..., description="Input data")
    outputs: Dict[str, Any] = Field(..., description="Output data")
    model_version: Optional[str] = Field(None, description="Model version if applicable")
    success: bool = Field(..., description="Whether action succeeded")
    error_message: Optional[str] = Field(None, description="Error if failed")
    
class FeedbackEntry(BaseModel):
    """Feedback for learning loop."""
    trade_id: str = Field(..., description="Trade identifier")
    strategy_spec_hash: str = Field(..., description="Hash of strategy used")
    actual_return: float = Field(..., description="Actual return achieved")
    planned_return: Optional[float] = Field(None, description="Expected return")
    exit_reason: str = Field(..., description="How trade was closed")
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="User satisfaction rating")
    notes: str = Field(default="", description="Additional feedback notes")
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Utility functions for schema operations
def serialize_model(model: BaseModel) -> str:
    """Serialize a pydantic model to JSON string."""
    return model.model_dump_json(exclude_none=True, by_alias=True)

def parse_trade_plan(json_str: str) -> TradePlan:
    """Parse JSON string into TradePlan with validation."""
    return TradePlan.model_validate_json(json_str)

def parse_strategy_spec(json_str: str) -> StrategySpec:
    """Parse JSON string into StrategySpec with validation."""
    return StrategySpec.model_validate_json(json_str)

def get_schema_json(model_class) -> Dict[str, Any]:
    """Get JSON schema for a model class."""
    return model_class.model_json_schema()

# Export commonly used schemas for prompt generation
TRADE_PLAN_SCHEMA = get_schema_json(TradePlan)
STRATEGY_SPEC_SCHEMA = get_schema_json(StrategySpec)
RATIONALE_SCHEMA = get_schema_json(Rationale)