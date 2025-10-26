#!/usr/bin/env python3
"""
EMO Options Bot - Reorganization Integration Test
Tests that all reorganized components work together properly
"""

import sys
import os
from pathlib import Path

# Add src to Python path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

def test_imports():
    """Test that all new imports work correctly"""
    print("🧪 Testing reorganized imports...")
    
    try:
        # Test database imports
        from src.database import DB, collect_live_data
        from src.database.models import DB as DBModel
        from src.database.data_collector import collect_live_data as collector
        print("   ✅ Database imports successful")
        
        # Test ML imports
        from src.ml import add_core_features, build_supervised, generate_ml_outlook, predict_symbols
        from src.ml.features import add_core_features, build_supervised, sliding_windows
        from src.ml.models import predict_symbols, predict_single_symbol, health_check
        from src.ml.outlook import generate_ml_outlook, save_ml_outlook, load_ml_outlook
        print("   ✅ ML imports successful")
        
        # Test web imports
        from src.web import DashboardHandler, start_dashboard
        print("   ✅ Web imports successful")
        
        # Test utils imports
        from src.utils import get_config, load_environment
        from src.utils.config import get_symbols, get_project_info
        print("   ✅ Utils imports successful")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False

def test_database_functionality():
    """Test database functionality with new structure"""
    print("🗄️ Testing database functionality...")
    
    try:
        from src.database.models import DB
        
        # Test bars database
        db_bars = DB(db_type="bars").connect()
        print("   ✅ Bars database connection successful")
        
        # Test analysis database
        db_analysis = DB(db_type="analysis").connect()
        print("   ✅ Analysis database connection successful")
        
        # Test data insertion
        test_bars = [{
            "symbol": "TEST",
            "ts": "2025-10-25T15:30:00Z",
            "open": 100.0,
            "high": 101.0,
            "low": 99.0,
            "close": 100.5,
            "volume": 1000
        }]
        
        n = db_bars.upsert_bars(test_bars)
        print(f"   ✅ Inserted {n} test bars")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        return False

def test_ml_functionality():
    """Test ML functionality with new structure"""
    print("🧠 Testing ML functionality...")
    
    try:
        from src.ml.models import predict_symbols, health_check
        from src.ml.outlook import generate_ml_outlook
        
        # Test ML predictions
        predictions = predict_symbols(["SPY", "QQQ"])
        print(f"   ✅ ML predictions generated for {len(predictions)} symbols")
        
        # Test health check
        health = health_check()
        print(f"   ✅ ML health check: {health['status']}")
        
        # Test ML outlook generation
        outlook = generate_ml_outlook(["SPY"])
        print(f"   ✅ ML outlook generated with {len(outlook['symbols'])} symbols")
        
        return True
        
    except Exception as e:
        print(f"   ❌ ML test failed: {e}")
        return False

def test_configuration():
    """Test configuration management"""
    print("⚙️ Testing configuration...")
    
    try:
        from src.utils.config import get_config, get_symbols, get_project_info, ensure_data_directories
        
        # Test config retrieval
        symbols = get_symbols()
        print(f"   ✅ Retrieved {len(symbols)} symbols: {symbols}")
        
        # Test project info
        info = get_project_info()
        print(f"   ✅ Project info: {info['name']} v{info['version']}")
        
        # Test directory creation
        ensure_data_directories()
        print("   ✅ Data directories ensured")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False

def test_file_structure():
    """Test that all files are in their expected locations"""
    print("📁 Testing file structure...")
    
    expected_files = [
        "src/__init__.py",
        "src/database/__init__.py",
        "src/database/models.py",
        "src/database/data_collector.py",
        "src/ml/__init__.py",
        "src/ml/features.py",
        "src/ml/models.py",
        "src/ml/outlook.py",
        "src/web/__init__.py",
        "src/web/dashboard.py",
        "src/utils/__init__.py",
        "src/utils/config.py",
        "scripts/retrain_weekly.py",
        "scripts/setup_weekly_task.ps1",
        "tests/test_database.py",
        "tests/test_dashboard.py",
        "tests/test_integration.py",
        "main.py",
        "dashboard.py"
    ]
    
    missing_files = []
    for file_path in expected_files:
        full_path = ROOT / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"   ❌ Missing files: {missing_files}")
        return False
    else:
        print(f"   ✅ All {len(expected_files)} expected files found")
        return True

def main():
    """Run all reorganization tests"""
    print("🚀 EMO Options Bot - Reorganization Integration Test")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Database", test_database_functionality),
        ("ML Functions", test_ml_functionality)
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
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    passed = 0
    total = len(tests)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"   {test_name:15}: {status}")
        if passed_test:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Reorganization successful!")
        return True
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)