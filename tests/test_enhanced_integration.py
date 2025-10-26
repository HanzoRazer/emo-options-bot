#!/usr/bin/env python3
"""
Integration Test for Enhanced EMO Options Bot
Tests the integration between risk management, data collection, ML, and dashboard.
"""

from __future__ import annotations
import sys
from pathlib import Path
import json
import time

# Add src to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from src.logic.risk_manager import RiskManager, PortfolioSnapshot, Position, OrderIntent
from src.database.enhanced_data_collector import EnhancedDataCollector
from scripts.enhanced_retrain import EnhancedMLTrainer
from src.web.enhanced_dashboard import EnhancedDashboard

def test_risk_integration():
    """Test risk management integration."""
    print("Testing Risk Management Integration...")
    
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
    
    # Test order validation
    test_order = OrderIntent(symbol="AAPL", side="buy", est_max_loss=2000, est_value=10000)
    violations = risk_manager.validate_order(portfolio, test_order)
    print(f"   Order validation: {'PASSED' if not violations else 'FAILED'} ({len(violations)} violations)")
    
    return True

def test_data_collection():
    """Test enhanced data collection."""
    print("Testing Enhanced Data Collection...")
    
    collector = EnhancedDataCollector()
    
    # Test database setup
    try:
        collector._ensure_database()
        print("   Database setup: PASSED")
    except Exception as e:
        print(f"   Database setup: FAILED - {e}")
        return False
    
    # Test mock portfolio creation
    try:
        portfolio = collector.get_mock_portfolio()
        print(f"   Mock portfolio: PASSED ({len(portfolio.positions)} positions)")
    except Exception as e:
        print(f"   Mock portfolio: FAILED - {e}")
        return False
    
    # Test risk metrics update
    try:
        collector.update_risk_metrics()
        print("   Risk metrics update: PASSED")
    except Exception as e:
        print(f"   Risk metrics update: FAILED - {e}")
        return False
    
    return True

def test_ml_integration():
    """Test ML integration with risk management."""
    print("Testing ML Integration...")
    
    trainer = EnhancedMLTrainer()
    
    # Test market regime features
    try:
        regime = trainer.get_market_regime_features()
        print(f"   Market regime: PASSED ({regime.get('vix_level', 0):.1f}% VIX)")
    except Exception as e:
        print(f"   Market regime: FAILED - {e}")
        return False
    
    # Test risk context features
    try:
        risk_context = trainer.get_risk_context_features("AAPL")
        print(f"   Risk context: PASSED (can add: {risk_context.get('can_add_position', False)})")
    except Exception as e:
        print(f"   Risk context: FAILED - {e}")
        return False
    
    # Test prediction generation (without full training)
    try:
        import pandas as pd
        # Create minimal test data
        test_data = pd.DataFrame({
            'c': [100, 101, 102, 103, 104],
            'o': [99, 100, 101, 102, 103],
            'h': [101, 102, 103, 104, 105],
            'l': [98, 99, 100, 101, 102],
            'v': [1000, 1100, 1200, 1300, 1400],
            't': [1, 2, 3, 4, 5]
        })
        
        # Add required features manually for test
        test_data['returns'] = test_data['c'].pct_change()
        test_data['sma_5'] = test_data['c'].rolling(5).mean()
        test_data['sma_20'] = test_data['c'].expanding().mean()  # Use expanding for small dataset
        test_data['volatility_5'] = test_data['returns'].expanding().std()
        test_data['volatility_20'] = test_data['returns'].expanding().std()
        test_data['volatility_ratio'] = 1.0
        test_data['volume_sma'] = test_data['v'].expanding().mean()
        test_data['volume_ratio'] = test_data['v'] / test_data['volume_sma']
        test_data['price_position'] = 0.5
        test_data['momentum_5'] = 0.01
        test_data['momentum_10'] = 0.01
        test_data['rsi'] = 50.0
        test_data['trend_strength'] = 0.01
        
        test_data = test_data.fillna(0)
        
        pred = trainer.enhanced_predict("TEST", test_data)
        print(f"   Prediction generation: PASSED ({pred['direction']}, conf: {pred['confidence']:.3f})")
    except Exception as e:
        print(f"   Prediction generation: FAILED - {e}")
        return False
    
    return True

def test_dashboard_integration():
    """Test dashboard integration."""
    print("Testing Dashboard Integration...")
    
    dashboard = EnhancedDashboard()
    
    # Test portfolio snapshot
    try:
        portfolio = dashboard._get_portfolio_snapshot()
        print(f"   Portfolio snapshot: PASSED ({len(portfolio.positions)} positions)")
    except Exception as e:
        print(f"   Portfolio snapshot: FAILED - {e}")
        return False
    
    # Test risk management card generation
    try:
        risk_card = dashboard._render_risk_management_card()
        print(f"   Risk card generation: PASSED ({len(risk_card)} chars)")
    except Exception as e:
        print(f"   Risk card generation: FAILED - {e}")
        return False
    
    # Test dashboard generation (without saving)
    try:
        html = dashboard.generate_dashboard()
        print(f"   Dashboard HTML generation: PASSED ({len(html)} chars)")
    except Exception as e:
        print(f"   Dashboard HTML generation: FAILED - {e}")
        return False
    
    return True

def test_end_to_end_integration():
    """Test complete end-to-end integration."""
    print("Testing End-to-End Integration...")
    
    try:
        # 1. Data collection
        collector = EnhancedDataCollector()
        collector._ensure_database()
        
        # 2. Risk metrics
        collector.update_risk_metrics()
        
        # 3. Risk summary
        risk_summary = collector.generate_risk_summary()
        print(f"   Risk summary: PASSED (status: {risk_summary.get('status', 'unknown')})")
        
        # 4. Dashboard generation
        dashboard = EnhancedDashboard()
        dashboard_file = dashboard.build_dashboard()
        print(f"   Dashboard file: PASSED ({dashboard_file.name})")
        
        # 5. Verify outputs exist
        data_dir = ROOT / "data"
        outputs = [
            data_dir / "risk_summary.json",
            ROOT / "enhanced_dashboard.html"
        ]
        
        for output in outputs:
            if output.exists():
                print(f"   Output {output.name}: PASSED")
            else:
                print(f"   Output {output.name}: FAILED (not found)")
                return False
        
        return True
        
    except Exception as e:
        print(f"   End-to-end integration: FAILED - {e}")
        return False

def main():
    """Run all integration tests."""
    print("Enhanced EMO Options Bot - Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Risk Management Integration", test_risk_integration),
        ("Data Collection Integration", test_data_collection),
        ("ML Integration", test_ml_integration),
        ("Dashboard Integration", test_dashboard_integration),
        ("End-to-End Integration", test_end_to_end_integration),
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
    
    print("\n" + "=" * 50)
    print(f"Integration Test Results: {passed}/{total} PASSED")
    
    if passed == total:
        print("All integration tests passed! The enhanced system is working correctly.")
        return True
    else:
        print("Some integration tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)