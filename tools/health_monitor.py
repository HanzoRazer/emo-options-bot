#!/usr/bin/env python3
"""
System Health Monitor
Comprehensive health checking and monitoring for EMO Options Bot
"""

import sys
import json
import time
import psutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import subprocess
import logging

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from tools.dependency_manager import DependencyManager
    from src.utils.robust_handler import get_all_loggers_health
    from src.config.robust_config import get_config, RobustConfig
except ImportError as e:
    print(f"Warning: Could not import health monitoring modules: {e}")
    DependencyManager = None
    get_all_loggers_health = None
    get_config = None

class SystemHealthMonitor:
    """Comprehensive system health monitoring."""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.checks_performed = 0
        self.last_check_time = None
        self.health_history: List[Dict] = []
        
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk usage
            disk = psutil.disk_usage('/')
            
            # Process info
            process = psutil.Process()
            process_memory = process.memory_info()
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "status": "healthy" if cpu_percent < 80 else "warning" if cpu_percent < 95 else "critical"
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "percent_used": memory.percent,
                    "status": "healthy" if memory.percent < 80 else "warning" if memory.percent < 95 else "critical"
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent_used": round((disk.used / disk.total) * 100, 1),
                    "status": "healthy" if disk.percent < 85 else "warning" if disk.percent < 95 else "critical"
                },
                "process": {
                    "memory_mb": round(process_memory.rss / (1024**2), 2),
                    "cpu_percent": process.cpu_percent(),
                    "threads": process.num_threads()
                }
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Check dependency health."""
        if DependencyManager is None:
            return {"status": "unavailable", "message": "DependencyManager not available"}
        
        try:
            dep_manager = DependencyManager()
            healthy, results = dep_manager.validate_and_repair(auto_install=False)
            
            # Count available modules
            core_available = sum(1 for info in results["core_modules"].values() if info["status"] == "available")
            core_total = len(results["core_modules"])
            
            optional_available = sum(1 for info in results["optional_modules"].values() if info["status"] == "available")
            optional_total = len(results["optional_modules"])
            
            local_available = sum(1 for info in results["local_modules"].values() if info["status"] == "available")
            local_total = len(results["local_modules"])
            
            return {
                "overall_healthy": healthy,
                "core_modules": {
                    "available": core_available,
                    "total": core_total,
                    "percentage": round((core_available / core_total) * 100, 1) if core_total > 0 else 0
                },
                "optional_modules": {
                    "available": optional_available,
                    "total": optional_total,
                    "percentage": round((optional_available / optional_total) * 100, 1) if optional_total > 0 else 0
                },
                "local_modules": {
                    "available": local_available,
                    "total": local_total,
                    "percentage": round((local_available / local_total) * 100, 1) if local_total > 0 else 0
                },
                "status": "healthy" if healthy else "critical"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def check_configuration(self) -> Dict[str, Any]:
        """Check configuration health."""
        if get_config is None:
            return {"status": "unavailable", "message": "Configuration system not available"}
        
        try:
            config = get_config()
            is_valid = config.validate()
            
            return {
                "valid": is_valid,
                "errors": config.validation_errors,
                "warnings": config.validation_warnings,
                "environment": config.system.environment.value,
                "order_mode": config.trading.order_mode,
                "risk_validation_enabled": config.risk.risk_validation_enabled,
                "status": "healthy" if is_valid else "warning" if config.validation_warnings else "critical"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def check_file_system(self) -> Dict[str, Any]:
        """Check file system health."""
        try:
            project_root = Path.cwd()
            
            # Check required directories
            required_dirs = [
                "ops/staged_orders",
                "ops/staged_orders/backup",
                "logs",
                "data",
                "src"
            ]
            
            directory_status = {}
            for dir_path in required_dirs:
                full_path = project_root / dir_path
                directory_status[dir_path] = {
                    "exists": full_path.exists(),
                    "writable": full_path.exists() and os.access(full_path, os.W_OK),
                    "size_mb": self._get_directory_size(full_path) if full_path.exists() else 0
                }
            
            # Check important files
            important_files = [
                ".env",
                ".env.example",
                "requirements.txt",
                "requirements-ml.txt"
            ]
            
            file_status = {}
            for file_path in important_files:
                full_path = project_root / file_path
                file_status[file_path] = {
                    "exists": full_path.exists(),
                    "readable": full_path.exists() and os.access(full_path, os.R_OK),
                    "size_kb": round(full_path.stat().st_size / 1024, 2) if full_path.exists() else 0,
                    "modified": full_path.stat().st_mtime if full_path.exists() else None
                }
            
            # Overall status
            missing_dirs = sum(1 for status in directory_status.values() if not status["exists"])
            missing_files = sum(1 for status in file_status.values() if not status["exists"])
            
            overall_status = "healthy"
            if missing_dirs > 0 or missing_files > 2:
                overall_status = "critical"
            elif missing_files > 0:
                overall_status = "warning"
            
            return {
                "directories": directory_status,
                "files": file_status,
                "missing_directories": missing_dirs,
                "missing_files": missing_files,
                "status": overall_status
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def _get_directory_size(self, path: Path) -> float:
        """Get directory size in MB."""
        try:
            total_size = 0
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return round(total_size / (1024**2), 2)
        except:
            return 0
    
    def check_network_connectivity(self) -> Dict[str, Any]:
        """Check network connectivity to key services."""
        try:
            import requests
            
            services = {
                "OpenAI": "https://api.openai.com/v1/models",
                "Anthropic": "https://api.anthropic.com/v1/messages",
                "Alpaca": "https://paper-api.alpaca.markets/v2/account",
                "Polygon": "https://api.polygon.io/v1/meta/symbols/AAPL/news"
            }
            
            connectivity = {}
            for service_name, url in services.items():
                try:
                    response = requests.head(url, timeout=5)
                    connectivity[service_name] = {
                        "reachable": True,
                        "status_code": response.status_code,
                        "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2)
                    }
                except requests.exceptions.RequestException as e:
                    connectivity[service_name] = {
                        "reachable": False,
                        "error": str(e)
                    }
            
            # Overall connectivity status
            reachable_count = sum(1 for status in connectivity.values() if status.get("reachable", False))
            total_count = len(connectivity)
            
            if reachable_count == total_count:
                overall_status = "healthy"
            elif reachable_count >= total_count // 2:
                overall_status = "warning"
            else:
                overall_status = "critical"
            
            return {
                "services": connectivity,
                "reachable_count": reachable_count,
                "total_count": total_count,
                "status": overall_status
            }
        except ImportError:
            return {"status": "unavailable", "message": "requests module not available"}
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def check_logging_health(self) -> Dict[str, Any]:
        """Check logging system health."""
        if get_all_loggers_health is None:
            return {"status": "unavailable", "message": "Logging health checker not available"}
        
        try:
            logger_health = get_all_loggers_health()
            
            total_errors = sum(logger["error_count"] for logger in logger_health.values())
            total_warnings = sum(logger["warning_count"] for logger in logger_health.values())
            
            # Check log directory
            log_dir = Path("logs")
            log_files_count = len(list(log_dir.glob("*.log"))) if log_dir.exists() else 0
            
            return {
                "loggers": logger_health,
                "total_errors": total_errors,
                "total_warnings": total_warnings,
                "log_files_count": log_files_count,
                "log_directory_exists": log_dir.exists(),
                "status": "healthy" if total_errors == 0 else "warning" if total_errors < 10 else "critical"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def perform_comprehensive_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        self.checks_performed += 1
        self.last_check_time = datetime.now()
        
        health_data = {
            "timestamp": self.last_check_time.isoformat(),
            "uptime_seconds": (self.last_check_time - self.start_time).total_seconds(),
            "checks_performed": self.checks_performed,
            "system_resources": self.check_system_resources(),
            "dependencies": self.check_dependencies(),
            "configuration": self.check_configuration(),
            "file_system": self.check_file_system(),
            "network": self.check_network_connectivity(),
            "logging": self.check_logging_health()
        }
        
        # Calculate overall health
        health_data["overall_status"] = self._calculate_overall_status(health_data)
        
        # Store in history (keep last 100 checks)
        self.health_history.append(health_data)
        if len(self.health_history) > 100:
            self.health_history.pop(0)
        
        return health_data
    
    def _calculate_overall_status(self, health_data: Dict[str, Any]) -> str:
        """Calculate overall system health status."""
        statuses = []
        
        for check_name, check_data in health_data.items():
            if isinstance(check_data, dict) and "status" in check_data:
                statuses.append(check_data["status"])
        
        # Priority: critical > warning > error > healthy
        if "critical" in statuses:
            return "critical"
        elif "error" in statuses:
            return "error"
        elif "warning" in statuses:
            return "warning"
        else:
            return "healthy"
    
    def generate_health_report(self, health_data: Optional[Dict] = None) -> str:
        """Generate human-readable health report."""
        if health_data is None:
            health_data = self.perform_comprehensive_check()
        
        report = []
        report.append("EMO OPTIONS BOT - SYSTEM HEALTH REPORT")
        report.append("=" * 60)
        report.append(f"Timestamp: {health_data['timestamp']}")
        report.append(f"Uptime: {health_data['uptime_seconds']:.1f} seconds")
        report.append(f"Overall Status: {health_data['overall_status'].upper()}")
        report.append("")
        
        # System Resources
        resources = health_data["system_resources"]
        if "error" not in resources:
            report.append("🖥️ SYSTEM RESOURCES")
            report.append(f"   CPU: {resources['cpu']['percent']:.1f}% ({resources['cpu']['status']})")
            report.append(f"   Memory: {resources['memory']['percent_used']:.1f}% used ({resources['memory']['status']})")
            report.append(f"   Disk: {resources['disk']['percent_used']:.1f}% used ({resources['disk']['status']})")
            report.append(f"   Process Memory: {resources['process']['memory_mb']:.1f} MB")
        else:
            report.append("🖥️ SYSTEM RESOURCES: ERROR")
        
        # Dependencies
        deps = health_data["dependencies"]
        if "error" not in deps:
            report.append("")
            report.append("📦 DEPENDENCIES")
            report.append(f"   Core Modules: {deps['core_modules']['available']}/{deps['core_modules']['total']} ({deps['core_modules']['percentage']:.1f}%)")
            report.append(f"   Optional Modules: {deps['optional_modules']['available']}/{deps['optional_modules']['total']} ({deps['optional_modules']['percentage']:.1f}%)")
            report.append(f"   Local Modules: {deps['local_modules']['available']}/{deps['local_modules']['total']} ({deps['local_modules']['percentage']:.1f}%)")
        else:
            report.append("")
            report.append("📦 DEPENDENCIES: ERROR")
        
        # Configuration
        config = health_data["configuration"]
        if "error" not in config:
            report.append("")
            report.append("⚙️ CONFIGURATION")
            report.append(f"   Valid: {config['valid']}")
            report.append(f"   Environment: {config['environment']}")
            report.append(f"   Order Mode: {config['order_mode']}")
            if config['errors']:
                report.append(f"   Errors: {len(config['errors'])}")
            if config['warnings']:
                report.append(f"   Warnings: {len(config['warnings'])}")
        else:
            report.append("")
            report.append("⚙️ CONFIGURATION: ERROR")
        
        # Network
        network = health_data["network"]
        if "error" not in network:
            report.append("")
            report.append("🌐 NETWORK CONNECTIVITY")
            report.append(f"   Services Reachable: {network['reachable_count']}/{network['total_count']}")
            for service, status in network["services"].items():
                if status.get("reachable"):
                    report.append(f"   {service}: ✅ ({status.get('response_time_ms', 0):.0f}ms)")
                else:
                    report.append(f"   {service}: ❌")
        else:
            report.append("")
            report.append("🌐 NETWORK CONNECTIVITY: ERROR")
        
        # File System
        fs = health_data["file_system"]
        if "error" not in fs:
            report.append("")
            report.append("📁 FILE SYSTEM")
            report.append(f"   Missing Directories: {fs['missing_directories']}")
            report.append(f"   Missing Files: {fs['missing_files']}")
        else:
            report.append("")
            report.append("📁 FILE SYSTEM: ERROR")
        
        # Logging
        logging_status = health_data["logging"]
        if "error" not in logging_status:
            report.append("")
            report.append("📝 LOGGING")
            report.append(f"   Total Errors: {logging_status['total_errors']}")
            report.append(f"   Total Warnings: {logging_status['total_warnings']}")
            report.append(f"   Log Files: {logging_status['log_files_count']}")
        else:
            report.append("")
            report.append("📝 LOGGING: ERROR")
        
        return "\n".join(report)
    
    def save_health_report(self, file_path: Optional[Path] = None) -> Path:
        """Save health report to file."""
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = Path(f"logs/health_report_{timestamp}.json")
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        health_data = self.perform_comprehensive_check()
        
        with open(file_path, 'w') as f:
            json.dump(health_data, f, indent=2, default=str)
        
        return file_path

def main():
    """CLI interface for health monitoring."""
    import argparse
    
    parser = argparse.ArgumentParser(description="EMO Options Bot System Health Monitor")
    parser.add_argument("--report", action="store_true", help="Generate detailed health report")
    parser.add_argument("--save", type=str, help="Save report to file")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--watch", type=int, help="Continuous monitoring with interval in seconds")
    
    args = parser.parse_args()
    
    monitor = SystemHealthMonitor()
    
    if args.watch:
        print(f"Starting continuous monitoring (interval: {args.watch}s)...")
        print("Press Ctrl+C to stop")
        try:
            while True:
                health_data = monitor.perform_comprehensive_check()
                print(f"\n[{health_data['timestamp']}] Overall Status: {health_data['overall_status'].upper()}")
                time.sleep(args.watch)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
    else:
        health_data = monitor.perform_comprehensive_check()
        
        if args.json:
            print(json.dumps(health_data, indent=2, default=str))
        else:
            print(monitor.generate_health_report(health_data))
        
        if args.save:
            file_path = Path(args.save)
            monitor.save_health_report(file_path)
            print(f"\nHealth report saved to: {file_path}")

if __name__ == "__main__":
    main()