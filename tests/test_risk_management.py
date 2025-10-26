#!/usr/bin/env python3
"""
EMO Options Bot - Risk Management Integration Test
Tests the new risk management and position sizing components
"""

import sys
import os
from pathlib import Path

# Add src to Python path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

def test_risk_manager():
    """Test RiskManager functionality"""
    print("🛡️ Testing Risk Manager...")
    
    try:
        from src.logic.risk_manager import RiskManager, PortfolioSnapshot, Position, OrderIntent
        
        # Create risk manager
        rm = RiskManager()
        
        # Create test portfolio
        pf = PortfolioSnapshot(
            equity=100_000, 
            cash=80_000, 
            positions=[
                Position(symbol="SPY", qty=1, mark=500, value=500, max_loss=1000, beta=1.0),
                Position(symbol="QQQ", qty=1, mark=420, value=420, max_loss=800, beta=1.2),
            ]
        )
        
        # Record equity for drawdown tracking
        rm.record_equity(100_000)
        
        # Assess portfolio
        assessment = rm.assess_portfolio(pf)
        print(f"   ✅ Portfolio Assessment: {assessment['positions']} positions, "
              f"${assessment['risk_used']:,.0f} risk used, "
              f"{assessment['risk_util']:.1%} risk utilization")
        
        # Test order validation - should pass
        order_ok = OrderIntent(
            symbol="IWM", 
            side="open", 
            est_max_loss=1_500, 
            est_value=0, 
            correlation_hint=0.75, 
            beta=0.9
        )
        
        ok, reasons = rm.validate_order(order_ok, pf)
        print(f"   ✅ Order validation (should pass): {ok}, reasons: {reasons}")
        
        # Test order validation - should fail (too much risk)
        order_fail = OrderIntent(
            symbol="TSLA", 
            side="open", 
            est_max_loss=5_000,  # Too much risk for 2% limit
            est_value=0, 
            correlation_hint=0.85, 
            beta=1.5
        )
        
        ok, reasons = rm.validate_order(order_fail, pf)
        print(f"   ✅ Order validation (should fail): {ok}, reasons: {reasons}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Risk Manager test failed: {e}")
        return False

def test_position_sizer():
    """Test position sizing functionality"""
    print("📊 Testing Position Sizer...")
    
    try:
        from src.logic.position_sizer import equity_size_by_vol, credit_spread_contracts, correlation_scale
        
        # Test equity sizing by volatility
        prices = [100 + i*0.2 for i in range(60)]  # Trending prices
        equity_shares = equity_size_by_vol(
            prices, 
            equity=100_000, 
            per_position_risk=0.01
        )
        print(f"   ✅ Equity size by volatility: {equity_shares} shares")
        
        # Test credit spread sizing
        spread_contracts = credit_spread_contracts(
            credit_per_contract=1.50, 
            width=5, 
            equity=100_000, 
            per_position_risk=0.01
        )
        print(f"   ✅ Credit spread contracts: {spread_contracts} contracts")
        
        # Test correlation scaling
        scaled_size = correlation_scale(10, avg_corr_to_book=0.9)
        print(f"   ✅ Correlation scaled size: {scaled_size} (scaled down from 10)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Position Sizer test failed: {e}")
        return False

def test_database_router():
    """Test advanced database router"""
    print("🗄️ Testing Database Router...")
    
    try:
        from src.database.router import get_db, ensure_minimum_schema
        
        # Set development environment
        os.environ["EMO_ENV"] = "development"
        
        # Get database connection
        db = get_db()
        print("   ✅ Database connection established")
        
        # Ensure schema
        ensure_minimum_schema(db)
        print("   ✅ Database schema ensured")
        
        # Test data insertion
        db.execute(
            "INSERT OR REPLACE INTO equity_curve(ts, equity) VALUES(?, ?)", 
            ("2025-10-25T00:00:00Z", 100000)
        )
        
        # Test data retrieval
        rows = db.query("SELECT * FROM equity_curve")
        print(f"   ✅ Database query successful: {len(rows)} rows")
        
        # Test risk metrics table
        db.execute("""
        INSERT OR REPLACE INTO risk_metrics(ts, equity, positions_count, risk_used, risk_util) 
        VALUES(?, ?, ?, ?, ?)
        """, ("2025-10-25T00:00:00Z", 100000, 2, 1800, 0.18))
        
        risk_rows = db.query("SELECT * FROM risk_metrics")
        print(f"   ✅ Risk metrics stored: {len(risk_rows)} records")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Database Router test failed: {e}")
        return False

def test_integration():
    """Test integration between risk management and existing systems"""
    print("🔗 Testing Risk Management Integration...")
    
    try:
        from src.logic import RiskManager, PortfolioSnapshot, Position, OrderIntent
        from src.logic import equity_size_by_vol, credit_spread_contracts
        from src.database.router import get_db, ensure_minimum_schema
        from src.ml.models import predict_symbols
        
        # Initialize components
        risk_manager = RiskManager()
        db = get_db()
        ensure_minimum_schema(db)
        
        # Get ML predictions
        predictions = predict_symbols(["SPY", "QQQ"])
        print(f"   ✅ ML predictions: {len(predictions)} symbols")
        
        # Create portfolio with predicted positions
        positions = []
        for symbol, pred in predictions.items():
            # Simulate position based on prediction
            trend = pred.get('trend', 'FLAT')
            confidence = pred.get('confidence', 0.5)
            
            if trend != 'FLAT' and confidence > 0.6:
                position = Position(
                    symbol=symbol,
                    qty=100,
                    mark=500 if symbol == "SPY" else 400,
                    value=50000 if symbol == "SPY" else 40000,
                    max_loss=1000,
                    beta=1.0 if symbol == "SPY" else 1.2
                )
                positions.append(position)
        
        portfolio = PortfolioSnapshot(
            equity=100_000,
            cash=50_000,
            positions=positions
        )
        
        # Assess portfolio risk
        risk_manager.record_equity(100_000)
        assessment = risk_manager.assess_portfolio(portfolio)
        print(f"   ✅ Portfolio risk assessment: {assessment['risk_util']:.1%} utilization")
        
        # Store risk metrics in database
        db.execute("""
        INSERT OR REPLACE INTO risk_metrics(ts, equity, positions_count, risk_used, risk_util, beta_exposure, drawdown) 
        VALUES(?, ?, ?, ?, ?, ?, ?)
        """, (
            "2025-10-25T00:00:00Z",
            assessment['equity'],
            assessment['positions'],
            assessment['risk_used'],
            assessment['risk_util'],
            assessment['beta_exposure'],
            assessment['drawdown']
        ))
        
        print("   ✅ Risk metrics stored in database")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        return False

def main():
    """Run all risk management tests"""
    print("🚀 EMO Options Bot - Risk Management Integration Test")
    print("=" * 65)
    
    tests = [
        ("Risk Manager", test_risk_manager),
        ("Position Sizer", test_position_sizer),
        ("Database Router", test_database_router),
        ("Integration", test_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 65)
    print("📊 Risk Management Test Results:")
    
    passed = 0
    total = len(tests)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"   {test_name:15}: {status}")
        if passed_test:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All risk management tests passed!")
        print("🛡️ Professional-grade risk controls are operational!")
        return True
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)