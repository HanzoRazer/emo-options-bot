#!/usr/bin/env python3
"""
Simplified Integration Test for Enhanced EMO Options Bot
Tests basic functionality without requiring external data.
"""

from __future__ import annotations
import sys
from pathlib import Path

# Add src to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.logic.risk_manager import RiskManager, PortfolioSnapshot, Position, OrderIntent

def test_basic_risk_management():
    """Test basic risk management functionality."""
    print("Testing Basic Risk Management...")
    
    # Create mock portfolio
    positions = [
        Position(symbol="SPY", qty=100, mark=450.0, value=45000, max_loss=4500, beta=1.0),
        Position(symbol="QQQ", qty=50, mark=380.0, value=19000, max_loss=2850, beta=1.2),
    ]
    portfolio = PortfolioSnapshot(equity=75000, cash=11000, positions=positions)
    
    # Test risk manager
    risk_manager = RiskManager()
    assessment = risk_manager.assess_portfolio(portfolio)
    
    print(f"   Portfolio heat: {sum(p.max_loss for p in positions) / portfolio.equity * 100:.1f}%")
    print(f"   Assessment violations: {len(assessment.get('violations', []))}")
    print(f"   Assessment warnings: {len(assessment.get('warnings', []))}")
    
    # Test order validation with a smaller, valid order
    test_order = OrderIntent(symbol="AAPL", side="buy", est_max_loss=1000, est_value=8000)  # Under 2% cap
    try:
        success, violations = risk_manager.validate_order(test_order, portfolio)
        print(f"   Order validation: {'PASSED' if success else 'FAILED'} ({len(violations)} violations)")
        
        if violations:
            for v in violations:
                print(f"     - {v}")
        
        return success
    except Exception as e:
        print(f"   Order validation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_portfolio_metrics():
    """Test portfolio metric calculations."""
    print("Testing Portfolio Metrics...")
    
    # Test empty portfolio
    empty_portfolio = PortfolioSnapshot(equity=50000, cash=50000, positions=[])
    risk_manager = RiskManager()
    
    empty_assessment = risk_manager.assess_portfolio(empty_portfolio)
    print(f"   Empty portfolio assessment: PASSED (violations: {len(empty_assessment.get('violations', []))})")
    
    # Test high-risk portfolio
    high_risk_positions = [
        Position(symbol="TSLA", qty=100, mark=250.0, value=25000, max_loss=12500, beta=2.0),  # 25% max loss
        Position(symbol="NVDA", qty=50, mark=400.0, value=20000, max_loss=10000, beta=1.8),   # 20% max loss
    ]
    high_risk_portfolio = PortfolioSnapshot(equity=50000, cash=5000, positions=high_risk_positions)
    
    high_risk_assessment = risk_manager.assess_portfolio(high_risk_portfolio)
    
    # Check if risk utilization exceeds 100% (which indicates portfolio heat cap exceeded)
    risk_util = high_risk_assessment.get('risk_util', 0)
    print(f"   High-risk portfolio risk utilization: {risk_util:.1%}")
    print(f"   Risk used: {high_risk_assessment.get('risk_used', 0):,.0f} vs cap: {high_risk_assessment.get('risk_cap', 0):,.0f}")
    
    # This should show risk utilization > 100% (meaning portfolio exceeds risk cap)
    exceeds_risk_cap = risk_util > 1.0
    print(f"   Exceeds risk cap: {'YES' if exceeds_risk_cap else 'NO'}")
    
    return exceeds_risk_cap  # Should exceed risk cap

def test_order_validation():
    """Test order validation logic."""
    print("Testing Order Validation...")
    
    # Conservative portfolio
    positions = [
        Position(symbol="SPY", qty=100, mark=450.0, value=45000, max_loss=2250, beta=1.0),  # 5% max loss
    ]
    portfolio = PortfolioSnapshot(equity=50000, cash=5000, positions=positions)
    risk_manager = RiskManager()
    
    # Test valid order
    valid_order = OrderIntent(symbol="VTI", side="buy", est_max_loss=500, est_value=5000)
    valid_success, valid_violations = risk_manager.validate_order(valid_order, portfolio)
    print(f"   Valid order: {'PASSED' if valid_success else 'FAILED'} ({len(valid_violations)} violations)")
    
    # Test risky order
    risky_order = OrderIntent(symbol="TSLA", side="buy", est_max_loss=5000, est_value=15000)
    risky_success, risky_violations = risk_manager.validate_order(risky_order, portfolio)
    print(f"   Risky order: {'PROPERLY_REJECTED' if not risky_success else 'FAILED_TO_REJECT'} ({len(risky_violations)} violations)")
    
    if risky_violations:
        for v in risky_violations:
            print(f"     - {v}")
    
    return valid_success and not risky_success

def test_enhanced_components():
    """Test that enhanced components can be imported."""
    print("Testing Enhanced Component Imports...")
    
    try:
        from src.database.enhanced_data_collector import EnhancedDataCollector
        print("   Enhanced Data Collector: IMPORTED")
        
        from src.web.enhanced_dashboard import EnhancedDashboard
        print("   Enhanced Dashboard: IMPORTED")
        
        from scripts.enhanced_retrain import EnhancedMLTrainer
        print("   Enhanced ML Trainer: IMPORTED")
        
        return True
        
    except Exception as e:
        print(f"   Import error: {e}")
        return False

def test_database_creation():
    """Test database creation without external API calls."""
    print("Testing Database Creation...")
    
    try:
        from src.database.enhanced_data_collector import EnhancedDataCollector
        collector = EnhancedDataCollector()
        
        # This should create the database without any API calls
        collector._ensure_database()
        print("   Database creation: PASSED")
        
        # Test risk metrics update with empty portfolio
        collector.update_risk_metrics()
        print("   Risk metrics update: PASSED")
        
        return True
        
    except Exception as e:
        print(f"   Database creation error: {e}")
        return False

def main():
    """Run simplified integration tests."""
    print("Enhanced EMO Options Bot - Simplified Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Basic Risk Management", test_basic_risk_management),
        ("Portfolio Metrics", test_portfolio_metrics),
        ("Order Validation", test_order_validation),
        ("Enhanced Component Imports", test_enhanced_components),
        ("Database Creation", test_database_creation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n>>> {test_name}")
        try:
            if test_func():
                print(f"PASSED: {test_name}")
                passed += 1
            else:
                print(f"FAILED: {test_name}")
        except Exception as e:
            print(f"ERROR: {test_name} - {e}")
    
    print("\n" + "=" * 60)
    print(f"Simplified Integration Test Results: {passed}/{total} PASSED")
    
    if passed == total:
        print("All tests passed! The enhanced system core functionality is working.")
        return True
    else:
        print("Some tests failed. Core system issues detected.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)