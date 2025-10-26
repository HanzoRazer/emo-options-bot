#!/usr/bin/env python3
"""
Environment Validation Tool
===========================
Fail-fast environment validation for production deployments with:
- Comprehensive environment variable checking
- Production readiness validation
- Configuration health verification
- Integration with enhanced configuration system

Features:
- Multi-environment validation (dev/staging/prod)
- Required vs optional variable checking
- Configuration format validation
- Database connectivity verification
- Broker API credentials validation
- Email notification setup verification

Usage:
  python tools/validate_env.py --mode prod
  python tools/validate_env.py --mode staging --check-database
  python tools/validate_env.py --check-all --verbose
"""

import os
import sys
import argparse
import logging
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path for enhanced config integration
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

# Enhanced configuration integration
try:
    from utils.enhanced_config import Config
    config = Config()
    logger.info("✅ Enhanced configuration loaded")
except Exception as e:
    logger.warning(f"⚠️ Enhanced config not available: {e}")
    class FallbackConfig:
        def get(self, key: str, default: str = None) -> str:
            return os.getenv(key, default)
        def as_bool(self, key: str, default: bool = False) -> bool:
            return os.getenv(key, "0").lower() in ("1", "true", "yes", "on")
        def as_int(self, key: str, default: int = 0) -> int:
            try:
                return int(self.get(key, str(default)))
            except (ValueError, TypeError):
                return default
    config = FallbackConfig()

# Environment variable requirements by mode
ENV_REQUIREMENTS = {
    "prod": {
        "critical": [
            "ALPACA_KEY_ID",
            "ALPACA_SECRET_KEY", 
            "ALPACA_API_BASE",
            "EMO_ENV"
        ],
        "recommended": [
            "EMO_EMAIL_NOTIFICATIONS",
            "SMTP_SERVER",
            "SMTP_USER", 
            "SMTP_PASS",
            "NOTIFY_EMAIL",
            "EMO_PG_DSN",
            "EMO_TIMESCALE_URL"
        ],
        "optional": [
            "EMO_STAGE_ORDERS",
            "EMO_AUTO_BACKUP",
            "EMO_PERFORMANCE_MONITORING",
            "HEALTH_SERVER_PORT",
            "EMO_SLEEP_INTERVAL",
            "EMO_MAX_CYCLES"
        ]
    },
    "staging": {
        "critical": [
            "EMO_ENV",
            "ALPACA_KEY_ID",
            "ALPACA_SECRET_KEY"
        ],
        "recommended": [
            "ALPACA_API_BASE",
            "EMO_STAGE_ORDERS",
            "EMO_EMAIL_NOTIFICATIONS"
        ],
        "optional": [
            "SMTP_SERVER",
            "EMO_PG_DSN",
            "HEALTH_SERVER_PORT"
        ]
    },
    "dev": {
        "critical": [
            "EMO_ENV"
        ],
        "recommended": [
            "EMO_STAGE_ORDERS"
        ],
        "optional": [
            "ALPACA_KEY_ID",
            "ALPACA_SECRET_KEY",
            "EMO_SQLITE_PATH",
            "HEALTH_SERVER_PORT"
        ]
    }
}

class EnvironmentValidator:
    """Comprehensive environment validation system."""
    
    def __init__(self, mode: str = "dev"):
        self.mode = mode.lower()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        
        if self.mode not in ENV_REQUIREMENTS:
            raise ValueError(f"Invalid mode: {mode}. Valid modes: {list(ENV_REQUIREMENTS.keys())}")
    
    def validate_environment_variables(self) -> bool:
        """Validate environment variables for the specified mode."""
        requirements = ENV_REQUIREMENTS[self.mode]
        all_valid = True
        
        # Check critical variables
        for var in requirements["critical"]:
            value = config.get(var)
            if not value:
                self.errors.append(f"Critical environment variable missing: {var}")
                all_valid = False
            else:
                self.info.append(f"✅ Critical variable set: {var}")
        
        # Check recommended variables
        for var in requirements["recommended"]:
            value = config.get(var)
            if not value:
                self.warnings.append(f"Recommended environment variable missing: {var}")
            else:
                self.info.append(f"✅ Recommended variable set: {var}")
        
        # Check optional variables
        for var in requirements["optional"]:
            value = config.get(var)
            if value:
                self.info.append(f"ℹ️ Optional variable set: {var}")
        
        return all_valid
    
    def validate_configuration_format(self) -> bool:
        """Validate configuration value formats."""
        all_valid = True
        
        # Validate URLs
        url_vars = ["ALPACA_API_BASE", "EMO_PG_DSN", "EMO_TIMESCALE_URL", "SMTP_SERVER"]
        for var in url_vars:
            value = config.get(var)
            if value and not self._is_valid_url_format(value):
                self.errors.append(f"Invalid URL format for {var}: {value}")
                all_valid = False
        
        # Validate email addresses
        email_vars = ["SMTP_USER", "NOTIFY_EMAIL"]
        for var in email_vars:
            value = config.get(var)
            if value and not self._is_valid_email_format(value):
                self.errors.append(f"Invalid email format for {var}: {value}")
                all_valid = False
        
        # Validate numeric values
        numeric_vars = ["HEALTH_SERVER_PORT", "EMO_SLEEP_INTERVAL", "EMO_MAX_CYCLES", "SMTP_PORT"]
        for var in numeric_vars:
            value = config.get(var)
            if value and not value.isdigit():
                self.errors.append(f"Invalid numeric value for {var}: {value}")
                all_valid = False
        
        # Validate boolean values
        bool_vars = ["EMO_STAGE_ORDERS", "EMO_EMAIL_NOTIFICATIONS", "EMO_AUTO_BACKUP", "EMO_PERFORMANCE_MONITORING"]
        for var in bool_vars:
            value = config.get(var)
            if value and value.lower() not in ["0", "1", "true", "false", "yes", "no", "on", "off"]:
                self.warnings.append(f"Unclear boolean value for {var}: {value} (should be 0/1, true/false)")
        
        return all_valid
    
    def validate_file_permissions(self) -> bool:
        """Validate file and directory permissions."""
        all_valid = True
        
        # Check data directories
        data_dirs = [
            ROOT / "data",
            ROOT / "ops", 
            ROOT / "logs",
            ROOT / "backups"
        ]
        
        for dir_path in data_dirs:
            if not dir_path.exists():
                try:
                    dir_path.mkdir(parents=True, exist_ok=True)
                    self.info.append(f"✅ Created directory: {dir_path}")
                except Exception as e:
                    self.errors.append(f"Cannot create directory {dir_path}: {e}")
                    all_valid = False
            else:
                if not os.access(dir_path, os.W_OK):
                    self.errors.append(f"No write permission for directory: {dir_path}")
                    all_valid = False
                else:
                    self.info.append(f"✅ Directory writable: {dir_path}")
        
        # Check SQLite database path
        sqlite_path = config.get("EMO_SQLITE_PATH", "ops/emo.sqlite")
        if not Path(sqlite_path).is_absolute():
            sqlite_path = ROOT / sqlite_path
        
        sqlite_dir = Path(sqlite_path).parent
        if not sqlite_dir.exists():
            try:
                sqlite_dir.mkdir(parents=True, exist_ok=True)
                self.info.append(f"✅ Created SQLite directory: {sqlite_dir}")
            except Exception as e:
                self.errors.append(f"Cannot create SQLite directory {sqlite_dir}: {e}")
                all_valid = False
        
        return all_valid
    
    def validate_database_connectivity(self) -> bool:
        """Validate database connectivity."""
        try:
            # Try to import and test database router
            sys.path.insert(0, str(ROOT))
            from db.router import test_connection
            
            if test_connection():
                self.info.append("✅ Database connection test successful")
                return True
            else:
                self.errors.append("❌ Database connection test failed")
                return False
                
        except Exception as e:
            self.errors.append(f"Database connectivity check failed: {e}")
            return False
    
    def validate_broker_credentials(self) -> bool:
        """Validate broker API credentials."""
        if self.mode == "dev":
            # Skip broker validation in dev mode
            self.info.append("ℹ️ Broker credential validation skipped in dev mode")
            return True
        
        try:
            key_id = config.get("ALPACA_KEY_ID")
            secret_key = config.get("ALPACA_SECRET_KEY")
            api_base = config.get("ALPACA_API_BASE", "https://paper-api.alpaca.markets")
            
            if not all([key_id, secret_key]):
                self.errors.append("Alpaca credentials incomplete")
                return False
            
            # Basic format validation
            if len(key_id) < 10 or len(secret_key) < 20:
                self.warnings.append("Alpaca credentials appear to be in incorrect format")
            
            # Try to import and test broker connection (if available)
            try:
                from exec.alpaca_broker import AlpacaBroker
                broker = AlpacaBroker(paper=True)
                # Attempt a simple API call
                account = broker.get_account()
                if account:
                    self.info.append("✅ Broker API connection successful")
                    return True
                else:
                    self.errors.append("Broker API returned no account data")
                    return False
            except ImportError:
                self.info.append("ℹ️ Broker module not available for testing")
                return True
            except Exception as e:
                self.errors.append(f"Broker API test failed: {e}")
                return False
                
        except Exception as e:
            self.errors.append(f"Broker credential validation error: {e}")
            return False
    
    def validate_email_configuration(self) -> bool:
        """Validate email notification configuration."""
        if not config.as_bool("EMO_EMAIL_NOTIFICATIONS"):
            self.info.append("ℹ️ Email notifications disabled, skipping validation")
            return True
        
        try:
            required_email_vars = ["SMTP_SERVER", "SMTP_USER", "SMTP_PASS"]
            missing_vars = [var for var in required_email_vars if not config.get(var)]
            
            if missing_vars:
                self.errors.append(f"Email notifications enabled but missing: {', '.join(missing_vars)}")
                return False
            
            # Test SMTP connection (optional, can be slow)
            self.info.append("✅ Email configuration variables present")
            self.info.append("ℹ️ SMTP connection test skipped (use --check-email to test)")
            return True
            
        except Exception as e:
            self.errors.append(f"Email configuration validation error: {e}")
            return False
    
    def validate_health_monitoring(self) -> bool:
        """Validate health monitoring configuration."""
        try:
            # Check if health monitoring is available
            try:
                from tools.emit_health import serve_health_monitor
                self.info.append("✅ Health monitoring module available")
            except ImportError:
                self.warnings.append("Health monitoring module not available")
                return True
            
            # Check port configuration
            port = config.as_int("HEALTH_SERVER_PORT", 8082)
            if port < 1024 and os.name != 'nt':
                self.warnings.append(f"Health server port {port} requires root privileges on Unix systems")
            elif port > 65535:
                self.errors.append(f"Invalid health server port: {port}")
                return False
            else:
                self.info.append(f"✅ Health server port configured: {port}")
            
            return True
            
        except Exception as e:
            self.errors.append(f"Health monitoring validation error: {e}")
            return False
    
    def _is_valid_url_format(self, url: str) -> bool:
        """Basic URL format validation."""
        return url.startswith(("http://", "https://", "postgresql://", "sqlite://"))
    
    def _is_valid_email_format(self, email: str) -> bool:
        """Basic email format validation."""
        return "@" in email and "." in email.split("@")[1]
    
    def run_all_validations(self, check_database: bool = False, check_broker: bool = False) -> bool:
        """Run all validation checks."""
        all_passed = True
        
        logger.info(f"🔍 Running environment validation for mode: {self.mode}")
        
        # Core validations
        if not self.validate_environment_variables():
            all_passed = False
        
        if not self.validate_configuration_format():
            all_passed = False
        
        if not self.validate_file_permissions():
            all_passed = False
        
        if not self.validate_email_configuration():
            all_passed = False
        
        if not self.validate_health_monitoring():
            all_passed = False
        
        # Optional validations
        if check_database:
            if not self.validate_database_connectivity():
                all_passed = False
        
        if check_broker and self.mode != "dev":
            if not self.validate_broker_credentials():
                all_passed = False
        
        return all_passed
    
    def print_results(self):
        """Print validation results."""
        print(f"\n🔍 Environment Validation Results ({self.mode.upper()} mode)")
        print("=" * 60)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        if self.warnings:
            print(f"\n⚠️ WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  • {warning}")
        
        if self.info:
            print(f"\n✅ INFO ({len(self.info)}):")
            for info in self.info:
                print(f"  • {info}")
        
        # Summary
        if self.errors:
            print(f"\n❌ VALIDATION FAILED: {len(self.errors)} errors found")
            if self.mode == "prod":
                print("🚨 Production deployment NOT recommended")
        elif self.warnings:
            print(f"\n⚠️ VALIDATION PASSED WITH WARNINGS: {len(self.warnings)} warnings")
            if self.mode == "prod":
                print("🟡 Production deployment possible but review warnings")
        else:
            print("\n✅ VALIDATION PASSED: All checks successful")
            if self.mode == "prod":
                print("🟢 Production deployment ready")

def main():
    """Main CLI interface for environment validation."""
    parser = argparse.ArgumentParser(
        description="EMO Environment Validation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate production environment
  python tools/validate_env.py --mode prod
  
  # Full validation with database and broker checks
  python tools/validate_env.py --mode prod --check-all
  
  # Staging environment validation
  python tools/validate_env.py --mode staging --check-database
  
  # Development environment (minimal checks)
  python tools/validate_env.py --mode dev --verbose
        """
    )
    
    parser.add_argument(
        "--mode", "-m", 
        choices=["dev", "staging", "prod"],
        default="dev",
        help="Environment mode to validate (default: dev)"
    )
    parser.add_argument(
        "--check-database", 
        action="store_true", 
        help="Test database connectivity"
    )
    parser.add_argument(
        "--check-broker", 
        action="store_true", 
        help="Test broker API credentials"
    )
    parser.add_argument(
        "--check-all", 
        action="store_true", 
        help="Run all optional checks (database, broker, etc.)"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--exit-on-error", 
        action="store_true", 
        help="Exit with error code if validation fails"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Configure check options
    check_database = args.check_database or args.check_all
    check_broker = args.check_broker or args.check_all
    
    try:
        # Run validation
        validator = EnvironmentValidator(args.mode)
        validation_passed = validator.run_all_validations(
            check_database=check_database,
            check_broker=check_broker
        )
        
        # Print results
        validator.print_results()
        
        # Exit with appropriate code
        if args.exit_on_error and not validation_passed:
            return 2
        elif validator.errors:
            return 1
        else:
            return 0
            
    except Exception as e:
        logger.error(f"❌ Validation tool failed: {e}")
        return 3

if __name__ == "__main__":
    exit(main())