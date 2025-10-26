# Enhanced Environment Configuration Loader
# Supports .env file merging and environment-specific overrides

"""
EMO Options Bot - Configuration Management System
Implements environment-based configuration with file merging.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class EnvironmentConfig:
    """Configuration container with validation"""
    
    # Core settings
    emo_env: str = "dev"
    debug: bool = False
    
    # Database
    db_url: str = "sqlite:///./data/emo.sqlite"
    
    # Broker
    alpaca_key_id: str = ""
    alpaca_secret_key: str = ""
    alpaca_api_base: str = "https://paper-api.alpaca.markets"
    alpaca_data_url: str = "https://data.alpaca.markets/v2"
    
    # Trading
    emo_stage_orders: bool = True
    emo_live_data: bool = False
    emo_symbols: List[str] = None
    
    # Services
    emo_health_port: int = 8082
    emo_dashboard_port: int = 8083
    emo_log_level: str = "INFO"
    
    # ML/AI
    emo_ml_enable: bool = True
    openai_api_key: str = ""
    
    # Alerts
    smtp_server: str = ""
    smtp_user: str = ""
    smtp_pass: str = ""
    alert_email: str = ""
    
    def __post_init__(self):
        if self.emo_symbols is None:
            self.emo_symbols = ["SPY", "QQQ", "IWM"]
    
    @classmethod
    def from_env(cls, env_dict: Dict[str, str]) -> "EnvironmentConfig":
        """Create config from environment dictionary"""
        
        def get_bool(key: str, default: bool = False) -> bool:
            value = env_dict.get(key, "").lower()
            return value in ("1", "true", "yes", "on")
        
        def get_int(key: str, default: int = 0) -> int:
            try:
                return int(env_dict.get(key, str(default)))
            except (ValueError, TypeError):
                return default
        
        def get_list(key: str, default: List[str] = None) -> List[str]:
            value = env_dict.get(key, "")
            if not value:
                return default or []
            return [s.strip().upper() for s in value.split(",") if s.strip()]
        
        return cls(
            emo_env=env_dict.get("EMO_ENV", "dev"),
            debug=get_bool("EMO_DEBUG"),
            db_url=env_dict.get("DB_URL", "sqlite:///./data/emo.sqlite"),
            alpaca_key_id=env_dict.get("ALPACA_KEY_ID", ""),
            alpaca_secret_key=env_dict.get("ALPACA_SECRET_KEY", ""),
            alpaca_api_base=env_dict.get("ALPACA_API_BASE", "https://paper-api.alpaca.markets"),
            alpaca_data_url=env_dict.get("ALPACA_DATA_URL", "https://data.alpaca.markets/v2"),
            emo_stage_orders=get_bool("EMO_STAGE_ORDERS", True),
            emo_live_data=get_bool("EMO_LIVE_DATA", False),
            emo_symbols=get_list("EMO_SYMBOLS", ["SPY", "QQQ", "IWM"]),
            emo_health_port=get_int("EMO_HEALTH_PORT", 8082),
            emo_dashboard_port=get_int("EMO_DASHBOARD_PORT", 8083),
            emo_log_level=env_dict.get("EMO_LOG_LEVEL", "INFO"),
            emo_ml_enable=get_bool("EMO_ML_ENABLE", True),
            openai_api_key=env_dict.get("OPENAI_API_KEY", ""),
            smtp_server=env_dict.get("SMTP_SERVER", ""),
            smtp_user=env_dict.get("SMTP_USER", ""),
            smtp_pass=env_dict.get("SMTP_PASS", ""),
            alert_email=env_dict.get("ALERT_EMAIL", ""),
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Environment-specific validation
        if self.emo_env == "prod":
            if not self.alpaca_key_id:
                errors.append("Production requires ALPACA_KEY_ID")
            if not self.alpaca_secret_key:
                errors.append("Production requires ALPACA_SECRET_KEY")
            if "postgresql" not in self.db_url.lower():
                errors.append("Production should use PostgreSQL/TimescaleDB")
        
        # Port conflicts
        if self.emo_health_port == self.emo_dashboard_port:
            errors.append("Health and Dashboard ports cannot be the same")
        
        # Valid log levels
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.emo_log_level.upper() not in valid_log_levels:
            errors.append(f"Invalid log level: {self.emo_log_level}")
        
        return errors

class ConfigLoader:
    """Environment-aware configuration loader with file merging"""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self._loaded_files = []
        self._config = None
    
    def load_environment_files(self, env_name: str = None) -> Dict[str, str]:
        """
        Load environment files with merging priority:
        1. .env (base configuration)
        2. .env.{env_name} (environment-specific overrides)
        3. .env.local (local developer overrides)
        4. Process environment variables (highest priority)
        """
        
        if env_name is None:
            env_name = os.getenv("EMO_ENV", "dev")
        
        # Initialize with process environment
        env_dict = dict(os.environ)
        
        # File loading priority (reverse order, later files override)
        env_files = [
            ".env",
            f".env.{env_name}",
            ".env.local"
        ]
        
        for env_file in env_files:
            file_path = self.project_root / env_file
            if file_path.exists():
                file_env = self._load_env_file(file_path)
                env_dict.update(file_env)
                self._loaded_files.append(str(file_path))
                logger.info(f"Loaded environment from: {env_file}")
        
        # Ensure EMO_ENV is set
        env_dict["EMO_ENV"] = env_name
        
        return env_dict
    
    def _load_env_file(self, file_path: Path) -> Dict[str, str]:
        """Load a single .env file"""
        env_dict = {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        env_dict[key] = value
                    else:
                        logger.warning(f"Invalid line in {file_path}:{line_num}: {line}")
        
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
        
        return env_dict
    
    def get_config(self, env_name: str = None) -> EnvironmentConfig:
        """Get validated configuration for environment"""
        
        if self._config is None or env_name:
            env_dict = self.load_environment_files(env_name)
            self._config = EnvironmentConfig.from_env(env_dict)
        
        return self._config
    
    def validate_config(self, config: EnvironmentConfig = None) -> List[str]:
        """Validate configuration and return errors"""
        if config is None:
            config = self.get_config()
        
        return config.validate()
    
    def get_loaded_files(self) -> List[str]:
        """Get list of loaded configuration files"""
        return self._loaded_files.copy()

# Global config loader instance
_config_loader = None

def get_config_loader() -> ConfigLoader:
    """Get global config loader instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader

def load_config(env_name: str = None) -> EnvironmentConfig:
    """Load configuration for environment"""
    return get_config_loader().get_config(env_name)

def validate_config(env_name: str = None) -> List[str]:
    """Validate configuration and return errors"""
    config = load_config(env_name)
    return config.validate()

# Compatibility functions for existing code
def load_environment() -> Dict[str, str]:
    """Load environment variables (legacy compatibility)"""
    return get_config_loader().load_environment_files()

def get_config_value(key: str, default: Any = None) -> Any:
    """Get a single configuration value (legacy compatibility)"""
    config = load_config()
    return getattr(config, key.lower(), default)

if __name__ == "__main__":
    # CLI for configuration testing
    import sys
    
    if len(sys.argv) > 1:
        env_name = sys.argv[1]
    else:
        env_name = None
    
    # Load and validate configuration
    config = load_config(env_name)
    errors = validate_config(env_name)
    
    print(f"=== EMO Configuration ({config.emo_env}) ===")
    print(f"Database: {config.db_url}")
    print(f"Broker: {config.alpaca_api_base}")
    print(f"Stage Orders: {config.emo_stage_orders}")
    print(f"Live Data: {config.emo_live_data}")
    print(f"Symbols: {', '.join(config.emo_symbols)}")
    print(f"Health Port: {config.emo_health_port}")
    print(f"Dashboard Port: {config.emo_dashboard_port}")
    print(f"ML Enabled: {config.emo_ml_enable}")
    
    loader = get_config_loader()
    loaded_files = loader.get_loaded_files()
    if loaded_files:
        print(f"\nLoaded from: {', '.join(loaded_files)}")
    
    if errors:
        print(f"\n❌ Configuration Errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print(f"\n✅ Configuration valid")
        sys.exit(0)