#!/usr/bin/env python3
"""
EMO Options Bot - Workspace Configuration Manager
=================================================
Comprehensive workspace setup and configuration management for:
- Enhanced Phase 2 infrastructure integration
- Multi-environment configuration (dev/staging/prod)
- Component health monitoring and validation
- Automated workspace initialization
- Development and production readiness checks

Features:
- Automated directory structure creation
- Environment-specific configuration templates
- Component integration validation
- Development tools setup
- Production deployment preparation
- Health monitoring dashboard setup

Usage:
  python workspace_config.py --init                    # Initialize workspace
  python workspace_config.py --validate               # Validate configuration
  python workspace_config.py --health                 # Show component health
  python workspace_config.py --setup-dev              # Setup development environment
  python workspace_config.py --setup-prod             # Setup production environment
"""

import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import sys
import shutil
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Workspace paths
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

class WorkspaceManager:
    """Comprehensive workspace configuration and management system."""
    
    def __init__(self):
        self.root = ROOT
        self.config = config
        self.required_directories = [
            "data",
            "ops",
            "ops/orders",
            "ops/orders/drafts", 
            "ops/orders/archive",
            "logs",
            "backups",
            "src",
            "src/database",
            "src/utils",
            "tools",
            "tests",
            "scripts"
        ]
        
        self.components = {
            "enhanced_config": "src/utils/enhanced_config.py",
            "database_router": "src/database/db_router.py",
            "health_monitor": "tools/emit_health.py",
            "order_staging": "tools/stage_order_cli.py",
            "live_logger": "data/live_logger.py",
            "runner": "tools/runner.py",
            "order_rotation": "tools/rotate_staged_orders.py",
            "env_validator": "tools/validate_env.py"
        }
        
        self.environment_templates = {
            "dev": {
                "EMO_ENV": "dev",
                "EMO_STAGE_ORDERS": "1",
                "EMO_EMAIL_NOTIFICATIONS": "0",
                "EMO_AUTO_BACKUP": "1",
                "EMO_PERFORMANCE_MONITORING": "1",
                "EMO_HEALTH_INTEGRATION": "1",
                "EMO_SQLITE_PATH": "./ops/emo.sqlite",
                "HEALTH_SERVER_PORT": "8082",
                "EMO_SLEEP_INTERVAL": "60",
                "EMO_SYMBOLS": "SPY,QQQ,AAPL",
                "EMO_LIVE_LOGGER_ENABLED": "1"
            },
            "staging": {
                "EMO_ENV": "staging",
                "EMO_STAGE_ORDERS": "1",
                "EMO_EMAIL_NOTIFICATIONS": "1",
                "EMO_AUTO_BACKUP": "1",
                "EMO_PERFORMANCE_MONITORING": "1",
                "EMO_HEALTH_INTEGRATION": "1",
                "EMO_SQLITE_PATH": "./ops/emo_staging.sqlite",
                "HEALTH_SERVER_PORT": "8082",
                "EMO_SLEEP_INTERVAL": "300",
                "EMO_SYMBOLS": "SPY,QQQ,AAPL,MSFT,TSLA",
                "EMO_LIVE_LOGGER_ENABLED": "1",
                "ALPACA_API_BASE": "https://paper-api.alpaca.markets"
            },
            "prod": {
                "EMO_ENV": "prod",
                "EMO_STAGE_ORDERS": "0",
                "EMO_EMAIL_NOTIFICATIONS": "1",
                "EMO_AUTO_BACKUP": "1",
                "EMO_PERFORMANCE_MONITORING": "1",
                "EMO_HEALTH_INTEGRATION": "1",
                "HEALTH_SERVER_PORT": "8082",
                "EMO_SLEEP_INTERVAL": "300",
                "EMO_SYMBOLS": "SPY,QQQ,AAPL,MSFT,TSLA,NVDA,AMZN,GOOGL",
                "EMO_LIVE_LOGGER_ENABLED": "1",
                "ALPACA_API_BASE": "https://api.alpaca.markets"
            }
        }
    
    def create_directory_structure(self) -> bool:
        """Create required directory structure."""
        try:
            logger.info("📁 Creating workspace directory structure...")
            
            created_dirs = []
            for dir_path in self.required_directories:
                full_path = self.root / dir_path
                if not full_path.exists():
                    full_path.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(str(dir_path))
                    logger.info(f"  ✅ Created: {dir_path}")
                else:
                    logger.debug(f"  ℹ️ Exists: {dir_path}")
            
            if created_dirs:
                logger.info(f"✅ Created {len(created_dirs)} directories")
            else:
                logger.info("ℹ️ All directories already exist")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create directory structure: {e}")
            return False
    
    def validate_components(self) -> Dict[str, bool]:
        """Validate that all components exist and are functional."""
        logger.info("🔍 Validating workspace components...")
        
        results = {}
        
        for component_name, file_path in self.components.items():
            full_path = self.root / file_path
            exists = full_path.exists()
            results[component_name] = exists
            
            status = "✅" if exists else "❌"
            logger.info(f"  {status} {component_name}: {file_path}")
        
        return results
    
    def create_environment_file(self, environment: str, overwrite: bool = False) -> bool:
        """Create environment-specific .env file."""
        try:
            if environment not in self.environment_templates:
                logger.error(f"❌ Unknown environment: {environment}")
                return False
            
            env_file = self.root / f".env.{environment}"
            
            if env_file.exists() and not overwrite:
                logger.info(f"ℹ️ Environment file already exists: {env_file}")
                return True
            
            template = self.environment_templates[environment]
            
            # Create environment file content
            content = [
                f"# EMO Options Bot - {environment.upper()} Environment Configuration",
                f"# Generated: {datetime.now().isoformat()}",
                f"# Environment: {environment}",
                "",
                "# Core Configuration",
            ]
            
            for key, value in template.items():
                content.append(f"{key}={value}")
            
            content.extend([
                "",
                "# API Credentials (configure these manually)",
                "# ALPACA_KEY_ID=your_key_id",
                "# ALPACA_SECRET_KEY=your_secret_key",
                "",
                "# Email Configuration (optional)",
                "# SMTP_SERVER=smtp.gmail.com",
                "# SMTP_PORT=587", 
                "# SMTP_USER=your_email@example.com",
                "# SMTP_PASS=your_app_password",
                "# NOTIFY_EMAIL=notifications@example.com",
                "",
                "# Database Configuration (optional for prod)",
                "# EMO_PG_DSN=postgresql://user:pass@host:5432/emo",
                "# EMO_TIMESCALE_URL=postgresql://user:pass@timescale:5432/emo",
                ""
            ])
            
            with open(env_file, 'w') as f:
                f.write('\n'.join(content))
            
            logger.info(f"✅ Created environment file: {env_file}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create environment file: {e}")
            return False
    
    def setup_development_environment(self) -> bool:
        """Setup complete development environment."""
        logger.info("🚀 Setting up development environment...")
        
        success = True
        
        # Create directories
        if not self.create_directory_structure():
            success = False
        
        # Create dev environment file
        if not self.create_environment_file("dev"):
            success = False
        
        # Initialize database
        try:
            from db.router import migrate
            if migrate():
                logger.info("✅ Database migration completed")
            else:
                logger.warning("⚠️ Database migration failed")
                success = False
        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            success = False
        
        # Create sample configuration
        self.create_sample_configs()
        
        return success
    
    def setup_production_environment(self) -> bool:
        """Setup production environment with validation."""
        logger.info("🚀 Setting up production environment...")
        
        success = True
        
        # Create directories
        if not self.create_directory_structure():
            success = False
        
        # Create prod environment file
        if not self.create_environment_file("prod"):
            success = False
        
        # Validate production requirements
        try:
            from tools.validate_env import EnvironmentValidator
            validator = EnvironmentValidator("prod")
            if not validator.run_all_validations(check_database=True, check_broker=True):
                logger.warning("⚠️ Production validation has issues")
                validator.print_results()
                success = False
        except Exception as e:
            logger.error(f"❌ Production validation failed: {e}")
            success = False
        
        return success
    
    def create_sample_configs(self):
        """Create sample configuration files."""
        logger.info("📝 Creating sample configuration files...")
        
        # Sample config.json for dynamic configuration
        config_file = self.root / "config.json"
        if not config_file.exists():
            sample_config = {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "trading": {
                    "enabled": False,
                    "paper_trading": True,
                    "risk_limits": {
                        "max_position_size": 1000,
                        "max_daily_trades": 10
                    }
                },
                "analysis": {
                    "symbols": ["SPY", "QQQ", "AAPL"],
                    "indicators": ["sma", "rsi", "macd"],
                    "timeframes": ["1m", "5m", "1h", "1d"]
                },
                "notifications": {
                    "email_enabled": False,
                    "alert_thresholds": {
                        "profit_target": 0.02,
                        "stop_loss": -0.01
                    }
                }
            }
            
            with open(config_file, 'w') as f:
                json.dump(sample_config, f, indent=2)
            
            logger.info(f"✅ Created sample config: {config_file}")
    
    def get_component_health(self) -> Dict[str, Any]:
        """Get health status of all components."""
        health = {
            "workspace": {
                "status": "healthy",
                "root_directory": str(self.root),
                "directories_exist": True,
                "components_available": True
            },
            "components": {}
        }
        
        # Check directories
        missing_dirs = []
        for dir_path in self.required_directories:
            if not (self.root / dir_path).exists():
                missing_dirs.append(dir_path)
        
        if missing_dirs:
            health["workspace"]["directories_exist"] = False
            health["workspace"]["missing_directories"] = missing_dirs
            health["workspace"]["status"] = "warning"
        
        # Check components
        component_results = self.validate_components()
        missing_components = [name for name, exists in component_results.items() if not exists]
        
        if missing_components:
            health["workspace"]["components_available"] = False
            health["workspace"]["missing_components"] = missing_components
            health["workspace"]["status"] = "error"
        
        health["components"] = component_results
        
        # Check individual component health if available
        try:
            # Enhanced config health
            if hasattr(self.config, 'health_check'):
                health["enhanced_config"] = self.config.health_check()
        except Exception as e:
            health["enhanced_config"] = {"error": str(e)}
        
        try:
            # Database health
            from db.router import test_connection
            health["database"] = {
                "connection_healthy": test_connection(),
                "type": "sqlite" if not config.get("EMO_PG_DSN") else "postgresql"
            }
        except Exception as e:
            health["database"] = {"error": str(e)}
        
        try:
            # Live logger health
            from data.live_logger import health_check
            health["live_logger"] = health_check()
        except Exception as e:
            health["live_logger"] = {"error": str(e)}
        
        return health
    
    def print_workspace_summary(self):
        """Print comprehensive workspace summary."""
        print(f"\n🏗️ EMO Options Bot Workspace Summary")
        print("=" * 60)
        print(f"Root Directory: {self.root}")
        print(f"Environment: {self.config.get('EMO_ENV', 'not-set')}")
        
        # Component status
        components = self.validate_components()
        print(f"\n📦 Components ({len([c for c in components.values() if c])}/{len(components)} available):")
        for name, available in components.items():
            status = "✅" if available else "❌"
            print(f"  {status} {name}")
        
        # Health status
        health = self.get_component_health()
        print(f"\n🏥 Workspace Health: {health['workspace']['status'].upper()}")
        
        if not health['workspace']['directories_exist']:
            print(f"  Missing directories: {', '.join(health['workspace'].get('missing_directories', []))}")
        
        if not health['workspace']['components_available']:
            print(f"  Missing components: {', '.join(health['workspace'].get('missing_components', []))}")

def main():
    """CLI interface for workspace management."""
    parser = argparse.ArgumentParser(
        description="EMO Options Bot Workspace Configuration Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Initialize new workspace
  python workspace_config.py --init
  
  # Setup development environment
  python workspace_config.py --setup-dev
  
  # Setup production environment
  python workspace_config.py --setup-prod
  
  # Validate workspace
  python workspace_config.py --validate
  
  # Show health status
  python workspace_config.py --health
        """
    )
    
    parser.add_argument("--init", action="store_true", help="Initialize workspace structure")
    parser.add_argument("--setup-dev", action="store_true", help="Setup development environment")
    parser.add_argument("--setup-prod", action="store_true", help="Setup production environment")
    parser.add_argument("--validate", action="store_true", help="Validate workspace configuration")
    parser.add_argument("--health", action="store_true", help="Show component health status")
    parser.add_argument("--create-env", choices=["dev", "staging", "prod"], help="Create environment file")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not any([args.init, args.setup_dev, args.setup_prod, args.validate, args.health, args.create_env]):
        # Default: show workspace summary
        manager = WorkspaceManager()
        manager.print_workspace_summary()
        return 0
    
    try:
        manager = WorkspaceManager()
        
        if args.init:
            logger.info("🚀 Initializing workspace...")
            success = manager.create_directory_structure()
            if success:
                logger.info("✅ Workspace initialization completed")
                return 0
            else:
                logger.error("❌ Workspace initialization failed")
                return 1
        
        if args.setup_dev:
            success = manager.setup_development_environment()
            if success:
                logger.info("✅ Development environment setup completed")
                return 0
            else:
                logger.error("❌ Development environment setup failed")
                return 1
        
        if args.setup_prod:
            success = manager.setup_production_environment()
            if success:
                logger.info("✅ Production environment setup completed")
                return 0
            else:
                logger.error("❌ Production environment setup failed")
                return 1
        
        if args.validate:
            logger.info("🔍 Validating workspace...")
            components = manager.validate_components()
            all_valid = all(components.values())
            
            if all_valid:
                logger.info("✅ Workspace validation passed")
                return 0
            else:
                logger.error("❌ Workspace validation failed")
                return 1
        
        if args.health:
            health = manager.get_component_health()
            print("🏥 Workspace Health Report:")
            print(json.dumps(health, indent=2))
            
            if health["workspace"]["status"] == "healthy":
                return 0
            elif health["workspace"]["status"] == "warning":
                return 1
            else:
                return 2
        
        if args.create_env:
            success = manager.create_environment_file(args.create_env, args.overwrite)
            if success:
                logger.info(f"✅ Environment file created: .env.{args.create_env}")
                return 0
            else:
                logger.error(f"❌ Failed to create environment file: .env.{args.create_env}")
                return 1
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Workspace management failed: {e}")
        return 3

if __name__ == "__main__":
    exit(main())