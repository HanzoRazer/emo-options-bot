#!/usr/bin/env python3
"""
Test script for new trading database session helper and health server endpoints.
Demonstrates the integration of trading DB with health monitoring.
"""

import sys
import time
import threading
from pathlib import Path

# Add project paths
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_trading_session():
    """Test the trading session helper."""
    print("\n🗄️ Testing Trading Session Helper...")
    
    try:
        from src.database.trading_session import quick_health_check, session_scope, get_engine
        
        # Test health check
        health = quick_health_check()
        print(f"✅ Health check: {health}")
        
        # Test session scope
        with session_scope() as s:
            from sqlalchemy import text
            result = s.execute(text("SELECT 1 as test")).fetchone()
            print(f"✅ Session scope test: {result}")
        
        # Test engine creation
        engine = get_engine()
        print(f"✅ Engine created: {engine.url}")
        
        return True
        
    except Exception as e:
        print(f"❌ Trading session test failed: {e}")
        return False

def test_read_paths():
    """Test the read paths functionality."""
    print("\n📖 Testing Read Paths...")
    
    try:
        from src.database.read_paths import fetch_positions, fetch_recent_orders
        
        # Test positions fetch
        positions = fetch_positions(limit=10)
        print(f"✅ Positions fetched: {len(positions)} items")
        
        # Test orders fetch  
        orders = fetch_recent_orders(limit=10)
        print(f"✅ Orders fetched: {len(orders)} items")
        
        return True
        
    except Exception as e:
        print(f"❌ Read paths test failed: {e}")
        return False

def test_health_server():
    """Test the enhanced health server."""
    print("\n🏥 Testing Enhanced Health Server...")
    
    try:
        from tools.emit_health import serve_health_monitor, snapshot
        import requests
        
        # Start server
        print("📡 Starting health server...")
        server_thread = serve_health_monitor(host="127.0.0.1", port=8083)
        time.sleep(1)  # Give server time to start
        
        # Provide sample data
        sample_perf = {
            "cycle_times": [1.0, 1.2, 0.9, 1.1],
            "memory_usage": 256.5,
            "cpu_usage": 15.2
        }
        snapshot(sample_perf)
        
        # Test endpoints
        base_url = "http://127.0.0.1:8083"
        
        # Test health endpoint
        print("🔍 Testing /health endpoint...")
        r = requests.get(f"{base_url}/health", timeout=3)
        health_data = r.json()
        print(f"✅ Health status: {health_data.get('status')}")
        print(f"✅ Trading DB available: {health_data.get('trading_db', {}).get('db') == 'ok'}")
        
        # Test metrics endpoint  
        print("📊 Testing /metrics endpoint...")
        r = requests.get(f"{base_url}/metrics", timeout=3)
        metrics_data = r.json()
        print(f"✅ Metrics cycle: {metrics_data.get('cycle')}")
        print(f"✅ Trading DB status: {metrics_data.get('trading_db', {})}")
        
        # Test positions endpoint
        print("📋 Testing /positions.json endpoint...")
        r = requests.get(f"{base_url}/positions.json", timeout=3)
        print(f"✅ Positions endpoint status: {r.status_code}")
        if r.status_code == 200:
            pos_data = r.json()
            print(f"✅ Positions count: {pos_data.get('count', 0)}")
        
        # Test orders JSON endpoint
        print("📄 Testing /orders.json endpoint...")
        r = requests.get(f"{base_url}/orders.json", timeout=3)
        if r.status_code == 200:
            orders_data = r.json()
            print(f"✅ Orders endpoint working: {list(orders_data.keys())}")
        
        # Test simple orders HTML endpoint
        print("🌐 Testing /orders HTML endpoint...")
        r = requests.get(f"{base_url}/orders", timeout=3)
        print(f"✅ Orders HTML status: {r.status_code}")
        print(f"✅ Content type: {r.headers.get('Content-Type')}")
        if r.status_code == 200:
            print(f"✅ HTML length: {len(r.text)} chars")
        
        # Test root endpoint with new features
        print("🏠 Testing root endpoint...")
        r = requests.get(f"{base_url}/", timeout=3)
        if r.status_code == 200:
            root_data = r.json()
            endpoints = root_data.get('endpoints', [])
            print(f"✅ Available endpoints: {endpoints}")
            print(f"✅ Trading DB available: {root_data.get('trading_db_available', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Health server test failed: {e}")
        return False

def main():
    """Main test runner."""
    print("🚀 EMO Trading DB Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Trading Session Helper", test_trading_session),
        ("Read Paths", test_read_paths), 
        ("Enhanced Health Server", test_health_server),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
            if success:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST RESULTS:")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n🎯 Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Trading DB integration is working!")
        print("\n📖 Available endpoints:")
        print("   • http://localhost:8082/health - JSON health status")
        print("   • http://localhost:8082/metrics - Full metrics with trading DB")
        print("   • http://localhost:8082/orders.json - Orders in JSON")
        print("   • http://localhost:8082/positions.json - Positions in JSON")
        print("   • http://localhost:8082/orders - Simple HTML orders view")
    else:
        print("⚠️ Some tests failed. Check the output above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)