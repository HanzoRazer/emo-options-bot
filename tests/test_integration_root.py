#!/usr/bin/env python3
"""
EMO Trading System Integration Test Suite
=========================================
Comprehensive integration tests for the enterprise trading system including:
- Trading database connectivity and session management
- Advanced query engine performance
- Portfolio analytics and risk assessment
- Order validation and compliance checking
- Performance monitoring and alerting
- Enhanced health monitoring dashboard
"""

import sys
import os
import time
import tempfile
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_enhanced_trading_session():
    """Test enhanced trading session manager."""
    print("🔧 Testing Enhanced Trading Session Manager...")
    
    try:
        from src.database.enhanced_trading_session import (
            EnhancedTradingSession, ConnectionState, enhanced_session_scope, enhanced_health_check
        )
        
        # Test session creation
        session_manager = EnhancedTradingSession()
        assert session_manager is not None
        print("  ✅ Session manager created")
        
        # Test health check
        health_status = enhanced_health_check()
        assert isinstance(health_status, dict)
        print(f"  ✅ Health check: {health_status.get('status', 'unknown')}")
        
        # Test session scope context manager
        with enhanced_session_scope() as session:
            assert session is not None
            print("  ✅ Session scope context manager works")
        
        # Test connection metrics
        metrics = session_manager.get_connection_metrics()
        assert isinstance(metrics.active_connections, int)
        print(f"  ✅ Connection metrics: {metrics.active_connections} active connections")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Enhanced trading session test failed: {e}")
        return False

def test_advanced_query_engine():
    """Test advanced query engine."""
    print("🔧 Testing Advanced Query Engine...")
    
    try:
        from src.database.advanced_read_paths import (
            get_query_engine, AdvancedQueryEngine, QueryResult, 
            fetch_positions_advanced, get_query_performance_stats
        )
        
        # Test query engine creation
        engine = get_query_engine()
        assert isinstance(engine, AdvancedQueryEngine)
        print("  ✅ Query engine created")
        
        # Test schema information
        schema_info = engine.schema
        assert schema_info is not None
        print("  ✅ Schema information available")
        
        # Test query building
        query = engine.build_flexible_query(
            table_name='test_table',
            columns=['symbol', 'quantity', 'price'],
            filters={'status': 'FILLED'},
            limit=100
        )
        assert 'SELECT' in query
        assert 'test_table' in query
        print("  ✅ Query building works")
        
        # Test performance stats
        stats = get_query_performance_stats()
        assert isinstance(stats, dict)
        print(f"  ✅ Performance stats: {len(stats.get('table_stats', {}))} tables tracked")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Advanced query engine test failed: {e}")
        return False

def test_trading_analytics():
    """Test trading analytics engine."""
    print("🔧 Testing Trading Analytics Engine...")
    
    try:
        from src.analytics.trading_analytics import (
            get_analytics_engine, TradingAnalyticsEngine, PositionAnalytics,
            PortfolioMetrics, get_portfolio_summary, get_risk_dashboard
        )
        
        # Test analytics engine creation
        engine = get_analytics_engine()
        assert isinstance(engine, TradingAnalyticsEngine)
        print("  ✅ Analytics engine created")
        
        # Test portfolio analytics
        portfolio_metrics = engine.get_portfolio_analytics()
        assert isinstance(portfolio_metrics, PortfolioMetrics)
        print("  ✅ Portfolio analytics computed")
        
        # Test risk assessment
        risk_metrics = engine.get_risk_assessment()
        assert hasattr(risk_metrics, 'risk_score')
        print(f"  ✅ Risk assessment: score {risk_metrics.risk_score}")
        
        # Test convenience functions
        portfolio_summary = get_portfolio_summary()
        assert isinstance(portfolio_summary, dict)
        print("  ✅ Portfolio summary generated")
        
        risk_dashboard = get_risk_dashboard()
        assert isinstance(risk_dashboard, dict)
        print("  ✅ Risk dashboard generated")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Trading analytics test failed: {e}")
        return False

def test_order_validation():
    """Test order validation system."""
    print("🔧 Testing Order Validation System...")
    
    try:
        from src.validation.order_validator import OrderValidator
        
        # Test validator creation
        validator = OrderValidator()
        assert validator is not None
        print("  ✅ Order validator created")
        
        # Test order validation
        test_order = {
            'symbol': 'AAPL',
            'side': 'BUY',
            'quantity': 100,
            'price': 150.0,
            'order_type': 'LIMIT'
        }
        
        is_valid, errors = validator.validate_order(test_order)
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)
        print(f"  ✅ Order validation: {'valid' if is_valid else 'invalid'} ({len(errors)} errors)")
        
        # Test risk scoring
        risk_score = validator.calculate_risk_score(test_order)
        assert isinstance(risk_score, (int, float))
        print(f"  ✅ Risk scoring: {risk_score}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Order validation test failed: {e}")
        return False

def test_performance_monitoring():
    """Test performance monitoring system."""
    print("🔧 Testing Performance Monitoring System...")
    
    try:
        from src.monitoring.performance import (
            PerformanceMonitor, PerformanceMetric,
            get_performance_summary, get_performance_alerts
        )
        
        # Test monitor creation
        monitor = PerformanceMonitor()
        assert isinstance(monitor, PerformanceMonitor)
        print("  ✅ Performance monitor created")
        
        # Test metrics recording
        monitor.record_metric('test_metric', 42.0)
        print("  ✅ Metric recording works")
        
        # Test summary generation
        summary = get_performance_summary()
        assert isinstance(summary, dict)
        print("  ✅ Performance summary generated")
        
        # Test alert checking
        alerts = get_performance_alerts()
        assert isinstance(alerts, list)
        print(f"  ✅ Alert checking: {len(alerts)} alerts")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Performance monitoring test failed: {e}")
        return False

def test_health_monitoring_integration():
    """Test health monitoring integration."""
    print("🔧 Testing Health Monitoring Integration...")
    
    try:
        # Test health monitor import
        import tools.emit_health as health_module
        assert hasattr(health_module, 'HealthRequestHandler')
        print("  ✅ Health monitor module loaded")
        
        # Test global state
        state = health_module._state
        assert isinstance(state, dict)
        print("  ✅ Global state accessible")
        
        # Test trading database readiness
        trading_db_ready = health_module._TRADING_DB_READY
        print(f"  ✅ Trading DB ready: {trading_db_ready}")
        
        # Test handler class
        handler_class = health_module.HealthRequestHandler
        assert handler_class is not None
        print("  ✅ Handler class available")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Health monitoring integration test failed: {e}")
        return False

def test_end_to_end_integration():
    """Test end-to-end system integration."""
    print("🔧 Testing End-to-End Integration...")
    
    try:
        # Create a temporary database for testing
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name
        
        # Create test database schema
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create test tables
        cursor.execute('''
            CREATE TABLE positions (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                quantity REAL,
                avg_price REAL,
                market_value REAL,
                unrealized_pnl REAL,
                realized_pnl REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE trades (
                id INTEGER PRIMARY KEY,
                symbol TEXT,
                side TEXT,
                quantity REAL,
                price REAL,
                pnl REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert test data
        cursor.execute('''
            INSERT INTO positions (symbol, quantity, avg_price, market_value, unrealized_pnl, realized_pnl)
            VALUES ('AAPL', 100, 150.0, 15500.0, 500.0, 0.0)
        ''')
        
        cursor.execute('''
            INSERT INTO trades (symbol, side, quantity, price, pnl)
            VALUES ('AAPL', 'BUY', 100, 150.0, 0.0)
        ''')
        
        conn.commit()
        conn.close()
        
        print("  ✅ Test database created with sample data")
        
        # Test integration components
        components_working = 0
        total_components = 6
        
        if test_enhanced_trading_session():
            components_working += 1
        
        if test_advanced_query_engine():
            components_working += 1
        
        if test_trading_analytics():
            components_working += 1
        
        if test_order_validation():
            components_working += 1
        
        if test_performance_monitoring():
            components_working += 1
        
        if test_health_monitoring_integration():
            components_working += 1
        
        # Clean up
        os.unlink(db_path)
        
        success_rate = (components_working / total_components) * 100
        print(f"  ✅ Integration test complete: {components_working}/{total_components} components working ({success_rate:.1f}%)")
        
        return components_working == total_components
        
    except Exception as e:
        print(f"  ❌ End-to-end integration test failed: {e}")
        return False

def run_integration_tests():
    """Run all integration tests."""
    print("🚀 EMO Trading System Integration Test Suite")
    print("=" * 50)
    
    start_time = time.time()
    
    tests = [
        ("Enhanced Trading Session", test_enhanced_trading_session),
        ("Advanced Query Engine", test_advanced_query_engine),
        ("Trading Analytics", test_trading_analytics),
        ("Order Validation", test_order_validation),
        ("Performance Monitoring", test_performance_monitoring),
        ("Health Monitoring Integration", test_health_monitoring_integration),
        ("End-to-End Integration", test_end_to_end_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    duration = time.time() - start_time
    
    print("\n" + "=" * 50)
    print(f"🏁 Integration Test Results: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
    print(f"⏱️  Total time: {duration:.2f} seconds")
    
    if passed == total:
        print("🎉 All integration tests passed! System is ready for production.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)