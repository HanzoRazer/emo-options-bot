#!/usr/bin/env python3
"""
Robust Test Runner
Enhanced test runner with dependency management and health monitoring
"""

import sys
import json
import time
import signal
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from tools.dependency_manager import DependencyManager
    from tools.health_monitor import SystemHealthMonitor
    from src.utils.robust_handler import RobustLogger
    from src.config.robust_config import get_config
except ImportError as e:
    print(f"Warning: Could not import robust modules: {e}")
    DependencyManager = None
    SystemHealthMonitor = None
    RobustLogger = None
    get_config = None

class RobustTestRunner:
    """Enhanced test runner with robustness features."""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.start_time = datetime.now()
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.tests_skipped = 0
        self.test_results: List[Dict] = []
        self.timeout_handler = None
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for test runner."""
        if RobustLogger:
            robust_logger = RobustLogger("test_runner")
            return robust_logger.logger
        else:
            # Fallback logging setup
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            return logging.getLogger("test_runner")
    
    def setup_timeout_handler(self, timeout_seconds: int = 300):
        """Setup timeout handler to prevent hanging tests."""
        def timeout_handler(signum, frame):
            self.logger.error(f"Test execution timed out after {timeout_seconds} seconds")
            raise TimeoutError(f"Test execution exceeded {timeout_seconds} second timeout")
        
        self.timeout_handler = timeout_handler
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
    
    def clear_timeout(self):
        """Clear the timeout alarm."""
        if self.timeout_handler:
            signal.alarm(0)
    
    def pre_flight_checks(self) -> Dict[str, Any]:
        """Perform pre-flight checks before running tests."""
        self.logger.info("Performing pre-flight checks...")
        
        checks = {
            "timestamp": datetime.now().isoformat(),
            "system_health": {},
            "dependencies": {},
            "configuration": {},
            "environment": {}
        }
        
        # System health check
        if SystemHealthMonitor:
            try:
                monitor = SystemHealthMonitor()
                health_data = monitor.perform_comprehensive_check()
                checks["system_health"] = {
                    "status": health_data["overall_status"],
                    "cpu_percent": health_data["system_resources"].get("cpu", {}).get("percent", 0),
                    "memory_percent": health_data["system_resources"].get("memory", {}).get("percent_used", 0),
                    "disk_percent": health_data["system_resources"].get("disk", {}).get("percent_used", 0)
                }
                self.logger.info(f"System health: {health_data['overall_status']}")
            except Exception as e:
                self.logger.warning(f"System health check failed: {e}")
                checks["system_health"]["error"] = str(e)
        
        # Dependency check
        if DependencyManager:
            try:
                dep_manager = DependencyManager()
                healthy, results = dep_manager.validate_and_repair(auto_install=True)
                checks["dependencies"] = {
                    "healthy": healthy,
                    "core_available": sum(1 for info in results["core_modules"].values() 
                                        if info["status"] == "available"),
                    "core_total": len(results["core_modules"]),
                    "missing_modules": [name for name, info in results["core_modules"].items() 
                                      if info["status"] != "available"]
                }
                self.logger.info(f"Dependencies healthy: {healthy}")
            except Exception as e:
                self.logger.warning(f"Dependency check failed: {e}")
                checks["dependencies"]["error"] = str(e)
        
        # Configuration check
        if get_config:
            try:
                config = get_config()
                is_valid = config.validate()
                checks["configuration"] = {
                    "valid": is_valid,
                    "environment": config.system.environment.value,
                    "order_mode": config.trading.order_mode,
                    "errors": config.validation_errors,
                    "warnings": config.validation_warnings
                }
                self.logger.info(f"Configuration valid: {is_valid}")
            except Exception as e:
                self.logger.warning(f"Configuration check failed: {e}")
                checks["configuration"]["error"] = str(e)
        
        # Environment variables check
        import os
        critical_env_vars = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY", 
            "ALPACA_API_KEY",
            "ALPACA_SECRET_KEY"
        ]
        
        env_status = {}
        for var in critical_env_vars:
            value = os.getenv(var)
            env_status[var] = {
                "set": value is not None,
                "length": len(value) if value else 0
            }
        
        checks["environment"] = env_status
        
        return checks
    
    def run_llm_routing_test(self) -> Dict[str, Any]:
        """Run the LLM routing test with robustness."""
        test_result = {
            "name": "LLM Routing Test",
            "start_time": datetime.now().isoformat(),
            "status": "running",
            "duration_seconds": 0,
            "output": [],
            "error": None
        }
        
        self.logger.info("Starting LLM routing test...")
        
        try:
            # Setup timeout
            self.setup_timeout_handler(180)  # 3 minute timeout
            
            # Change to project directory
            original_cwd = Path.cwd()
            os.chdir(project_root)
            
            # Run the test script
            self.logger.info("Executing test-llm-routing.ps1...")
            
            # Use PowerShell to run the script
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", ".\\test-llm-routing.ps1"]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=project_root
            )
            
            # Monitor process with timeout
            stdout_lines = []
            stderr_lines = []
            
            start_time = time.time()
            timeout = 180  # 3 minutes
            
            while True:
                # Check if process has completed
                return_code = process.poll()
                if return_code is not None:
                    # Process completed
                    remaining_stdout, remaining_stderr = process.communicate()
                    if remaining_stdout:
                        stdout_lines.append(remaining_stdout)
                    if remaining_stderr:
                        stderr_lines.append(remaining_stderr)
                    break
                
                # Check for timeout
                if time.time() - start_time > timeout:
                    self.logger.error("Test process timed out, terminating...")
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    raise TimeoutError("Test process exceeded timeout")
                
                # Read available output
                try:
                    import select
                    ready, _, _ = select.select([process.stdout, process.stderr], [], [], 1)
                    for stream in ready:
                        if stream == process.stdout:
                            line = stream.readline()
                            if line:
                                stdout_lines.append(line)
                                self.logger.info(f"Test output: {line.strip()}")
                        elif stream == process.stderr:
                            line = stream.readline()
                            if line:
                                stderr_lines.append(line)
                                self.logger.warning(f"Test error: {line.strip()}")
                except (ImportError, OSError):
                    # select not available on Windows, fall back to polling
                    time.sleep(1)
            
            # Collect results
            stdout_output = "".join(stdout_lines)
            stderr_output = "".join(stderr_lines)
            
            test_result["output"] = stdout_lines + stderr_lines
            test_result["return_code"] = return_code
            test_result["duration_seconds"] = time.time() - start_time
            
            if return_code == 0:
                test_result["status"] = "passed"
                self.logger.info("LLM routing test completed successfully")
            else:
                test_result["status"] = "failed"
                test_result["error"] = f"Process exited with code {return_code}"
                self.logger.error(f"LLM routing test failed with code {return_code}")
            
        except TimeoutError as e:
            test_result["status"] = "timeout"
            test_result["error"] = str(e)
            test_result["duration_seconds"] = time.time() - start_time
            self.logger.error(f"Test timed out: {e}")
        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
            test_result["duration_seconds"] = time.time() - start_time
            self.logger.error(f"Test failed with error: {e}")
        finally:
            # Restore directory and clear timeout
            os.chdir(original_cwd)
            self.clear_timeout()
            test_result["end_time"] = datetime.now().isoformat()
        
        return test_result
    
    def run_phase3_component_tests(self) -> List[Dict[str, Any]]:
        """Run individual Phase 3 component tests."""
        self.logger.info("Running Phase 3 component tests...")
        
        components = [
            ("LLM Trade Plan Generator", "tools/llm_trade_plan.py"),
            ("Trade Plan Validator", "tools/validate_trade_plan.py"),
            ("Phase 3 Trade Stager", "tools/phase3_stage_trade.py")
        ]
        
        test_results = []
        
        for component_name, script_path in components:
            test_result = {
                "name": f"{component_name} Test",
                "component": component_name,
                "script_path": script_path,
                "start_time": datetime.now().isoformat(),
                "status": "running"
            }
            
            try:
                start_time = time.time()
                
                # Import and test the module
                sys.path.insert(0, str(project_root))
                
                if "llm_trade_plan" in script_path:
                    from tools.llm_trade_plan import generate_trade_plan, TradeRequest
                    
                    # Test with sample request
                    request = TradeRequest(
                        description="Buy 1 SPY call option at the money for next Friday",
                        risk_tolerance="moderate",
                        max_loss=500
                    )
                    
                    result = generate_trade_plan(request)
                    test_result["sample_output"] = result
                    
                elif "validate_trade_plan" in script_path:
                    from tools.validate_trade_plan import validate_trade_plan
                    
                    # Test with sample plan
                    sample_plan = {
                        "strategy": "long_call",
                        "symbol": "SPY",
                        "legs": [{"action": "buy", "quantity": 1, "strike": 450, "expiry": "2024-01-19"}],
                        "max_loss": 500,
                        "target_profit": 1000
                    }
                    
                    is_valid, errors, warnings = validate_trade_plan(sample_plan)
                    test_result["validation_result"] = {
                        "valid": is_valid,
                        "errors": errors,
                        "warnings": warnings
                    }
                    
                elif "phase3_stage_trade" in script_path:
                    from tools.phase3_stage_trade import stage_trade_for_approval
                    
                    # Test staging functionality
                    sample_plan = {
                        "strategy": "long_call",
                        "symbol": "SPY",
                        "legs": [{"action": "buy", "quantity": 1, "strike": 450, "expiry": "2024-01-19"}]
                    }
                    
                    staging_result = stage_trade_for_approval(sample_plan, "test_user")
                    test_result["staging_result"] = staging_result
                
                test_result["status"] = "passed"
                test_result["duration_seconds"] = time.time() - start_time
                self.logger.info(f"{component_name} test passed")
                
            except Exception as e:
                test_result["status"] = "failed"
                test_result["error"] = str(e)
                test_result["duration_seconds"] = time.time() - start_time
                self.logger.error(f"{component_name} test failed: {e}")
            finally:
                test_result["end_time"] = datetime.now().isoformat()
            
            test_results.append(test_result)
        
        return test_results
    
    def run_dependency_health_test(self) -> Dict[str, Any]:
        """Run dependency health test."""
        test_result = {
            "name": "Dependency Health Test",
            "start_time": datetime.now().isoformat(),
            "status": "running"
        }
        
        try:
            start_time = time.time()
            
            if DependencyManager:
                dep_manager = DependencyManager()
                healthy, results = dep_manager.validate_and_repair(auto_install=False)
                
                test_result.update({
                    "healthy": healthy,
                    "results": results,
                    "status": "passed" if healthy else "failed"
                })
                
                self.logger.info(f"Dependency health test: {'passed' if healthy else 'failed'}")
            else:
                test_result["status"] = "skipped"
                test_result["reason"] = "DependencyManager not available"
                self.logger.warning("Dependency health test skipped - DependencyManager not available")
            
            test_result["duration_seconds"] = time.time() - start_time
            
        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
            test_result["duration_seconds"] = time.time() - start_time
            self.logger.error(f"Dependency health test error: {e}")
        finally:
            test_result["end_time"] = datetime.now().isoformat()
        
        return test_result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite."""
        self.logger.info("Starting comprehensive test suite...")
        
        suite_result = {
            "suite_name": "EMO Options Bot Comprehensive Tests",
            "start_time": datetime.now().isoformat(),
            "pre_flight_checks": {},
            "tests": [],
            "summary": {}
        }
        
        try:
            # Pre-flight checks
            suite_result["pre_flight_checks"] = self.pre_flight_checks()
            
            # Run individual tests
            tests_to_run = [
                ("Dependency Health", self.run_dependency_health_test),
                ("Phase 3 Components", self.run_phase3_component_tests),
                ("LLM Routing", self.run_llm_routing_test)
            ]
            
            for test_name, test_function in tests_to_run:
                self.logger.info(f"Running {test_name} test(s)...")
                
                try:
                    if test_name == "Phase 3 Components":
                        # This returns a list of test results
                        test_results = test_function()
                        suite_result["tests"].extend(test_results)
                        for result in test_results:
                            self._update_test_counts(result)
                    else:
                        # This returns a single test result
                        test_result = test_function()
                        suite_result["tests"].append(test_result)
                        self._update_test_counts(test_result)
                        
                except Exception as e:
                    error_result = {
                        "name": f"{test_name} Test",
                        "status": "error",
                        "error": str(e),
                        "start_time": datetime.now().isoformat(),
                        "end_time": datetime.now().isoformat(),
                        "duration_seconds": 0
                    }
                    suite_result["tests"].append(error_result)
                    self._update_test_counts(error_result)
                    self.logger.error(f"Error running {test_name} test: {e}")
            
            # Generate summary
            suite_result["summary"] = {
                "total_tests": self.tests_run,
                "passed": self.tests_passed,
                "failed": self.tests_failed,
                "skipped": self.tests_skipped,
                "errors": len([t for t in suite_result["tests"] if t["status"] == "error"]),
                "success_rate": (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0,
                "total_duration": (datetime.now() - self.start_time).total_seconds()
            }
            
            suite_result["end_time"] = datetime.now().isoformat()
            suite_result["overall_status"] = "passed" if self.tests_failed == 0 else "failed"
            
            self.logger.info(f"Test suite completed: {self.tests_passed}/{self.tests_run} passed")
            
        except Exception as e:
            suite_result["error"] = str(e)
            suite_result["overall_status"] = "error"
            self.logger.error(f"Test suite error: {e}")
        
        return suite_result
    
    def _update_test_counts(self, test_result: Dict[str, Any]):
        """Update test statistics."""
        self.tests_run += 1
        
        status = test_result.get("status", "unknown")
        if status == "passed":
            self.tests_passed += 1
        elif status == "failed":
            self.tests_failed += 1
        elif status == "skipped":
            self.tests_skipped += 1
    
    def save_test_results(self, results: Dict[str, Any], file_path: Optional[Path] = None) -> Path:
        """Save test results to file."""
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = Path(f"logs/test_results_{timestamp}.json")
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info(f"Test results saved to: {file_path}")
        return file_path
    
    def generate_test_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable test report."""
        report = []
        report.append("EMO OPTIONS BOT - TEST RESULTS REPORT")
        report.append("=" * 60)
        report.append(f"Suite: {results['suite_name']}")
        report.append(f"Started: {results['start_time']}")
        report.append(f"Completed: {results.get('end_time', 'N/A')}")
        report.append("")
        
        # Summary
        summary = results.get("summary", {})
        report.append("📊 SUMMARY")
        report.append(f"   Total Tests: {summary.get('total_tests', 0)}")
        report.append(f"   Passed: {summary.get('passed', 0)} ✅")
        report.append(f"   Failed: {summary.get('failed', 0)} ❌")
        report.append(f"   Skipped: {summary.get('skipped', 0)} ⏭️")
        report.append(f"   Errors: {summary.get('errors', 0)} 🚨")
        report.append(f"   Success Rate: {summary.get('success_rate', 0):.1f}%")
        report.append(f"   Total Duration: {summary.get('total_duration', 0):.1f}s")
        report.append("")
        
        # Pre-flight checks
        preflight = results.get("pre_flight_checks", {})
        if preflight:
            report.append("🔍 PRE-FLIGHT CHECKS")
            
            # System health
            health = preflight.get("system_health", {})
            if health:
                report.append(f"   System Health: {health.get('status', 'unknown').upper()}")
                report.append(f"   CPU: {health.get('cpu_percent', 0):.1f}%")
                report.append(f"   Memory: {health.get('memory_percent', 0):.1f}%")
            
            # Dependencies
            deps = preflight.get("dependencies", {})
            if deps:
                report.append(f"   Dependencies: {'✅' if deps.get('healthy') else '❌'}")
                report.append(f"   Core Modules: {deps.get('core_available', 0)}/{deps.get('core_total', 0)}")
            
            # Configuration
            config = preflight.get("configuration", {})
            if config:
                report.append(f"   Configuration: {'✅' if config.get('valid') else '❌'}")
                report.append(f"   Environment: {config.get('environment', 'unknown')}")
            
            report.append("")
        
        # Individual test results
        report.append("🧪 TEST RESULTS")
        for test in results.get("tests", []):
            status_emoji = {
                "passed": "✅",
                "failed": "❌", 
                "skipped": "⏭️",
                "error": "🚨",
                "timeout": "⏰"
            }.get(test.get("status", "unknown"), "❓")
            
            report.append(f"   {status_emoji} {test.get('name', 'Unknown Test')}")
            
            if test.get("duration_seconds"):
                report.append(f"      Duration: {test['duration_seconds']:.2f}s")
            
            if test.get("error"):
                report.append(f"      Error: {test['error']}")
            
            if test.get("reason"):
                report.append(f"      Reason: {test['reason']}")
        
        return "\n".join(report)

def main():
    """CLI interface for robust test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="EMO Options Bot Robust Test Runner")
    parser.add_argument("--component", type=str, help="Run specific component test")
    parser.add_argument("--llm-routing", action="store_true", help="Run LLM routing test only")
    parser.add_argument("--dependencies", action="store_true", help="Run dependency test only")
    parser.add_argument("--save", type=str, help="Save results to specific file")
    parser.add_argument("--timeout", type=int, default=300, help="Test timeout in seconds")
    
    args = parser.parse_args()
    
    runner = RobustTestRunner()
    
    try:
        if args.llm_routing:
            result = runner.run_llm_routing_test()
            print(json.dumps(result, indent=2, default=str))
        elif args.dependencies:
            result = runner.run_dependency_health_test()
            print(json.dumps(result, indent=2, default=str))
        else:
            # Run full test suite
            results = runner.run_all_tests()
            
            # Print report
            print(runner.generate_test_report(results))
            
            # Save results
            if args.save:
                file_path = Path(args.save)
            else:
                file_path = None
            
            saved_path = runner.save_test_results(results, file_path)
            print(f"\nDetailed results saved to: {saved_path}")
            
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test runner error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()