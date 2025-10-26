#!/usr/bin/env python3
"""
Robust Dependency Manager
Ensures all required modules are available with proper fallbacks
"""

import sys
import importlib
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DependencyManager:
    """Manages dependencies with automatic installation and validation."""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).parent.parent
        self.src_path = self.project_root / "src"
        self.requirements_files = [
            self.project_root / "requirements.txt",
            self.project_root / "requirements-ml.txt",
            self.project_root / "requirements-dev.txt"
        ]
        
        # Ensure src is in path
        if str(self.src_path) not in sys.path:
            sys.path.insert(0, str(self.src_path))
    
    def check_module_health(self) -> Dict[str, Dict]:
        """Comprehensive module health check."""
        results = {
            "core_modules": {},
            "optional_modules": {},
            "local_modules": {},
            "missing_requirements": []
        }
        
        # Core modules (required for basic functionality)
        core_modules = {
            "json": "Built-in JSON support",
            "pathlib": "Path handling",
            "datetime": "Date/time operations",
            "argparse": "Command line parsing",
            "typing": "Type hints"
        }
        
        # Optional modules (degrade gracefully)
        optional_modules = {
            "openai": "OpenAI API client",
            "anthropic": "Anthropic API client", 
            "alpaca_trade_api": "Alpaca trading API",
            "polygon": "Polygon market data API",
            "yfinance": "Yahoo Finance data",
            "requests": "HTTP requests",
            "numpy": "Numerical computing",
            "pandas": "Data analysis"
        }
        
        # Local modules (our own code)
        local_modules = {
            "ai.json_orchestrator": "AI orchestration",
            "risk.math": "Risk calculations",
            "staging.writer": "Trade staging",
            "options.chain_providers": "Options data",
            "strategies.signals": "Strategy signals"
        }
        
        # Check core modules
        for module, desc in core_modules.items():
            results["core_modules"][module] = self._check_module(module, desc, critical=True)
        
        # Check optional modules
        for module, desc in optional_modules.items():
            results["optional_modules"][module] = self._check_module(module, desc, critical=False)
        
        # Check local modules
        for module, desc in local_modules.items():
            results["local_modules"][module] = self._check_module(module, desc, critical=False)
        
        return results
    
    def _check_module(self, module_name: str, description: str, critical: bool = False) -> Dict:
        """Check if a module is available and working."""
        try:
            mod = importlib.import_module(module_name)
            return {
                "status": "available",
                "description": description,
                "version": getattr(mod, "__version__", "unknown"),
                "critical": critical,
                "path": getattr(mod, "__file__", "built-in")
            }
        except ImportError as e:
            return {
                "status": "missing",
                "description": description,
                "error": str(e),
                "critical": critical,
                "install_name": self._get_install_name(module_name)
            }
        except Exception as e:
            return {
                "status": "error",
                "description": description,
                "error": str(e),
                "critical": critical
            }
    
    def _get_install_name(self, module_name: str) -> str:
        """Get pip install name for module."""
        mapping = {
            "alpaca_trade_api": "alpaca-trade-api",
            "yfinance": "yfinance",
            "openai": "openai",
            "anthropic": "anthropic",
            "polygon": "polygon-api-client"
        }
        return mapping.get(module_name, module_name)
    
    def auto_install_missing(self, results: Dict) -> bool:
        """Attempt to install missing optional dependencies."""
        missing_optional = []
        
        for module, info in results["optional_modules"].items():
            if info["status"] == "missing" and "install_name" in info:
                missing_optional.append(info["install_name"])
        
        if not missing_optional:
            logger.info("No missing optional dependencies to install")
            return True
        
        logger.info(f"Attempting to install: {', '.join(missing_optional)}")
        
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "--upgrade"
            ] + missing_optional)
            logger.info("Successfully installed missing dependencies")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
    
    def generate_health_report(self, results: Dict) -> str:
        """Generate human-readable health report."""
        report = []
        report.append("=" * 60)
        report.append("EMO OPTIONS BOT - DEPENDENCY HEALTH REPORT")
        report.append("=" * 60)
        
        # Core modules
        report.append("\n🔧 CORE MODULES (Required)")
        report.append("-" * 30)
        for module, info in results["core_modules"].items():
            status = "✅" if info["status"] == "available" else "❌"
            report.append(f"{status} {module:<20} {info['description']}")
            if info["status"] != "available":
                report.append(f"   Error: {info['error']}")
        
        # Optional modules
        report.append("\n🔌 OPTIONAL MODULES (Graceful Degradation)")
        report.append("-" * 45)
        for module, info in results["optional_modules"].items():
            if info["status"] == "available":
                status = "✅"
                version = f"v{info['version']}"
            elif info["status"] == "missing":
                status = "⚠️"
                version = "not installed"
            else:
                status = "❌"
                version = "error"
            
            report.append(f"{status} {module:<20} {version:<15} {info['description']}")
        
        # Local modules
        report.append("\n🏠 LOCAL MODULES (Project Code)")
        report.append("-" * 35)
        for module, info in results["local_modules"].items():
            status = "✅" if info["status"] == "available" else "⚠️"
            report.append(f"{status} {module:<25} {info['description']}")
            if info["status"] != "available":
                report.append(f"   Issue: {info['error']}")
        
        # Summary
        total_core = len(results["core_modules"])
        available_core = sum(1 for info in results["core_modules"].values() if info["status"] == "available")
        
        total_optional = len(results["optional_modules"])
        available_optional = sum(1 for info in results["optional_modules"].values() if info["status"] == "available")
        
        total_local = len(results["local_modules"])
        available_local = sum(1 for info in results["local_modules"].values() if info["status"] == "available")
        
        report.append("\n📊 SUMMARY")
        report.append("-" * 20)
        report.append(f"Core Modules:     {available_core}/{total_core} available")
        report.append(f"Optional Modules: {available_optional}/{total_optional} available") 
        report.append(f"Local Modules:    {available_local}/{total_local} available")
        
        if available_core == total_core:
            report.append("\n🎯 SYSTEM STATUS: HEALTHY")
            if available_optional < total_optional:
                report.append("⚠️  Some optional features may use fallback implementations")
        else:
            report.append("\n🚨 SYSTEM STATUS: CRITICAL ISSUES")
            report.append("❌ Missing core dependencies - system may not function properly")
        
        return "\n".join(report)
    
    def validate_and_repair(self, auto_install: bool = False) -> Tuple[bool, Dict]:
        """Complete validation and optional repair."""
        logger.info("Starting dependency health check...")
        
        results = self.check_module_health()
        
        # Check if core modules are healthy
        core_healthy = all(
            info["status"] == "available" 
            for info in results["core_modules"].values()
        )
        
        if not core_healthy:
            logger.error("Critical core modules missing!")
            return False, results
        
        # Auto-install missing optional modules if requested
        if auto_install:
            self.auto_install_missing(results)
            # Re-check after installation
            results = self.check_module_health()
        
        return True, results

def main():
    """CLI interface for dependency management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="EMO Options Bot Dependency Manager")
    parser.add_argument("--auto-install", action="store_true", help="Auto-install missing optional dependencies")
    parser.add_argument("--report", action="store_true", help="Generate detailed health report")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    
    args = parser.parse_args()
    
    dep_manager = DependencyManager()
    healthy, results = dep_manager.validate_and_repair(auto_install=args.auto_install)
    
    if not args.quiet or args.report:
        print(dep_manager.generate_health_report(results))
    
    if not healthy:
        print("\n❌ System has critical issues that need to be resolved")
        sys.exit(1)
    else:
        print("\n✅ System is healthy and ready to run")
        sys.exit(0)

if __name__ == "__main__":
    main()