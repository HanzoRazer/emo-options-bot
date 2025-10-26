#!/usr/bin/env python
"""
Patch #7 Validation Script
Comprehensive validation of Phase 3 skeleton, local env generator, and contract tests.
"""

import os
import sys
from pathlib import Path
import subprocess
from datetime import datetime

# Color coding for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_status(message: str, status: str = "info"):
    colors = {"success": GREEN, "error": RED, "warning": YELLOW, "info": BLUE}
    color = colors.get(status, RESET)
    symbols = {"success": "[OK]", "error": "[ERR]", "warning": "[WARN]", "info": "[INFO]"}
    symbol = symbols.get(status, "[INFO]")
    print(f"{color}{symbol} {message}{RESET}")

def run_command(command: str, description: str) -> bool:
    """Run a command and return success status."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print_status(f"{description}: SUCCESS", "success")
            return True
        else:
            print_status(f"{description}: FAILED", "error")
            print(f"Command: {command}")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print_status(f"{description}: EXCEPTION - {e}", "error")
        return False

def check_file_exists(file_path: Path, description: str) -> bool:
    """Check if a file exists."""
    if file_path.exists():
        print_status(f"{description}: EXISTS", "success")
        return True
    else:
        print_status(f"{description}: MISSING", "error")
        return False

def validate_skeleton_module():
    """Validate the Phase 3 skeleton module."""
    print_status("Testing Phase 3 skeleton module...", "info")
    
    # Test import
    success = run_command(
        'python -c "from src.phase3.skeleton import TradeLeg, TradePlan, example_plan, describe; print(\'Skeleton imports OK\')"',
        "Skeleton module import"
    )
    
    # Test functionality
    if success:
        success &= run_command(
            'python -c "from src.phase3.skeleton import example_plan; plan = example_plan(); print(f\'Plan: {plan.symbol} {plan.strategy} {len(plan.legs)} legs\')"',
            "Skeleton functionality"
        )
    
    return success

def validate_local_env_generator():
    """Validate the local environment generator."""
    print_status("Testing local environment generator...", "info")
    
    # Test tool execution
    success = run_command(
        "python tools/generate_local_env.py",
        "Local env generator execution"
    )
    
    # Check if file was created
    env_file = Path("local.dev.env")
    if success:
        success &= check_file_exists(env_file, "local.dev.env file creation")
        
        # Validate content
        if success and env_file.exists():
            content = env_file.read_text()
            required_vars = ["EMO_ENV", "PHASE3_MODULE_DIR", "PROJECT_ROOT", "PYTHONPATH"]
            for var in required_vars:
                if var in content:
                    print_status(f"Environment variable {var} present", "success")
                else:
                    print_status(f"Environment variable {var} missing", "error")
                    success = False
    
    return success

def validate_schema_contract_test():
    """Validate the schema contract test."""
    print_status("Testing schema contract test...", "info")
    
    success = run_command(
        "python -m pytest tests/test_phase3_schema_contract.py -v",
        "Schema contract test"
    )
    
    return success

def validate_integration():
    """Validate integration with existing Phase 3 components."""
    print_status("Testing Phase 3 integration...", "info")
    
    # Test auto-loader integration
    success = run_command(
        'python -c "from src.phase3.auto_loader import try_import_all; modules, failures = try_import_all(); print(f\'Found modules: {[n for n, m in modules.items() if m]}\')"',
        "Auto-loader integration"
    )
    
    # Test test harness with skeleton
    if success:
        success &= run_command(
            "python tools/phase3_e2e_test.py",
            "Phase 3 end-to-end test"
        )
    
    return success

def validate_documentation():
    """Validate documentation updates."""
    print_status("Checking documentation updates...", "info")
    
    dev_guide = Path("DEVELOPER_QUICK_START.md")
    success = check_file_exists(dev_guide, "DEVELOPER_QUICK_START.md")
    
    if success:
        try:
            content = dev_guide.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                content = dev_guide.read_text(encoding='latin1')
            except:
                print_status("Cannot read documentation file due to encoding issues", "warning")
                return False
                
        required_sections = [
            "Phase 3 Skeleton & Local Dev Env",
            "Local Env Setup", 
            "Schema Contract Test"
        ]
        
        for section in required_sections:
            if section in content:
                print_status(f"Documentation section '{section}' present", "success")
            else:
                print_status(f"Documentation section '{section}' missing", "error")
                success = False
    
    return success

def main():
    """Run comprehensive Patch #7 validation."""
    print(f"{BLUE}{'='*60}")
    print(f"Patch #7 Validation - Phase 3 Foundation Complete")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}{RESET}")
    
    tests = [
        ("Phase 3 Skeleton Module", validate_skeleton_module),
        ("Local Environment Generator", validate_local_env_generator),
        ("Schema Contract Test", validate_schema_contract_test),
        ("Phase 3 Integration", validate_integration),
        ("Documentation Updates", validate_documentation),
    ]
    
    results = {}
    total_success = True
    
    for test_name, test_func in tests:
        print(f"\n{YELLOW}{'='*50}")
        print(f"Testing: {test_name}")
        print(f"{'='*50}{RESET}")
        
        try:
            success = test_func()
            results[test_name] = success
            total_success &= success
        except Exception as e:
            print_status(f"{test_name} validation failed: {e}", "error")
            results[test_name] = False
            total_success = False
    
    # Summary
    print(f"\n{BLUE}{'='*60}")
    print("PATCH #7 VALIDATION SUMMARY")
    print(f"{'='*60}{RESET}")
    
    for test_name, success in results.items():
        status = "[PASS]" if success else "[FAIL]"
        color = GREEN if success else RED
        print(f"{color}{status:<10} {test_name}{RESET}")

    print(f"\n{GREEN if total_success else RED}{'='*60}")
    if total_success:
        print("PATCH #7 VALIDATION COMPLETE - ALL TESTS PASSED!")
        print("[OK] Phase 3 skeleton module operational")
        print("[OK] Local environment generator working")
        print("[OK] Schema contract tests passing")
        print("[OK] Integration with existing components successful")
        print("[OK] Documentation updated")
        print("\nReady for Phase 3 production development!")
    else:
        print("PATCH #7 VALIDATION FAILED - SOME TESTS FAILED")
        print("Please review the failed tests above and fix issues.")
    print(f"{'='*60}{RESET}")
    
    return 0 if total_success else 1

if __name__ == "__main__":
    sys.exit(main())