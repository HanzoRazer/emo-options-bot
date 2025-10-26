#!/usr/bin/env python3
"""
EMO Options Bot Setup and Installation Script
============================================
Comprehensive setup script for the EMO Options Bot with OPS database integration
and institutional-grade trading infrastructure.

Features:
- Automatic dependency installation and validation
- Database initialization and migration
- Configuration validation and setup
- Development and production environment setup
- Health check and system validation
- Package structure verification
"""

import os
import sys
import subprocess
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EMOSetup:
    """Comprehensive setup manager for EMO Options Bot."""
    
    def __init__(self):
        """Initialize setup manager."""
        self.project_root = Path(__file__).resolve().parent
        self.requirements_file = self.project_root / "requirements.txt"
        self.src_dir = self.project_root / "src"
        self.ops_dir = self.project_root / "ops"
        self.tools_dir = self.project_root / "tools"
        self.data_dir = self.project_root / "data"
        self.backups_dir = self.project_root / "backups"
        
        logger.info(f"EMO Setup initialized in: {self.project_root}")
    
    def validate_environment(self) -> bool:
        """Validate Python environment and basic requirements."""
        logger.info("🔍 Validating environment...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            logger.error(f"❌ Python 3.8+ required, found {python_version.major}.{python_version.minor}")
            return False
        
        logger.info(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # Check pip availability
        try:
            import pip
            logger.info(f"✅ pip available: {pip.__version__}")
        except ImportError:
            logger.error("❌ pip not available")
            return False
        
        return True
    
    def install_dependencies(self) -> bool:
        """Install all required dependencies."""
        logger.info("📦 Installing dependencies...")
        
        if not self.requirements_file.exists():
            logger.error(f"❌ Requirements file not found: {self.requirements_file}")
            return False
        
        try:
            # Install requirements
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(self.requirements_file)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"❌ pip install failed: {result.stderr}")
                return False
            
            logger.info("✅ Dependencies installed successfully")
            
            # Verify key packages
            key_packages = ["sqlalchemy", "yfinance", "pandas", "numpy"]
            for package in key_packages:
                try:
                    __import__(package)
                    logger.info(f"✅ {package} available")
                except ImportError:
                    logger.warning(f"⚠️ {package} not available")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Dependency installation failed: {e}")
            return False
    
    def create_directory_structure(self) -> bool:
        """Create necessary directory structure."""
        logger.info("📁 Creating directory structure...")
        
        directories = [
            self.data_dir,
            self.backups_dir,
            self.data_dir / "logs",
            self.data_dir / "cache",
            self.data_dir / "exports"
        ]
        
        try:
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"✅ Created: {directory}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Directory creation failed: {e}")
            return False
    
    def validate_package_structure(self) -> bool:
        """Validate package structure and imports."""
        logger.info("🏗️ Validating package structure...")
        
        # Required files and directories
        required_paths = [
            self.src_dir,
            self.ops_dir,
            self.tools_dir,
            self.ops_dir / "db" / "__init__.py",
            self.ops_dir / "db" / "session.py",
            self.ops_dir / "staging" / "__init__.py",
            self.ops_dir / "staging" / "models.py",
            self.tools_dir / "stage_order_cli.py",
            self.tools_dir / "emit_health.py",
            self.tools_dir / "db_manage.py"
        ]
        
        missing_paths = []
        for path in required_paths:
            if not path.exists():
                missing_paths.append(path)
                logger.error(f"❌ Missing: {path}")
            else:
                logger.info(f"✅ Found: {path}")
        
        if missing_paths:
            logger.error(f"❌ Package structure validation failed: {len(missing_paths)} missing files")
            return False
        
        # Test key imports
        sys.path.insert(0, str(self.project_root))
        
        import_tests = [
            ("ops.db.session", ["get_session", "init_db"]),
            ("ops.staging.models", ["StagedOrder"]),
        ]
        
        for module_name, expected_attrs in import_tests:
            try:
                module = __import__(module_name, fromlist=expected_attrs)
                for attr in expected_attrs:
                    if hasattr(module, attr):
                        logger.info(f"✅ {module_name}.{attr} available")
                    else:
                        logger.warning(f"⚠️ {module_name}.{attr} not found")
                        
            except ImportError as e:
                logger.error(f"❌ Import failed: {module_name} - {e}")
                return False
        
        logger.info("✅ Package structure validation passed")
        return True
    
    def initialize_databases(self) -> bool:
        """Initialize databases."""
        logger.info("🗄️ Initializing databases...")
        
        try:
            # Initialize OPS database
            from ops.db.session import init_db, test_connection
            
            init_db()
            
            if test_connection():
                logger.info("✅ OPS database initialized and tested")
            else:
                logger.error("❌ OPS database connection test failed")
                return False
            
            # Test institutional integration if available
            try:
                sys.path.insert(0, str(self.src_dir))
                from database.institutional_integration import InstitutionalIntegration
                
                integration = InstitutionalIntegration()
                status = integration.check_system_health()
                
                if status.database_healthy:
                    logger.info("✅ Institutional database healthy")
                else:
                    logger.warning("⚠️ Institutional database not healthy")
                    
            except ImportError:
                logger.info("ℹ️ Institutional integration not available (optional)")
            except Exception as e:
                logger.warning(f"⚠️ Institutional database check failed: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate system configuration."""
        logger.info("⚙️ Validating configuration...")
        
        config_status = {
            "environment_variables": {},
            "file_permissions": {},
            "network_connectivity": {},
            "overall_healthy": True
        }
        
        # Check environment variables
        env_vars = [
            "EMO_ENV",
            "DATABASE_URL", 
            "LOG_LEVEL"
        ]
        
        for var in env_vars:
            value = os.getenv(var)
            config_status["environment_variables"][var] = {
                "set": value is not None,
                "value": value if value else "Not set"
            }
            if not value:
                logger.info(f"ℹ️ Environment variable {var} not set (using defaults)")
        
        # Check file permissions
        key_files = [
            self.tools_dir / "stage_order_cli.py",
            self.tools_dir / "emit_health.py",
            self.tools_dir / "db_manage.py"
        ]
        
        for file_path in key_files:
            if file_path.exists():
                readable = os.access(file_path, os.R_OK)
                executable = os.access(file_path, os.X_OK)
                config_status["file_permissions"][str(file_path)] = {
                    "readable": readable,
                    "executable": executable
                }
                if not readable:
                    logger.warning(f"⚠️ File not readable: {file_path}")
                    config_status["overall_healthy"] = False
        
        # Test network connectivity (basic check)
        try:
            import socket
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            config_status["network_connectivity"]["internet"] = True
            logger.info("✅ Internet connectivity available")
        except:
            config_status["network_connectivity"]["internet"] = False
            logger.warning("⚠️ Internet connectivity limited")
        
        return config_status
    
    def run_health_checks(self) -> Dict[str, Any]:
        """Run comprehensive health checks."""
        logger.info("🏥 Running health checks...")
        
        health_status = {
            "timestamp": "2025-10-25T00:00:00Z",
            "overall_healthy": True,
            "components": {}
        }
        
        # Test CLI tool
        try:
            import subprocess
            result = subprocess.run(
                [sys.executable, str(self.tools_dir / "stage_order_cli.py"), "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            cli_healthy = result.returncode == 0
            health_status["components"]["cli_tool"] = {
                "healthy": cli_healthy,
                "details": "Help command executed successfully" if cli_healthy else result.stderr
            }
            
            if cli_healthy:
                logger.info("✅ CLI tool healthy")
            else:
                logger.error("❌ CLI tool failed")
                health_status["overall_healthy"] = False
                
        except Exception as e:
            logger.error(f"❌ CLI tool health check failed: {e}")
            health_status["components"]["cli_tool"] = {"healthy": False, "details": str(e)}
            health_status["overall_healthy"] = False
        
        # Test database manager
        try:
            result = subprocess.run(
                [sys.executable, str(self.tools_dir / "db_manage.py"), "health"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            db_healthy = result.returncode == 0
            health_status["components"]["database_manager"] = {
                "healthy": db_healthy,
                "details": "Health check passed" if db_healthy else result.stderr
            }
            
            if db_healthy:
                logger.info("✅ Database manager healthy")
            else:
                logger.error("❌ Database manager failed")
                health_status["overall_healthy"] = False
                
        except Exception as e:
            logger.error(f"❌ Database manager health check failed: {e}")
            health_status["components"]["database_manager"] = {"healthy": False, "details": str(e)}
            health_status["overall_healthy"] = False
        
        # Test health monitoring
        try:
            from tools.emit_health import _get_institutional_status, get_system_metrics
            
            inst_status = _get_institutional_status()
            sys_metrics = get_system_metrics()
            
            health_monitoring_healthy = True
            health_status["components"]["health_monitoring"] = {
                "healthy": health_monitoring_healthy,
                "institutional_available": inst_status.get("available", False),
                "system_metrics_available": "error" not in sys_metrics
            }
            
            logger.info("✅ Health monitoring healthy")
            
        except Exception as e:
            logger.error(f"❌ Health monitoring check failed: {e}")
            health_status["components"]["health_monitoring"] = {"healthy": False, "details": str(e)}
            health_status["overall_healthy"] = False
        
        return health_status
    
    def create_startup_scripts(self) -> bool:
        """Create startup and utility scripts."""
        logger.info("📜 Creating startup scripts...")
        
        try:
            # Create start script
            start_script = self.project_root / "start_emo.py"
            start_script_content = '''#!/usr/bin/env python3
"""
EMO Options Bot Startup Script
=============================
Comprehensive startup script that initializes all components.
"""

import sys
import logging
from pathlib import Path

# Add project paths
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from tools.emit_health import serve_health_monitor
from ops.db.session import init_db, test_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Start EMO Options Bot services."""
    logger.info("🚀 Starting EMO Options Bot...")
    
    # Initialize databases
    logger.info("📊 Initializing databases...")
    init_db()
    
    if not test_connection():
        logger.error("❌ Database connection failed")
        return False
    
    logger.info("✅ Database initialized")
    
    # Start health monitoring
    logger.info("🏥 Starting health monitoring...")
    try:
        thread, server = serve_health_monitor(port=8082)
        logger.info("✅ Health monitoring started on http://localhost:8082")
        
        logger.info("🎉 EMO Options Bot started successfully!")
        logger.info("   📋 Orders: http://localhost:8082/orders.html")
        logger.info("   🏥 Health: http://localhost:8082/health")
        logger.info("   📊 Metrics: http://localhost:8082/metrics")
        
        # Keep running
        try:
            thread.join()
        except KeyboardInterrupt:
            logger.info("\\n🛑 Shutting down...")
            server.shutdown()
            
    except Exception as e:
        logger.error(f"❌ Failed to start services: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
'''
            
            with open(start_script, 'w') as f:
                f.write(start_script_content)
            
            logger.info(f"✅ Created startup script: {start_script}")
            
            # Create validation script
            validate_script = self.project_root / "validate_system.py"
            validate_script_content = '''#!/usr/bin/env python3
"""
EMO Options Bot System Validation Script
=======================================
Comprehensive system validation and health checking.
"""

import sys
import json
from pathlib import Path

# Add project paths
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from setup import EMOSetup

def main():
    """Run comprehensive system validation."""
    print("🔍 EMO Options Bot System Validation")
    print("=" * 50)
    
    setup = EMOSetup()
    
    # Run all validation steps
    steps = [
        ("Environment", setup.validate_environment),
        ("Package Structure", setup.validate_package_structure),
        ("Database Initialization", setup.initialize_databases),
    ]
    
    all_passed = True
    
    for step_name, step_func in steps:
        print(f"\\n📋 {step_name}...")
        try:
            result = step_func()
            if result:
                print(f"✅ {step_name} passed")
            else:
                print(f"❌ {step_name} failed")
                all_passed = False
        except Exception as e:
            print(f"💥 {step_name} error: {e}")
            all_passed = False
    
    # Configuration validation
    print(f"\\n📋 Configuration...")
    try:
        config = setup.validate_configuration()
        print(f"{'✅' if config['overall_healthy'] else '⚠️'} Configuration check completed")
        print(json.dumps(config, indent=2))
    except Exception as e:
        print(f"💥 Configuration error: {e}")
        all_passed = False
    
    # Health checks
    print(f"\\n📋 Health Checks...")
    try:
        health = setup.run_health_checks()
        print(f"{'✅' if health['overall_healthy'] else '❌'} Health checks completed")
        print(json.dumps(health, indent=2))
    except Exception as e:
        print(f"💥 Health check error: {e}")
        all_passed = False
    
    print(f"\\n{'🎉' if all_passed else '💥'} System validation {'PASSED' if all_passed else 'FAILED'}")
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
'''
            
            with open(validate_script, 'w') as f:
                f.write(validate_script_content)
            
            logger.info(f"✅ Created validation script: {validate_script}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create scripts: {e}")
            return False
    
    def run_full_setup(self) -> bool:
        """Run complete setup process."""
        logger.info("🚀 Running full EMO Options Bot setup...")
        
        steps = [
            ("Environment Validation", self.validate_environment),
            ("Directory Structure", self.create_directory_structure),
            ("Dependency Installation", self.install_dependencies),
            ("Package Structure", self.validate_package_structure),
            ("Database Initialization", self.initialize_databases),
            ("Startup Scripts", self.create_startup_scripts),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"📋 {step_name}...")
            try:
                if not step_func():
                    logger.error(f"❌ Setup failed at: {step_name}")
                    return False
                logger.info(f"✅ {step_name} completed")
            except Exception as e:
                logger.error(f"💥 Setup error in {step_name}: {e}")
                return False
        
        # Final validation
        logger.info("🏁 Running final validation...")
        try:
            config = self.validate_configuration()
            health = self.run_health_checks()
            
            logger.info("📊 Setup Summary:")
            logger.info(f"  Configuration: {'✅ Healthy' if config['overall_healthy'] else '⚠️ Issues'}")
            logger.info(f"  Health Checks: {'✅ Passed' if health['overall_healthy'] else '❌ Failed'}")
            
            if config['overall_healthy'] and health['overall_healthy']:
                logger.info("🎉 EMO Options Bot setup completed successfully!")
                logger.info("🚀 Ready to start trading operations!")
                return True
            else:
                logger.warning("⚠️ Setup completed with some issues - check logs above")
                return False
                
        except Exception as e:
            logger.error(f"💥 Final validation failed: {e}")
            return False

def main():
    """Main setup entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="EMO Options Bot Setup")
    parser.add_argument("--full", action="store_true", help="Run full setup")
    parser.add_argument("--validate", action="store_true", help="Validate only")
    parser.add_argument("--deps", action="store_true", help="Install dependencies only")
    parser.add_argument("--db", action="store_true", help="Initialize databases only")
    
    args = parser.parse_args()
    
    setup = EMOSetup()
    
    try:
        if args.full or not any([args.validate, args.deps, args.db]):
            success = setup.run_full_setup()
            sys.exit(0 if success else 1)
        
        if args.validate:
            env_ok = setup.validate_environment()
            pkg_ok = setup.validate_package_structure()
            success = env_ok and pkg_ok
            sys.exit(0 if success else 1)
        
        if args.deps:
            success = setup.install_dependencies()
            sys.exit(0 if success else 1)
        
        if args.db:
            success = setup.initialize_databases()
            sys.exit(0 if success else 1)
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()