#!/usr/bin/env python
import shlex
"""
Patch #8 Validation Script
Comprehensive validation of Phase 3 LLM stack: schemas, orchestrator, synthesizer, gates, and CLI.
"""

import os
import sys
import subprocess
from pathlib import Path
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
        result = subprocess.run(shlex.split(command), capture_output=True, text=True)
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

def validate_phase3_modules():
    """Validate Phase 3 module structure and imports."""
    print_status("Testing Phase 3 module structure...", "info")
    
    # Check core module files exist
    base_path = Path("src/phase3")
    modules = ["__init__.py", "schemas.py", "orchestrator.py", "synthesizer.py", "gates.py"]
    
    success = True
    for module in modules:
        if not check_file_exists(base_path / module, f"Module {module}"):
            success = False
    
    # Test imports
    if success:
        success &= run_command(
            'python -c "from src.phase3.schemas import AnalysisRequest, TradePlan, RiskConstraints, TradeLeg; print(\'Schema imports OK\')"',
            "Schema module imports"
        )
        
        success &= run_command(
            'python -c "from src.phase3.orchestrator import LLMOrchestrator, MockLLM; print(\'Orchestrator imports OK\')"',
            "Orchestrator module imports"
        )
        
        success &= run_command(
            'python -c "from src.phase3.synthesizer import TradeSynthesizer; print(\'Synthesizer imports OK\')"',
            "Synthesizer module imports"
        )
        
        success &= run_command(
            'python -c "from src.phase3.gates import RiskGate; print(\'Gates imports OK\')"',
            "Gates module imports"
        )
    
    return success

def validate_llm_orchestrator():
    """Validate LLM orchestrator functionality."""
    print_status("Testing LLM orchestrator...", "info")
    
    # Test MockLLM functionality
    success = run_command(
        'python -c "from src.phase3.schemas import AnalysisRequest; from src.phase3.orchestrator import LLMOrchestrator; orch = LLMOrchestrator(); req = AnalysisRequest(user_text=\'sideways market\'); view = orch.analyze(req); print(f\'View: {view[\\\"view\\\"]}, Confidence: {view[\\\"confidence\\\"]}\')"',
        "MockLLM analysis functionality"
    )
    
    # Test different market views
    if success:
        views_to_test = [
            ("sideways market", "neutral"),
            ("very volatile conditions", "high_vol"),
            ("bullish outlook", "bullish"),
            ("bearish sentiment", "bearish")
        ]
        
        for text, expected_view in views_to_test:
            success &= run_command(
                f'python -c "from src.phase3.schemas import AnalysisRequest; from src.phase3.orchestrator import LLMOrchestrator; orch = LLMOrchestrator(); req = AnalysisRequest(user_text=\'{text}\'); view = orch.analyze(req); assert view[\'view\'] == \'{expected_view}\', f\'Expected {expected_view}, got {{view[\\\"view\\\"]}}\'; print(f\'{text} -> {expected_view}\')"',
                f"View classification: {text} -> {expected_view}"
            )
    
    return success

def validate_trade_synthesizer():
    """Validate trade synthesizer functionality."""
    print_status("Testing trade synthesizer...", "info")
    
    # Test basic synthesis
    success = run_command(
        'python -c "from src.phase3.synthesizer import TradeSynthesizer; from src.phase3.schemas import RiskConstraints; synth = TradeSynthesizer(); plan = synth.synthesize(\'SPY\', {\'view\': \'neutral\'}, RiskConstraints()); print(f\'Strategy: {plan.strategy_type}, Legs: {len(plan.legs)}, Max Loss: {plan.max_loss}\')"',
        "Basic trade synthesis"
    )
    
    # Test different strategy types
    if success:
        strategies = [
            ("neutral", "iron_condor", 4),
            ("high_vol", "iron_condor", 4),
            ("bullish", "put_credit_spread", 2),
            ("bearish", "call_credit_spread", 2)
        ]
        
        for view, expected_strategy, expected_legs in strategies:
            success &= run_command(
                f'python -c "from src.phase3.synthesizer import TradeSynthesizer; synth = TradeSynthesizer(); plan = synth.synthesize(\'SPY\', {{\'view\': \'{view}\'}}, None); assert plan.strategy_type == \'{expected_strategy}\', f\'Expected {expected_strategy}, got {{plan.strategy_type}}\'; assert len(plan.legs) == {expected_legs}, f\'Expected {expected_legs} legs, got {{len(plan.legs)}}\'; print(f\'{view} -> {expected_strategy} ({expected_legs} legs)\')"',
                f"Strategy synthesis: {view} -> {expected_strategy}"
            )
    
    return success

def validate_risk_gates():
    """Validate risk gate functionality."""
    print_status("Testing risk gates...", "info")
    
    # Test risk validation with acceptable trade
    success = run_command(
        'python -c "from src.phase3.gates import RiskGate; from src.phase3.schemas import TradePlan, TradeLeg, RiskConstraints; gate = RiskGate(); plan = TradePlan(strategy_type=\'iron_condor\', symbol=\'SPY\', legs=[TradeLeg(\'sell\', \'put\', 100, 1)], max_loss=500.0); portfolio = {\'account_equity\': 100000.0, \'portfolio_risk_used\': 0.01}; result = gate.validate_trade(plan, portfolio); print(f\'Trade OK: {result.ok}, Violations: {len(result.violations)}\')"',
        "Risk validation - acceptable trade"
    )
    
    # Test risk violations
    if success:
        success &= run_command(
            'python -c "from src.phase3.gates import RiskGate; from src.phase3.schemas import TradePlan, TradeLeg, RiskConstraints; gate = RiskGate(); constraints = RiskConstraints(max_risk_per_trade=0.001); plan = TradePlan(strategy_type=\'iron_condor\', symbol=\'SPY\', legs=[TradeLeg(\'sell\', \'put\', 100, 1)], max_loss=500.0, constraints=constraints); portfolio = {\'account_equity\': 100000.0, \'portfolio_risk_used\': 0.01}; result = gate.validate_trade(plan, portfolio); assert not result.ok, \'Expected violations\'; print(f\'Violations detected: {len(result.violations)}\')"',
            "Risk validation - violation detection"
        )
    
    return success

def validate_stage_order_cli():
    """Validate stage order CLI functionality."""
    print_status("Testing stage order CLI...", "info")
    
    # Check CLI file exists
    success = check_file_exists(Path("scripts/stage_order_cli.py"), "Stage order CLI script")
    
    if success:
        # Test CLI execution with different scenarios
        test_cases = [
            ("SPY looks sideways", "SPY", "neutral view"),
            ("market is volatile", "QQQ", "volatile view"),
            ("bullish on tech", "TSLA", "bullish view"),
            ("bearish sentiment", "AAPL", "bearish view")
        ]
        
        for text, symbol, description in test_cases:
            success &= run_command(
                f'python scripts/stage_order_cli.py --text "{text}" --symbol {symbol}',
                f"CLI staging: {description}"
            )
    
    # Check if staged orders directory was created
    if success:
        staged_dir = Path("data/staged_orders")
        if staged_dir.exists():
            staged_files = list(staged_dir.glob("*.json"))
            print_status(f"Staged orders directory contains {len(staged_files)} files", "success")
        else:
            print_status("Staged orders directory not created", "error")
            success = False
    
    return success

def validate_integration_tests():
    """Validate integration test functionality."""
    print_status("Testing Phase 3 integration tests...", "info")
    
    # Run smoke tests
    success = run_command(
        "python -m pytest tests/test_phase3_smoke.py -v",
        "Phase 3 smoke tests"
    )
    
    # Run schema contract tests
    if success:
        success &= run_command(
            "python -m pytest tests/test_phase3_schema_contract.py -v",
            "Phase 3 schema contract tests"
        )
    
    return success

def validate_end_to_end_pipeline():
    """Validate complete end-to-end pipeline."""
    print_status("Testing end-to-end pipeline...", "info")
    
    # Test complete pipeline programmatically
    success = run_command(
        'python -c "from src.phase3.schemas import AnalysisRequest, RiskConstraints; from src.phase3.orchestrator import LLMOrchestrator; from src.phase3.synthesizer import TradeSynthesizer; from src.phase3.gates import RiskGate; req = AnalysisRequest(user_text=\'market looks neutral\'); llm = LLMOrchestrator(); view = llm.analyze(req); synth = TradeSynthesizer(); plan = synth.synthesize(\'SPY\', view, RiskConstraints()); gate = RiskGate(); portfolio = {\'account_equity\': 100000.0, \'portfolio_risk_used\': 0.05, \'option_liquidity\': lambda s,st,e,i: {\'oi\': 500}}; result = gate.validate_trade(plan, portfolio); print(f\'Pipeline: {req.user_text} -> {view[\\\"view\\\"]} -> {plan.strategy_type} -> Valid: {result.ok}\')"',
        "Complete pipeline integration"
    )
    
    return success

def main():
    """Run comprehensive Patch #8 validation."""
    print(f"{BLUE}{'='*60}")
    print(f"Patch #8 Validation - Phase 3 LLM Stack Complete")
    print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}{RESET}")
    
    tests = [
        ("Phase 3 Module Structure", validate_phase3_modules),
        ("LLM Orchestrator", validate_llm_orchestrator),
        ("Trade Synthesizer", validate_trade_synthesizer),
        ("Risk Gates", validate_risk_gates),
        ("Stage Order CLI", validate_stage_order_cli),
        ("Integration Tests", validate_integration_tests),
        ("End-to-End Pipeline", validate_end_to_end_pipeline),
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
    print("PATCH #8 VALIDATION SUMMARY")
    print(f"{'='*60}{RESET}")
    
    for test_name, success in results.items():
        status = "[PASS]" if success else "[FAIL]"
        color = GREEN if success else RED
        print(f"{color}{status:<10} {test_name}{RESET}")
    
    print(f"\n{GREEN if total_success else RED}{'='*60}")
    if total_success:
        print("PATCH #8 VALIDATION COMPLETE - ALL TESTS PASSED!")
        print("[OK] Phase 3 LLM stack operational")
        print("[OK] Natural language -> trade plan pipeline working")
        print("[OK] Risk gates enforcing constraints")
        print("[OK] CLI staging trades successfully")
        print("[OK] Integration tests passing")
        print("[OK] End-to-end pipeline functional")
        print("\nPhase 3 LLM stack ready for production!")
    else:
        print("PATCH #8 VALIDATION FAILED - SOME TESTS FAILED")
        print("Please review the failed tests above and fix issues.")
    print(f"{'='*60}{RESET}")
    
    return 0 if total_success else 1

if __name__ == "__main__":
    sys.exit(main())