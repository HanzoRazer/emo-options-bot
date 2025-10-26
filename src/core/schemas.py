# src/core/schemas.py
"""
Core data schemas for EMO Options Bot
Production-ready with enhanced validation and graceful fallbacks
"""
from __future__ import annotations
from typing import List, Optional, Literal, Dict, Any, Union
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime, date
import logging
from decimal import Decimal
import json

# Configure logging
logger = logging.getLogger(__name__)

# Type aliases for better readability
Side = Literal["buy", "sell"]
OptType = Literal["call", "put"]
StrategyType = Literal[
    "iron_condor", "put_credit_spread", "covered_call", 
    "protective_put", "straddle", "strangle", "calendar_spread",
    "butterfly", "condor", "collar", "custom"
]
OutlookType = Literal["bullish", "bearish", "neutral", "volatile", "unknown"]
SeverityType = Literal["info", "warn", "error", "critical"]
InstrumentType = Literal["stock", "call", "put", "future", "etf"]

class EnhancedBaseModel(BaseModel):
    """Base model with enhanced error handling and serialization"""
    
    class Config:
        # Enable validation on assignment
        validate_assignment = True
        # Use enum values instead of names
        use_enum_values = True
        # Allow population by field name or alias
        allow_population_by_field_name = True
        # Serialize datetime as ISO format
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
            date: lambda v: v.isoformat() if v else None,
            Decimal: lambda v: float(v) if v is not None else None,
        }
    
    def safe_dict(self) -> Dict[str, Any]:
        """Convert to dict with error handling"""
        try:
            return self.dict()
        except Exception as e:
            logger.warning(f"Error converting {self.__class__.__name__} to dict: {e}")
            return {"error": str(e), "type": self.__class__.__name__}
    
    def safe_json(self, **kwargs) -> str:
        """Convert to JSON with error handling"""
        try:
            return self.json(**kwargs)
        except Exception as e:
            logger.warning(f"Error converting {self.__class__.__name__} to JSON: {e}")
            return json.dumps({"error": str(e), "type": self.__class__.__name__})

class RiskConstraints(EnhancedBaseModel):
    """Enhanced risk constraints with validation and defaults"""
    max_risk_dollars: Optional[float] = Field(None, ge=0, description="Maximum risk in dollars")
    max_risk_pct: Optional[float] = Field(None, ge=0, le=1.0, description="Maximum risk as % of equity")
    max_spread_width: Optional[float] = Field(None, ge=0, description="Maximum spread width in dollars")
    min_premium: Optional[float] = Field(None, ge=0, description="Minimum premium to collect")
    max_premium: Optional[float] = Field(None, ge=0, description="Maximum premium to pay")
    time_horizon_days: Optional[int] = Field(None, ge=1, le=365, description="Trade time horizon in days")
    max_delta_exposure: Optional[float] = Field(None, ge=-10, le=10, description="Maximum delta exposure")
    max_vega_exposure: Optional[float] = Field(None, ge=-1000, le=1000, description="Maximum vega exposure")
    min_theta_per_day: Optional[float] = Field(None, description="Minimum theta per day target")
    max_gamma_risk: Optional[float] = Field(None, ge=0, description="Maximum gamma risk")
    notes: Optional[str] = Field(None, max_length=500, description="Risk notes and comments")
    
    @validator('max_risk_pct')
    def validate_risk_percentage(cls, v):
        if v is not None and (v < 0 or v > 0.5):  # Cap at 50% for safety
            logger.warning(f"Risk percentage {v} seems excessive, consider review")
        return v
    
    @root_validator
    def validate_risk_consistency(cls, values):
        max_pct = values.get('max_risk_pct')
        max_dollars = values.get('max_risk_dollars')
        
        if max_pct and max_pct > 0.25:  # 25% cap for safety
            logger.warning(f"Risk percentage {max_pct} exceeds recommended 25% limit")
        
        if max_dollars and max_dollars > 50000:  # $50k cap for safety
            logger.warning(f"Risk dollars {max_dollars} exceeds recommended $50k limit")
            
        return values

class TradeLeg(EnhancedBaseModel):
    """Enhanced trade leg with comprehensive validation"""
    action: Side = Field(..., description="Buy or sell action")
    instrument: InstrumentType = Field(..., description="Type of instrument")
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    strike: Optional[float] = Field(None, ge=0, description="Option strike price")
    expiry: Optional[Union[str, date]] = Field(None, description="Expiration date (YYYY-MM-DD)")
    quantity: int = Field(..., ne=0, description="Number of contracts/shares")
    price: Optional[float] = Field(None, ge=0, description="Execution price")
    order_type: Optional[str] = Field("market", description="Order type (market, limit, etc.)")
    time_in_force: Optional[str] = Field("day", description="Time in force (day, gtc, etc.)")
    memo: Optional[str] = Field(None, max_length=200, description="Trade memo/notes")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if v:
            v = v.upper().strip()
            if not v.isalnum():
                raise ValueError("Symbol must contain only alphanumeric characters")
        return v
    
    @validator('expiry')
    def validate_expiry(cls, v):
        if isinstance(v, str):
            try:
                # Parse and validate date format
                parsed_date = datetime.strptime(v, "%Y-%m-%d").date()
                if parsed_date < date.today():
                    logger.warning(f"Expiry date {v} is in the past")
                return v
            except ValueError:
                raise ValueError("Expiry must be in YYYY-MM-DD format")
        elif isinstance(v, date):
            return v.isoformat()
        return v
    
    @root_validator
    def validate_options_fields(cls, values):
        instrument = values.get('instrument')
        strike = values.get('strike')
        expiry = values.get('expiry')
        
        if instrument in ['call', 'put']:
            if strike is None:
                raise ValueError(f"Strike price required for {instrument}")
            if expiry is None:
                raise ValueError(f"Expiry date required for {instrument}")
                
        return values

class TradePlan(EnhancedBaseModel):
    """Enhanced trade plan with comprehensive validation and metadata"""
    strategy_type: StrategyType = Field(..., description="Type of trading strategy")
    underlying: str = Field(..., min_length=1, max_length=10, description="Underlying symbol")
    legs: List[TradeLeg] = Field(default_factory=list, description="Trade legs")
    risk_constraints: RiskConstraints = Field(default_factory=RiskConstraints, description="Risk parameters")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    status: str = Field("draft", description="Plan status (draft, validated, executed, etc.)")
    tags: List[str] = Field(default_factory=list, description="Strategy tags")
    
    @validator("underlying")
    def validate_underlying(cls, v):
        return v.upper().strip() if v else v
    
    @validator("legs")
    def validate_legs(cls, v):
        if not v:
            raise ValueError("TradePlan must include at least one leg")
        
        # Basic validation for common issues
        if len(v) > 10:  # Reasonable limit for complex strategies
            logger.warning(f"Trade plan has {len(v)} legs, which is unusual")
            
        return v
    
    @root_validator
    def validate_strategy_consistency(cls, values):
        strategy_type = values.get('strategy_type')
        legs = values.get('legs', [])
        
        # Basic strategy validation
        if strategy_type == 'iron_condor' and len(legs) != 4:
            logger.warning("Iron condor typically requires 4 legs")
        elif strategy_type == 'put_credit_spread' and len(legs) != 2:
            logger.warning("Put credit spread typically requires 2 legs")
        elif strategy_type == 'covered_call' and len(legs) != 2:
            logger.warning("Covered call typically requires 2 legs")
            
        # Update timestamp
        values['updated_at'] = datetime.utcnow()
        
        return values
    
    def estimate_max_risk(self, current_price: Optional[float] = None) -> float:
        """Estimate maximum risk for the trade plan"""
        try:
            if self.risk_constraints.max_risk_dollars:
                return self.risk_constraints.max_risk_dollars
                
            # For spread strategies, estimate based on spread width
            if self.strategy_type in ['put_credit_spread', 'call_credit_spread']:
                strikes = [leg.strike for leg in self.legs if leg.strike is not None]
                if len(strikes) >= 2:
                    spread_width = abs(max(strikes) - min(strikes))
                    return spread_width * 100  # Standard options multiplier
            
            # Default fallback
            return 1000.0  # Conservative default
            
        except Exception as e:
            logger.warning(f"Error estimating max risk: {e}")
            return 1000.0

class Violation(EnhancedBaseModel):
    """Enhanced violation with categorization and context"""
    code: str = Field(..., description="Violation code")
    message: str = Field(..., description="Human-readable violation message")
    severity: SeverityType = Field("error", description="Violation severity level")
    category: Optional[str] = Field(None, description="Violation category (risk, compliance, etc.)")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional violation data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Violation timestamp")
    source: Optional[str] = Field(None, description="Source system/component")
    suggested_action: Optional[str] = Field(None, description="Suggested remediation action")
    
    def is_blocking(self) -> bool:
        """Check if violation should block trade execution"""
        return self.severity in ['error', 'critical']
    
    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.code}: {self.message}"

class PortfolioPosition(EnhancedBaseModel):
    """Enhanced portfolio position with Greeks and P&L tracking"""
    symbol: str = Field(..., description="Position symbol")
    qty: float = Field(..., description="Position quantity")
    avg_price: float = Field(..., ge=0, description="Average entry price")
    current_price: Optional[float] = Field(None, ge=0, description="Current market price")
    kind: InstrumentType = Field("stock", description="Instrument type")
    expiry: Optional[str] = Field(None, description="Option expiry (if applicable)")
    strike: Optional[float] = Field(None, description="Option strike (if applicable)")
    
    # Greeks and risk metrics
    delta: Optional[float] = Field(None, description="Position delta")
    gamma: Optional[float] = Field(None, description="Position gamma")
    theta: Optional[float] = Field(None, description="Position theta")
    vega: Optional[float] = Field(None, description="Position vega")
    
    # P&L tracking
    unrealized_pnl: Optional[float] = Field(None, description="Unrealized P&L")
    realized_pnl: Optional[float] = Field(None, description="Realized P&L")
    
    # Metadata
    opened_at: Optional[datetime] = Field(None, description="Position open timestamp")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    def calculate_market_value(self) -> float:
        """Calculate current market value of position"""
        try:
            price = self.current_price or self.avg_price
            if self.kind in ['call', 'put']:
                return self.qty * price * 100  # Options multiplier
            else:
                return self.qty * price
        except Exception as e:
            logger.warning(f"Error calculating market value for {self.symbol}: {e}")
            return 0.0
    
    def calculate_unrealized_pnl(self) -> float:
        """Calculate unrealized P&L"""
        try:
            if self.current_price is None:
                return 0.0
                
            price_diff = self.current_price - self.avg_price
            if self.kind in ['call', 'put']:
                return self.qty * price_diff * 100  # Options multiplier
            else:
                return self.qty * price_diff
        except Exception as e:
            logger.warning(f"Error calculating unrealized P&L for {self.symbol}: {e}")
            return 0.0

class PortfolioSnapshot(EnhancedBaseModel):
    """Enhanced portfolio snapshot with comprehensive risk metrics"""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Snapshot timestamp")
    equity: float = Field(..., ge=0, description="Total portfolio equity")
    cash: Optional[float] = Field(None, ge=0, description="Available cash")
    buying_power: Optional[float] = Field(None, ge=0, description="Available buying power")
    positions: List[PortfolioPosition] = Field(default_factory=list, description="Current positions")
    
    # Risk metrics
    risk_exposure_pct: float = Field(0.0, ge=0, le=1.0, description="Current portfolio risk exposure %")
    daily_pnl: Optional[float] = Field(None, description="Daily P&L")
    total_pnl: Optional[float] = Field(None, description="Total P&L")
    
    # Greeks aggregation
    greek_exposure: Dict[str, float] = Field(
        default_factory=lambda: {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0},
        description="Aggregated Greek exposures"
    )
    
    # Risk limits and alerts
    risk_alerts: List[Violation] = Field(default_factory=list, description="Active risk alerts")
    margin_requirements: Optional[Dict[str, float]] = Field(None, description="Margin requirements")
    
    def calculate_total_market_value(self) -> float:
        """Calculate total market value of all positions"""
        try:
            return sum(pos.calculate_market_value() for pos in self.positions)
        except Exception as e:
            logger.warning(f"Error calculating total market value: {e}")
            return 0.0
    
    def calculate_concentration_risk(self) -> Dict[str, float]:
        """Calculate position concentration by symbol"""
        try:
            total_value = self.calculate_total_market_value()
            if total_value <= 0:
                return {}
                
            concentrations = {}
            for pos in self.positions:
                symbol = pos.symbol
                value = pos.calculate_market_value()
                concentrations[symbol] = concentrations.get(symbol, 0) + (value / total_value)
                
            return concentrations
        except Exception as e:
            logger.warning(f"Error calculating concentration risk: {e}")
            return {}
    
    def get_top_positions(self, limit: int = 10) -> List[PortfolioPosition]:
        """Get top positions by market value"""
        try:
            return sorted(
                self.positions,
                key=lambda p: abs(p.calculate_market_value()),
                reverse=True
            )[:limit]
        except Exception as e:
            logger.warning(f"Error getting top positions: {e}")
            return []

class AnalysisPlan(EnhancedBaseModel):
    """Enhanced structured LLM output with validation and confidence tracking"""
    intent: str = Field(..., min_length=1, description="Trading intent description")
    thesis: str = Field(..., min_length=1, description="Investment thesis")
    underlying: str = Field(..., min_length=1, max_length=10, description="Underlying symbol")
    outlook: OutlookType = Field(..., description="Market outlook")
    confidence: float = Field(0.6, ge=0.0, le=1.0, description="Confidence score (0-1)")
    strategy_hint: Optional[StrategyType] = Field(None, description="Suggested strategy type")
    risk: RiskConstraints = Field(default_factory=RiskConstraints, description="Risk constraints")
    
    # Enhanced fields
    time_horizon: Optional[str] = Field(None, description="Expected time horizon (e.g., '1-2 weeks')")
    key_catalysts: List[str] = Field(default_factory=list, description="Key market catalysts")
    key_risks: List[str] = Field(default_factory=list, description="Key risk factors")
    target_profit: Optional[float] = Field(None, ge=0, description="Target profit ($)")
    stop_loss: Optional[float] = Field(None, ge=0, description="Stop loss ($)")
    
    # Metadata
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    source: Optional[str] = Field(None, description="Analysis source (llm, heuristic, manual)")
    model_version: Optional[str] = Field(None, description="Model version used for analysis")
    
    @validator("underlying")
    def validate_underlying_symbol(cls, v):
        return v.upper().strip() if v else v
    
    @validator("confidence")
    def validate_confidence_range(cls, v):
        if v < 0.1:
            logger.warning(f"Very low confidence score: {v}")
        elif v > 0.95:
            logger.warning(f"Unusually high confidence score: {v}")
        return v
    
    def get_risk_level(self) -> str:
        """Categorize overall risk level"""
        if self.confidence < 0.3:
            return "high"
        elif self.confidence < 0.6:
            return "medium"
        else:
            return "low"
    
    def to_trade_plan(self) -> TradePlan:
        """Convert analysis to basic trade plan structure"""
        return TradePlan(
            strategy_type=self.strategy_hint or "custom",
            underlying=self.underlying,
            risk_constraints=self.risk,
            metadata={
                "source": "analysis_plan",
                "confidence": self.confidence,
                "outlook": self.outlook,
                "thesis": self.thesis,
                "intent": self.intent
            },
            tags=["ai_generated", f"outlook_{self.outlook}", f"confidence_{self.get_risk_level()}"]
        )

# Utility functions for schema validation and error handling
def validate_trade_plan_safely(data: Dict[str, Any]) -> tuple[Optional[TradePlan], List[str]]:
    """Safely validate and create TradePlan with error collection"""
    errors = []
    try:
        plan = TradePlan(**data)
        return plan, errors
    except Exception as e:
        errors.append(f"TradePlan validation error: {str(e)}")
        logger.error(f"Failed to validate TradePlan: {e}")
        return None, errors

def create_default_risk_constraints(equity: float = 10000.0) -> RiskConstraints:
    """Create sensible default risk constraints based on portfolio size"""
    return RiskConstraints(
        max_risk_pct=0.02,  # 2% max risk
        max_risk_dollars=min(equity * 0.02, 500.0),  # Cap at $500
        time_horizon_days=30,
        notes="Auto-generated default constraints"
    )

# Export all schemas for easy importing
__all__ = [
    "Side", "OptType", "StrategyType", "OutlookType", "SeverityType", "InstrumentType",
    "EnhancedBaseModel", "RiskConstraints", "TradeLeg", "TradePlan", 
    "Violation", "PortfolioPosition", "PortfolioSnapshot", "AnalysisPlan",
    "validate_trade_plan_safely", "create_default_risk_constraints"
]