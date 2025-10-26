"""
Robust Configuration Management System
Provides centralized, validated configuration with environment-specific overrides
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"

class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass

@dataclass
class ConfigSection:
    """Base configuration section with validation."""
    
    def validate(self) -> List[str]:
        """Validate configuration section. Return list of errors."""
        return []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

@dataclass
class AIConfig(ConfigSection):
    """AI/LLM provider configuration."""
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 1000
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-haiku-20240307"
    provider_order: List[str] = field(default_factory=lambda: ["openai", "anthropic", "mock"])
    fallback_enabled: bool = True
    
    def validate(self) -> List[str]:
        errors = []
        
        # At least one AI provider should be configured
        if not self.openai_api_key and not self.anthropic_api_key:
            errors.append("At least one AI provider (OpenAI or Anthropic) should be configured")
        
        # Validate API key formats
        if self.openai_api_key and not self.openai_api_key.startswith('sk-'):
            errors.append("OpenAI API key should start with 'sk-'")
        
        if self.anthropic_api_key and not self.anthropic_api_key.startswith('sk-ant-'):
            errors.append("Anthropic API key should start with 'sk-ant-'")
        
        # Validate token limits
        if self.openai_max_tokens < 100 or self.openai_max_tokens > 4000:
            errors.append("OpenAI max_tokens should be between 100 and 4000")
        
        return errors

@dataclass
class TradingConfig(ConfigSection):
    """Trading and broker configuration."""
    alpaca_key_id: Optional[str] = None
    alpaca_secret_key: Optional[str] = None
    alpaca_api_base: str = "https://paper-api.alpaca.markets"
    alpaca_data_url: str = "https://data.alpaca.markets/v2"
    polygon_api_key: Optional[str] = None
    broker: str = "alpaca"
    order_mode: str = "stage"  # stage, paper, live
    live_confirm: Optional[str] = None
    paper_trading: bool = True
    
    def validate(self) -> List[str]:
        errors = []
        
        # Check required keys for non-stage modes
        if self.order_mode in ["paper", "live"]:
            if not self.alpaca_key_id or not self.alpaca_secret_key:
                errors.append(f"Alpaca credentials required for {self.order_mode} mode")
        
        # Validate order mode
        if self.order_mode not in ["stage", "paper", "live"]:
            errors.append("order_mode must be 'stage', 'paper', or 'live'")
        
        # Live trading safety check
        if self.order_mode == "live":
            if self.live_confirm != "I_UNDERSTAND_THE_RISK":
                errors.append("Live trading requires EMO_LIVE_CONFIRM='I_UNDERSTAND_THE_RISK'")
            if self.paper_trading:
                errors.append("paper_trading must be False for live trading")
        
        return errors

@dataclass
class RiskConfig(ConfigSection):
    """Risk management configuration."""
    max_position_size_pct: float = 0.05
    max_portfolio_risk_pct: float = 0.10
    max_single_trade_risk: float = 5000.0
    risk_validation_enabled: bool = True
    auto_approval_limit: float = 1000.0
    require_manual_approval: bool = True
    
    def validate(self) -> List[str]:
        errors = []
        
        # Validate percentages
        if not 0.001 <= self.max_position_size_pct <= 1.0:
            errors.append("max_position_size_pct must be between 0.1% and 100%")
        
        if not 0.001 <= self.max_portfolio_risk_pct <= 1.0:
            errors.append("max_portfolio_risk_pct must be between 0.1% and 100%")
        
        # Validate dollar amounts
        if self.max_single_trade_risk <= 0:
            errors.append("max_single_trade_risk must be positive")
        
        if self.auto_approval_limit <= 0:
            errors.append("auto_approval_limit must be positive")
        
        # Risk validation should be enabled in production
        if not self.risk_validation_enabled:
            errors.append("WARNING: risk_validation_enabled is False")
        
        return errors

@dataclass
class SystemConfig(ConfigSection):
    """System and operational configuration."""
    environment: Environment = Environment.DEVELOPMENT
    staging_dir: str = "ops/staged_orders"
    backup_dir: str = "ops/staged_orders/backup"
    log_level: str = "INFO"
    log_file: str = "logs/emo_bot.log"
    database_url: str = "sqlite:///data/emo_options.db"
    dashboard_port: int = 8083
    dashboard_host: str = "0.0.0.0"
    secret_key: Optional[str] = None
    
    def validate(self) -> List[str]:
        errors = []
        
        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_levels:
            errors.append(f"log_level must be one of {valid_levels}")
        
        # Validate port
        if not 1024 <= self.dashboard_port <= 65535:
            errors.append("dashboard_port must be between 1024 and 65535")
        
        # Secret key should be set in production
        if self.environment == Environment.PRODUCTION and not self.secret_key:
            errors.append("secret_key must be set in production environment")
        
        return errors

class RobustConfig:
    """
    Robust configuration management with validation and environment overrides.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.env_file = self.project_root / ".env"
        self.config_dir = self.project_root / "config"
        
        # Configuration sections
        self.ai = AIConfig()
        self.trading = TradingConfig()
        self.risk = RiskConfig()
        self.system = SystemConfig()
        
        # Load configuration
        self._load_configuration()
        
        # Validation results
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
    
    def _load_configuration(self):
        """Load configuration from environment and files."""
        # Load from .env file if it exists
        if self.env_file.exists():
            self._load_env_file()
        
        # Load from environment variables
        self._load_from_environment()
        
        # Load from config files
        self._load_config_files()
    
    def _load_env_file(self):
        """Load configuration from .env file."""
        try:
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
        except Exception as e:
            logging.warning(f"Could not load .env file: {e}")
    
    def _load_from_environment(self):
        """Load configuration from environment variables."""
        # AI Configuration
        self.ai.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.ai.openai_model = os.getenv("OPENAI_MODEL", self.ai.openai_model)
        self.ai.openai_max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", self.ai.openai_max_tokens))
        self.ai.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.ai.anthropic_model = os.getenv("ANTHROPIC_MODEL", self.ai.anthropic_model)
        
        # Trading Configuration
        self.trading.alpaca_key_id = os.getenv("ALPACA_KEY_ID")
        self.trading.alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")
        self.trading.alpaca_api_base = os.getenv("ALPACA_API_BASE", self.trading.alpaca_api_base)
        self.trading.alpaca_data_url = os.getenv("ALPACA_DATA_URL", self.trading.alpaca_data_url)
        self.trading.polygon_api_key = os.getenv("POLYGON_API_KEY")
        self.trading.broker = os.getenv("EMO_BROKER", self.trading.broker)
        self.trading.order_mode = os.getenv("EMO_ORDER_MODE", self.trading.order_mode)
        self.trading.live_confirm = os.getenv("EMO_LIVE_CONFIRM")
        
        # Risk Configuration
        self.risk.max_position_size_pct = float(os.getenv("MAX_POSITION_SIZE_PCT", self.risk.max_position_size_pct))
        self.risk.max_portfolio_risk_pct = float(os.getenv("MAX_PORTFOLIO_RISK_PCT", self.risk.max_portfolio_risk_pct))
        self.risk.max_single_trade_risk = float(os.getenv("MAX_SINGLE_TRADE_RISK", self.risk.max_single_trade_risk))
        self.risk.risk_validation_enabled = os.getenv("RISK_VALIDATION_ENABLED", "1").lower() in ["1", "true", "yes"]
        self.risk.auto_approval_limit = float(os.getenv("AUTO_APPROVAL_LIMIT", self.risk.auto_approval_limit))
        self.risk.require_manual_approval = os.getenv("REQUIRE_MANUAL_APPROVAL", "1").lower() in ["1", "true", "yes"]
        
        # System Configuration
        env_name = os.getenv("EMO_ENV", "development").lower()
        self.system.environment = Environment(env_name) if env_name in [e.value for e in Environment] else Environment.DEVELOPMENT
        self.system.staging_dir = os.getenv("EMO_STAGING_DIR", self.system.staging_dir)
        self.system.log_level = os.getenv("EMO_LOG_LEVEL", self.system.log_level)
        self.system.dashboard_port = int(os.getenv("DASHBOARD_PORT", self.system.dashboard_port))
        self.system.secret_key = os.getenv("SECRET_KEY")
    
    def _load_config_files(self):
        """Load from configuration files if they exist."""
        if not self.config_dir.exists():
            return
        
        # Load environment-specific config
        env_config_file = self.config_dir / f"{self.system.environment.value}.json"
        if env_config_file.exists():
            try:
                with open(env_config_file, 'r') as f:
                    config_data = json.load(f)
                    self._apply_config_data(config_data)
            except Exception as e:
                logging.warning(f"Could not load {env_config_file}: {e}")
    
    def _apply_config_data(self, config_data: Dict[str, Any]):
        """Apply configuration data from JSON file."""
        for section_name, section_data in config_data.items():
            if hasattr(self, section_name):
                section = getattr(self, section_name)
                for key, value in section_data.items():
                    if hasattr(section, key):
                        setattr(section, key, value)
    
    def validate(self) -> bool:
        """Validate all configuration sections."""
        self.validation_errors = []
        self.validation_warnings = []
        
        # Validate each section
        sections = [
            ("AI", self.ai),
            ("Trading", self.trading),
            ("Risk", self.risk),
            ("System", self.system)
        ]
        
        for section_name, section in sections:
            errors = section.validate()
            for error in errors:
                if error.startswith("WARNING:"):
                    self.validation_warnings.append(f"{section_name}: {error[8:]}")
                else:
                    self.validation_errors.append(f"{section_name}: {error}")
        
        return len(self.validation_errors) == 0
    
    def get_validation_report(self) -> str:
        """Get detailed validation report."""
        report = []
        report.append("CONFIGURATION VALIDATION REPORT")
        report.append("=" * 50)
        
        if not self.validation_errors and not self.validation_warnings:
            report.append("✅ All configuration sections are valid")
        else:
            if self.validation_errors:
                report.append("\n❌ ERRORS:")
                for error in self.validation_errors:
                    report.append(f"  • {error}")
            
            if self.validation_warnings:
                report.append("\n⚠️ WARNINGS:")
                for warning in self.validation_warnings:
                    report.append(f"  • {warning}")
        
        report.append(f"\nEnvironment: {self.system.environment.value}")
        report.append(f"Order Mode: {self.trading.order_mode}")
        report.append(f"Risk Validation: {'Enabled' if self.risk.risk_validation_enabled else 'Disabled'}")
        
        return "\n".join(report)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire configuration to dictionary."""
        return {
            "ai": self.ai.to_dict(),
            "trading": self.trading.to_dict(),
            "risk": self.risk.to_dict(),
            "system": self.system.to_dict(),
            "validation": {
                "errors": self.validation_errors,
                "warnings": self.validation_warnings,
                "valid": len(self.validation_errors) == 0
            }
        }
    
    def save_config_template(self, file_path: Optional[Path] = None) -> Path:
        """Save configuration template to file."""
        if file_path is None:
            file_path = self.config_dir / "config_template.json"
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        template = {
            "ai": {
                "openai_model": "gpt-4o-mini",
                "anthropic_model": "claude-3-haiku-20240307",
                "provider_order": ["openai", "anthropic", "mock"]
            },
            "trading": {
                "broker": "alpaca",
                "order_mode": "stage",
                "paper_trading": True
            },
            "risk": {
                "max_position_size_pct": 0.05,
                "max_portfolio_risk_pct": 0.10,
                "risk_validation_enabled": True
            },
            "system": {
                "environment": "development",
                "log_level": "INFO",
                "dashboard_port": 8083
            }
        }
        
        with open(file_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        return file_path

# Global configuration instance
_global_config: Optional[RobustConfig] = None

def get_config() -> RobustConfig:
    """Get global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = RobustConfig()
        if not _global_config.validate():
            logging.warning("Configuration validation failed")
    return _global_config

def reload_config() -> RobustConfig:
    """Reload configuration from files."""
    global _global_config
    _global_config = RobustConfig()
    return _global_config