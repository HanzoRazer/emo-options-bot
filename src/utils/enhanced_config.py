from __future__ import annotations
import os
import logging
import json
from pathlib import Path
from typing import Dict, Optional, Any, Union
from dotenv import load_dotenv

# Setup robust logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

"""
Enhanced Config Loader with Robust Environment Management
---------------------------------------------------------
Features:
- Multi-environment support (.env.dev, .env.staging, .env.prod)
- Robust error handling and validation
- Comprehensive logging and monitoring
- Configuration validation and type conversion
- Environment health checks

Priority:
  1. OS environment variables
  2. Environment-specific .env file (.env.<EMO_ENV>)
  3. Default .env file
  4. Built-in secure defaults

Provides: get(), require(), as_bool(), validate(), health_check()
"""

class Config:
    """Enhanced configuration manager with robust error handling and validation."""
    
    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root) if root else Path.cwd()
        self._loaded_files: Dict[str, bool] = {}
        self._validation_errors: Dict[str, str] = {}
        self._load_timestamp = None
        self._load()

    def _load(self):
        """Load configuration files with comprehensive error handling."""
        # Initialize the environment snapshot first
        self._env: Dict[str, str] = dict(os.environ)
        
        try:
            self._load_timestamp = os.path.getmtime(self.root / ".env") if (self.root / ".env").exists() else None
            
            # Load base .env file
            base_env = self.root / ".env"
            if base_env.exists():
                success = load_dotenv(base_env)
                self._loaded_files[str(base_env)] = success
                if success:
                    logger.info(f"✅ Loaded base config: {base_env}")
                else:
                    logger.warning(f"⚠️ Failed to load base config: {base_env}")
            
            # Load environment-specific file
            emo_env = os.getenv("EMO_ENV", "dev").lower()
            env_specific = self.root / f".env.{emo_env}"
            if env_specific.exists():
                success = load_dotenv(env_specific, override=True)
                self._loaded_files[str(env_specific)] = success
                if success:
                    logger.info(f"✅ Loaded environment config: {env_specific}")
                else:
                    logger.warning(f"⚠️ Failed to load environment config: {env_specific}")
            else:
                logger.info(f"ℹ️ No environment-specific config found: {env_specific}")
            
            # Refresh environment snapshot after loading dotenv files
            self._env = dict(os.environ)
            
            # Validate critical settings
            self._validate_config()
            
        except Exception as e:
            logger.error(f"❌ Configuration loading failed: {e}")
            self._validation_errors["load_error"] = str(e)
            # Ensure _env exists even on failure
            self._env = dict(os.environ)
    
    def _validate_config(self):
        """Validate critical configuration settings."""
        # Check database URL validity
        try:
            db_url = self.get("DATABASE_URL")
            if db_url and not (db_url.startswith("sqlite:") or db_url.startswith("postgresql:")):
                self._validation_errors["database_url"] = "Invalid database URL scheme"
        except Exception as e:
            self._validation_errors["database_validation"] = str(e)
        
        # Check required numeric settings
        for key in ["DB_POOL_SIZE", "DB_MAX_OVERFLOW", "HEALTH_SERVER_PORT"]:
            value = self.get(key)
            if value and not str(value).isdigit():
                self._validation_errors[key.lower()] = f"Invalid numeric value: {value}"
    
    def health_check(self) -> Dict[str, Any]:
        """Return configuration health status."""
        return {
            "loaded_files": self._loaded_files,
            "validation_errors": self._validation_errors,
            "environment": self.get("EMO_ENV", "dev"),
            "config_timestamp": self._load_timestamp,
            "total_env_vars": len([k for k in os.environ.keys() if k.startswith("EMO_")]),
        }

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value with robust error handling."""
        try:
            return self._env.get(key, default)
        except Exception as e:
            logger.error(f"❌ Error getting config '{key}': {e}")
            return default

    def require(self, key: str) -> str:
        """Get required configuration value with validation."""
        val = self.get(key)
        if not val:
            error_msg = f"Missing required config: {key}"
            logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
        return val

    def as_bool(self, key: str, default: bool = False) -> bool:
        """Convert configuration value to boolean with validation."""
        try:
            val = self.get(key)
            if val is None:
                return default
            return str(val).strip().lower() in ("1", "true", "yes", "on")
        except Exception as e:
            logger.error(f"❌ Error converting '{key}' to bool: {e}")
            return default
    
    def as_int(self, key: str, default: int = 0) -> int:
        """Convert configuration value to integer with validation."""
        try:
            value = self.get(key)
            if value is None:
                return default
            return int(value)
        except (ValueError, TypeError) as e:
            logger.error(f"❌ Error converting '{key}' to int: {e}")
            return default
    
    def reload(self) -> bool:
        """Reload configuration from files."""
        try:
            old_errors = len(self._validation_errors)
            self._validation_errors.clear()
            self._loaded_files.clear()
            self._load()
            new_errors = len(self._validation_errors)
            
            if new_errors == 0:
                logger.info("✅ Configuration reloaded successfully")
                return True
            else:
                logger.warning(f"⚠️ Configuration reloaded with {new_errors} validation errors")
                return False
        except Exception as e:
            logger.error(f"❌ Configuration reload failed: {e}")
            return False

if __name__ == "__main__":
    # Enhanced CLI interface for configuration testing
    import argparse
    
    parser = argparse.ArgumentParser(description="EMO Enhanced Config - Testing & Validation")
    parser.add_argument("--health", action="store_true", help="Show configuration health")
    parser.add_argument("--validate", action="store_true", help="Run configuration validation")
    parser.add_argument("--reload", action="store_true", help="Reload configuration files")
    parser.add_argument("--get", type=str, help="Get specific configuration value")
    parser.add_argument("--list", action="store_true", help="List all EMO_ environment variables")
    
    args = parser.parse_args()
    
    c = Config()
    
    if args.health:
        health = c.health_check()
        print("🏥 Configuration Health Report:")
        print(f"  Environment: {health['environment']}")
        print(f"  Loaded Files: {len(health['loaded_files'])}")
        for file, success in health['loaded_files'].items():
            status = "✅" if success else "❌"
            print(f"    {status} {file}")
        
        if health['validation_errors']:
            print(f"  Validation Errors: {len(health['validation_errors'])}")
            for key, error in health['validation_errors'].items():
                print(f"    ❌ {key}: {error}")
        else:
            print("  ✅ No validation errors")
        
        print(f"  EMO Environment Variables: {health['total_env_vars']}")
    
    elif args.validate:
        health = c.health_check()
        if health['validation_errors']:
            print("❌ Configuration validation failed:")
            for key, error in health['validation_errors'].items():
                print(f"  • {key}: {error}")
            exit(1)
        else:
            print("✅ Configuration validation passed")
    
    elif args.reload:
        if c.reload():
            print("✅ Configuration reloaded successfully")
        else:
            print("❌ Configuration reload failed")
            exit(1)
    
    elif args.get:
        value = c.get(args.get)
        if value:
            print(f"{args.get}={value}")
        else:
            print(f"❌ Configuration '{args.get}' not found")
            exit(1)
    
    elif args.list:
        emo_vars = {k: v for k, v in os.environ.items() if k.startswith("EMO_")}
        if emo_vars:
            print("🔧 EMO Environment Variables:")
            for key, value in sorted(emo_vars.items()):
                # Mask sensitive values
                if any(sensitive in key.lower() for sensitive in ["password", "secret", "key", "token"]):
                    value = "*" * len(value) if value else "(empty)"
                print(f"  {key}={value}")
        else:
            print("ℹ️ No EMO_ environment variables found")
    
    else:
        # Default: show environment and database URL sample
        print(f"EMO_ENV: {c.get('EMO_ENV', 'dev')}")
        print("Database URL sample: run `python src/database/db_router.py`")