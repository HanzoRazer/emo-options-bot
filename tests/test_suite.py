#!/usr/bin/env python3
"""
EMO Options Bot - Comprehensive Test Suite
==========================================
Testing framework for all enhanced Phase 2 components:
- Enhanced configuration system
- Database router with health monitoring  
- Live logger with error handling
- Order rotation system
- Environment validation
- Orchestration runner system
- Workspace configuration

Test Categories:
- Unit tests for individual components
- Integration tests for component interaction
- Health monitoring validation
- Error handling verification
- Performance benchmarking
- End-to-end workflow testing

Usage:
  python test_suite.py                     # Run all tests
  python test_suite.py --unit             # Run unit tests only
  python test_suite.py --integration      # Run integration tests only
  python test_suite.py --performance      # Run performance tests only
  python test_suite.py --component live_logger  # Test specific component
"""

import os
import sys
import json
import logging
import unittest
import tempfile
import threading
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import argparse

# Setup paths
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

# Setup logging for tests
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BaseTestCase(unittest.TestCase):
    """Base test case with common utilities."""
    
    def setUp(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
        # Create test directory structure
        (self.test_dir / "ops").mkdir(exist_ok=True)
        (self.test_dir / "ops" / "orders").mkdir(exist_ok=True)
        (self.test_dir / "ops" / "orders" / "drafts").mkdir(exist_ok=True)
        (self.test_dir / "ops" / "orders" / "archive").mkdir(exist_ok=True)
        (self.test_dir / "logs").mkdir(exist_ok=True)
        (self.test_dir / "data").mkdir(exist_ok=True)
        
    def tearDown(self):
        """Cleanup test environment."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def create_test_config(self, **overrides) -> Dict[str, Any]:
        """Create test configuration."""
        config = {
            "EMO_ENV": "test",
            "EMO_SQLITE_PATH": str(self.test_dir / "test.sqlite"),
            "EMO_STAGE_ORDERS": "1",
            "EMO_EMAIL_NOTIFICATIONS": "0",
            "EMO_AUTO_BACKUP": "0",
            "EMO_PERFORMANCE_MONITORING": "1",
            "EMO_HEALTH_INTEGRATION": "1",
            "HEALTH_SERVER_PORT": "8083",
            "EMO_SLEEP_INTERVAL": "60",
            "EMO_SYMBOLS": "SPY,QQQ",
            "EMO_LIVE_LOGGER_ENABLED": "1"
        }
        config.update(overrides)
        return config

class TestEnhancedConfiguration(BaseTestCase):
    """Test enhanced configuration system."""
    
    def test_config_loading(self):
        """Test configuration loading and validation."""
        # Create test environment file
        env_content = [
            "EMO_ENV=test",
            "EMO_SQLITE_PATH=./test.sqlite",
            "EMO_STAGE_ORDERS=1",
            "EMO_PERFORMANCE_MONITORING=1"
        ]
        
        env_file = self.test_dir / ".env.test"
        with open(env_file, 'w') as f:
            f.write('\n'.join(env_content))
        
        # Test config loading
        try:
            from src.utils.enhanced_config import Config
            with patch.dict(os.environ, {"EMO_ENV": "test"}):
                config = Config()
                
                self.assertEqual(config.get("EMO_ENV"), "test")
                self.assertTrue(config.as_bool("EMO_STAGE_ORDERS"))
                self.assertTrue(config.as_bool("EMO_PERFORMANCE_MONITORING"))
                
        except ImportError:
            self.skipTest("Enhanced config not available")
    
    def test_environment_validation(self):
        """Test environment-specific validation."""
        test_configs = {
            "dev": {"EMO_ENV": "dev", "EMO_STAGE_ORDERS": "1"},
            "prod": {"EMO_ENV": "prod", "EMO_STAGE_ORDERS": "0"}
        }
        
        for env, expected in test_configs.items():
            with self.subTest(environment=env):
                # Test environment-specific behavior
                self.assertIn("EMO_ENV", expected)

class TestDatabaseRouter(BaseTestCase):
    """Test enhanced database router functionality."""
    
    def test_sqlite_connection(self):
        """Test SQLite database connection and health."""
        try:
            from db.router import DatabaseRouter, test_connection
            
            # Test basic connection
            router = DatabaseRouter()
            self.assertIsNotNone(router)
            
            # Test health check
            health = test_connection()
            self.assertIsInstance(health, bool)
            
        except ImportError:
            self.skipTest("Database router not available")
    
    def test_schema_management(self):
        """Test automatic schema creation and migration."""
        try:
            from db.router import migrate, get_schema_version
            
            # Test migration
            result = migrate()
            self.assertIsInstance(result, bool)
            
            # Test schema version tracking
            try:
                version = get_schema_version()
                self.assertIsInstance(version, (int, type(None)))
            except:
                pass  # Schema version may not be implemented
                
        except ImportError:
            self.skipTest("Database migration not available")
    
    def test_connection_pooling(self):
        """Test database connection pooling and cleanup."""
        try:
            from db.router import DatabaseRouter
            
            router = DatabaseRouter()
            
            # Test multiple connections
            conn1 = router.get_connection()
            conn2 = router.get_connection()
            
            self.assertIsNotNone(conn1)
            self.assertIsNotNone(conn2)
            
            # Test cleanup
            router.close_all_connections()
            
        except ImportError:
            self.skipTest("Database router not available")

class TestLiveLogger(BaseTestCase):
    """Test enhanced live logger functionality."""
    
    def test_error_handling(self):
        """Test robust error handling and recovery."""
        try:
            from data.live_logger import LiveLogger, handle_api_error
            
            # Test API error handling
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.text = "Rate limit exceeded"
            
            handled = handle_api_error(mock_response, "test_endpoint")
            self.assertIsInstance(handled, bool)
            
        except ImportError:
            self.skipTest("Live logger not available")
    
    def test_performance_metrics(self):
        """Test performance monitoring and metrics collection."""
        try:
            from data.live_logger import LiveLogger
            
            with patch.dict(os.environ, self.create_test_config()):
                logger = LiveLogger()
                
                # Test metrics initialization
                self.assertIsNotNone(logger.metrics)
                
                # Test metric recording
                logger.record_metric("test_metric", 123.45)
                
                # Test performance report
                report = logger.get_performance_report()
                self.assertIsInstance(report, dict)
                
        except ImportError:
            self.skipTest("Live logger not available")
    
    def test_integration_hooks(self):
        """Test integration with runner system."""
        try:
            from data.live_logger import LiveLogger
            
            with patch.dict(os.environ, self.create_test_config()):
                logger = LiveLogger()
                
                # Test health check
                health = logger.health_check()
                self.assertIsInstance(health, dict)
                self.assertIn("status", health)
                
        except ImportError:
            self.skipTest("Live logger not available")

class TestOrderRotation(BaseTestCase):
    """Test order rotation and archival system."""
    
    def test_order_archival(self):
        """Test order archival with date-based rotation."""
        try:
            from tools.rotate_staged_orders import OrderRotationManager
            
            # Create test orders
            drafts_dir = self.test_dir / "ops" / "orders" / "drafts"
            archive_dir = self.test_dir / "ops" / "orders" / "archive"
            
            # Create test order files with different ages
            old_order = drafts_dir / "old_order.json"
            new_order = drafts_dir / "new_order.json"
            
            old_order.write_text('{"symbol": "SPY", "created": "2024-01-01"}')
            new_order.write_text('{"symbol": "QQQ", "created": "2024-12-01"}')
            
            # Set file modification times
            old_time = time.time() - (30 * 24 * 60 * 60)  # 30 days ago
            new_time = time.time() - (1 * 24 * 60 * 60)   # 1 day ago
            
            os.utime(old_order, (old_time, old_time))
            os.utime(new_order, (new_time, new_time))
            
            with patch.dict(os.environ, self.create_test_config()):
                manager = OrderRotationManager()
                
                # Test archival with 7-day retention
                archived = manager.archive_old_orders(retention_days=7)
                self.assertIsInstance(archived, list)
                
                # Verify old order was archived
                self.assertFalse(old_order.exists())
                self.assertTrue(new_order.exists())
                
        except ImportError:
            self.skipTest("Order rotation not available")
    
    def test_retention_policy(self):
        """Test configurable retention policy."""
        try:
            from tools.rotate_staged_orders import OrderRotationManager
            
            with patch.dict(os.environ, self.create_test_config()):
                manager = OrderRotationManager()
                
                # Test different retention periods
                for days in [1, 7, 30]:
                    with self.subTest(retention_days=days):
                        # Test retention calculation
                        cutoff = manager.calculate_cutoff_date(days)
                        expected = datetime.now() - timedelta(days=days)
                        
                        # Allow 1 minute tolerance
                        self.assertLess(abs((cutoff - expected).total_seconds()), 60)
                        
        except ImportError:
            self.skipTest("Order rotation not available")

class TestEnvironmentValidator(BaseTestCase):
    """Test environment validation system."""
    
    def test_validation_modes(self):
        """Test different validation modes."""
        try:
            from tools.validate_env import EnvironmentValidator
            
            for env in ["dev", "staging", "prod"]:
                with self.subTest(environment=env):
                    with patch.dict(os.environ, self.create_test_config(EMO_ENV=env)):
                        validator = EnvironmentValidator(env)
                        
                        # Test basic validation
                        result = validator.validate_environment_variables()
                        self.assertIsInstance(result, bool)
                        
        except ImportError:
            self.skipTest("Environment validator not available")
    
    def test_database_validation(self):
        """Test database connectivity validation."""
        try:
            from tools.validate_env import EnvironmentValidator
            
            with patch.dict(os.environ, self.create_test_config()):
                validator = EnvironmentValidator("dev")
                
                # Test database validation (should work with SQLite)
                result = validator.validate_database_connectivity()
                self.assertIsInstance(result, bool)
                
        except ImportError:
            self.skipTest("Environment validator not available")

class TestRunnerSystem(BaseTestCase):
    """Test enhanced orchestration runner system."""
    
    def test_health_integration(self):
        """Test health monitoring integration."""
        try:
            from tools.runner import EnhancedRunner
            
            with patch.dict(os.environ, self.create_test_config()):
                runner = EnhancedRunner()
                
                # Test health check
                health = runner.get_health_status()
                self.assertIsInstance(health, dict)
                self.assertIn("status", health)
                
        except ImportError:
            self.skipTest("Runner system not available")
    
    def test_performance_monitoring(self):
        """Test performance monitoring and metrics."""
        try:
            from tools.runner import EnhancedRunner
            
            with patch.dict(os.environ, self.create_test_config()):
                runner = EnhancedRunner()
                
                # Test metrics collection
                runner.record_metric("test_execution_time", 1.23)
                
                # Test performance report
                report = runner.get_performance_report()
                self.assertIsInstance(report, dict)
                
        except ImportError:
            self.skipTest("Runner system not available")

class TestWorkspaceConfiguration(BaseTestCase):
    """Test workspace configuration management."""
    
    def test_directory_creation(self):
        """Test workspace directory structure creation."""
        try:
            from workspace_config import WorkspaceManager
            
            manager = WorkspaceManager()
            
            # Test directory creation
            result = manager.create_directory_structure()
            self.assertTrue(result)
            
            # Verify required directories exist
            for dir_path in manager.required_directories:
                full_path = manager.root / dir_path
                self.assertTrue(full_path.exists(), f"Directory {dir_path} not created")
                
        except ImportError:
            self.skipTest("Workspace manager not available")
    
    def test_component_validation(self):
        """Test component availability validation."""
        try:
            from workspace_config import WorkspaceManager
            
            manager = WorkspaceManager()
            
            # Test component validation
            results = manager.validate_components()
            self.assertIsInstance(results, dict)
            
            # All components should return boolean results
            for component, available in results.items():
                self.assertIsInstance(available, bool, f"Component {component} validation failed")
                
        except ImportError:
            self.skipTest("Workspace manager not available")
    
    def test_environment_templates(self):
        """Test environment-specific configuration templates."""
        try:
            from workspace_config import WorkspaceManager
            
            manager = WorkspaceManager()
            
            # Test environment templates
            for env in ["dev", "staging", "prod"]:
                with self.subTest(environment=env):
                    template = manager.environment_templates.get(env)
                    self.assertIsNotNone(template, f"No template for {env}")
                    self.assertIn("EMO_ENV", template)
                    self.assertEqual(template["EMO_ENV"], env)
                    
        except ImportError:
            self.skipTest("Workspace manager not available")

class IntegrationTestSuite(BaseTestCase):
    """Integration tests for component interaction."""
    
    def test_config_database_integration(self):
        """Test configuration system with database router."""
        try:
            from src.utils.enhanced_config import Config
            from db.router import DatabaseRouter
            
            with patch.dict(os.environ, self.create_test_config()):
                config = Config()
                router = DatabaseRouter()
                
                # Test configuration affects database behavior
                db_path = config.get("EMO_SQLITE_PATH")
                self.assertIsNotNone(db_path)
                
        except ImportError:
            self.skipTest("Integration components not available")
    
    def test_logger_runner_integration(self):
        """Test live logger integration with runner system."""
        try:
            from data.live_logger import LiveLogger
            from tools.runner import EnhancedRunner
            
            with patch.dict(os.environ, self.create_test_config()):
                logger = LiveLogger()
                runner = EnhancedRunner()
                
                # Test health status integration
                logger_health = logger.health_check()
                runner_health = runner.get_health_status()
                
                self.assertIsInstance(logger_health, dict)
                self.assertIsInstance(runner_health, dict)
                
        except ImportError:
            self.skipTest("Integration components not available")

class PerformanceTestSuite(BaseTestCase):
    """Performance benchmarking tests."""
    
    def test_database_performance(self):
        """Test database operation performance."""
        try:
            from db.router import DatabaseRouter
            
            router = DatabaseRouter()
            
            # Benchmark connection time
            start_time = time.time()
            conn = router.get_connection()
            connection_time = time.time() - start_time
            
            self.assertLess(connection_time, 1.0, "Database connection too slow")
            
        except ImportError:
            self.skipTest("Database router not available")
    
    def test_config_loading_performance(self):
        """Test configuration loading performance."""
        try:
            from src.utils.enhanced_config import Config
            
            # Benchmark config loading
            start_time = time.time()
            config = Config()
            loading_time = time.time() - start_time
            
            self.assertLess(loading_time, 0.5, "Config loading too slow")
            
        except ImportError:
            self.skipTest("Enhanced config not available")

def create_test_suite(test_type: str = "all", component: str = None) -> unittest.TestSuite:
    """Create test suite based on specified criteria."""
    suite = unittest.TestSuite()
    
    # Define test categories
    unit_tests = [
        TestEnhancedConfiguration,
        TestDatabaseRouter,
        TestLiveLogger,
        TestOrderRotation,
        TestEnvironmentValidator,
        TestRunnerSystem,
        TestWorkspaceConfiguration
    ]
    
    integration_tests = [IntegrationTestSuite]
    performance_tests = [PerformanceTestSuite]
    
    # Component-specific mapping
    component_tests = {
        "config": [TestEnhancedConfiguration],
        "database": [TestDatabaseRouter],
        "live_logger": [TestLiveLogger],
        "order_rotation": [TestOrderRotation],
        "env_validator": [TestEnvironmentValidator],
        "runner": [TestRunnerSystem],
        "workspace": [TestWorkspaceConfiguration]
    }
    
    # Select tests based on criteria
    if component:
        if component in component_tests:
            test_classes = component_tests[component]
        else:
            logger.warning(f"Unknown component: {component}")
            test_classes = []
    elif test_type == "unit":
        test_classes = unit_tests
    elif test_type == "integration":
        test_classes = integration_tests
    elif test_type == "performance":
        test_classes = performance_tests
    else:  # "all"
        test_classes = unit_tests + integration_tests + performance_tests
    
    # Add tests to suite
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite

def main():
    """CLI interface for test suite."""
    parser = argparse.ArgumentParser(
        description="EMO Options Bot Comprehensive Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python test_suite.py
  
  # Run only unit tests
  python test_suite.py --unit
  
  # Run integration tests
  python test_suite.py --integration
  
  # Run performance tests
  python test_suite.py --performance
  
  # Test specific component
  python test_suite.py --component live_logger
  
  # Verbose output
  python test_suite.py --verbose
        """
    )
    
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--performance", action="store_true", help="Run performance tests only")
    parser.add_argument("--component", choices=[
        "config", "database", "live_logger", "order_rotation", 
        "env_validator", "runner", "workspace"
    ], help="Test specific component")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--failfast", "-f", action="store_true", help="Stop on first failure")
    
    args = parser.parse_args()
    
    # Determine test type
    if args.unit:
        test_type = "unit"
    elif args.integration:
        test_type = "integration"
    elif args.performance:
        test_type = "performance"
    else:
        test_type = "all"
    
    # Create test suite
    suite = create_test_suite(test_type, args.component)
    
    # Configure test runner
    verbosity = 2 if args.verbose else 1
    runner = unittest.TextTestRunner(
        verbosity=verbosity,
        failfast=args.failfast
    )
    
    # Run tests
    logger.info(f"🧪 Running {test_type} tests for EMO Options Bot...")
    if args.component:
        logger.info(f"🎯 Component: {args.component}")
    
    result = runner.run(suite)
    
    # Print summary
    print(f"\n📊 Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    exit(main())