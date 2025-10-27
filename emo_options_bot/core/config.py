"""Configuration management for EMO Options Bot."""

from typing import Optional
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

load_dotenv()


class AIConfig(BaseModel):
    """AI/NLP configuration."""
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    model: str = "gpt-4"
    temperature: float = 0.1
    max_tokens: int = 2000


class RiskConfig(BaseModel):
    """Risk management configuration."""
    max_position_size: float = 10000.0
    max_portfolio_exposure: float = 50000.0
    max_loss_per_trade: float = 1000.0
    max_loss_per_day: float = 5000.0
    enable_risk_checks: bool = True


class TradingConfig(BaseModel):
    """Trading configuration."""
    default_account: str = "paper"
    enable_paper_trading: bool = True
    require_manual_approval: bool = True
    max_orders_per_day: int = 50


class MarketDataConfig(BaseModel):
    """Market data configuration."""
    data_provider: str = "yahoo"
    update_interval_seconds: int = 60
    cache_enabled: bool = True


class Config(BaseModel):
    """Main configuration class."""
    ai: AIConfig = Field(default_factory=AIConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    trading: TradingConfig = Field(default_factory=TradingConfig)
    market_data: MarketDataConfig = Field(default_factory=MarketDataConfig)
    
    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """Load configuration from file or environment."""
        if config_path and os.path.exists(config_path):
            import json
            with open(config_path, 'r') as f:
                return cls(**json.load(f))
        return cls()
