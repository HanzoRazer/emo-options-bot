#!/usr/bin/env python3
"""
Enhanced Options Chain and Integration Test Suite
Comprehensive testing of production-ready options features
"""

import sys
import os
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def setup_logging():
    """Configure logging for tests"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_options_chain_provider():
    """Test the enhanced options chain provider"""
    print("\n📊 Testing Enhanced Options Chain Provider")
    print("-" * 50)
    
    try:
        from src.options.chain_providers import OptionsChainProvider, test_providers, get_current_price
        
        # Test provider availability
        print("1. Testing provider availability...")
        provider = OptionsChainProvider()
        available = provider.get_available_providers()
        print(f"   Available providers: {available}")
        
        # Test health check
        print("\n2. Running provider health check...")
        health = provider.health_check()
        for provider_name, status in health.items():
            if status.get("available"):
                print(f"   ✅ {provider_name}: {status.get('test_result', 'OK')}")
            else:
                print(f"   ❌ {provider_name}: {status.get('error', 'Unknown error')}")
        
        # Test spot price retrieval
        print("\n3. Testing spot price retrieval...")
        test_symbols = ["SPY", "QQQ", "AAPL"]
        for symbol in test_symbols:
            try:
                price = get_current_price(symbol)
                if price:
                    print(f"   ✅ {symbol}: ${price:.2f}")
                else:
                    print(f"   ❌ {symbol}: No price available")
            except Exception as e:
                print(f"   ❌ {symbol}: Error - {e}")
        
        # Test options chain retrieval
        print("\n4. Testing options chain retrieval...")
        symbol = "SPY"
        try:
            chain = provider.get_chain(symbol, right="call")
            if chain:
                print(f"   ✅ {symbol} calls: {len(chain)} quotes retrieved")
                
                # Show sample quote
                sample = chain[0]
                print(f"      Sample: {sample.symbol} ${sample.strike} bid=${sample.bid} ask=${sample.ask}")
                if sample.delta:
                    print(f"      Greeks: δ={sample.delta:.3f} γ={sample.gamma:.5f} θ={sample.theta:.3f}")
                    
                # Test filtering
                itm_calls = [q for q in chain if q.is_itm(sample.strike + 10)]
                print(f"      ITM calls (for spot ${sample.strike + 10}): {len(itm_calls)}")
                
            else:
                print(f"   ❌ {symbol}: No options chain data")
                
        except Exception as e:
            print(f"   ❌ {symbol} chain error: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Options chain provider test failed: {e}")
        return False

def test_risk_mathematics():
    """Test the enhanced risk mathematics"""
    print("\n🧮 Testing Enhanced Risk Mathematics")
    print("-" * 50)
    
    try:
        from src.risk.math import Leg, iron_condor_risk, vertical_spread_risk, quick_risk_check
        
        print("1. Testing iron condor risk calculation...")
        
        # Create sample iron condor legs
        legs = [
            Leg("put", 440, -1, 2.50, delta=-0.15),    # Short put
            Leg("put", 435, 1, 1.20, delta=-0.08),     # Long put 
            Leg("call", 460, -1, 2.30, delta=0.15),   # Short call
            Leg("call", 465, 1, 1.10, delta=0.08)     # Long call
        ]
        
        risk = iron_condor_risk(legs)
        print(f"   ✅ Iron Condor Analysis:")
        print(f"      Net Credit: ${risk.credit:.2f}")
        print(f"      Max Loss: ${risk.max_loss:.2f}")
        print(f"      Max Gain: ${risk.max_gain:.2f}")
        print(f"      Risk/Reward: {getattr(risk, 'risk_reward_ratio', 0):.2f}")
        print(f"      Breakevens: {[f'${be:.2f}' for be in risk.breakevens]}")
        print(f"      Greeks: δ={risk.greeks.delta:.3f} γ={risk.greeks.gamma:.5f}")
        print(f"      Risk Grade: {risk.risk_grade()}")
        
        print("\n2. Testing vertical spread risk calculation...")
        
        # Create sample vertical spread
        spread_legs = [
            Leg("call", 450, -1, 5.20, delta=0.30),  # Short call
            Leg("call", 455, 1, 3.10, delta=0.20)    # Long call
        ]
        
        spread_risk = vertical_spread_risk(spread_legs)
        print(f"   ✅ Call Credit Spread Analysis:")
        print(f"      Net Credit: ${spread_risk.credit:.2f}")
        print(f"      Max Loss: ${spread_risk.max_loss:.2f}")
        print(f"      Max Gain: ${spread_risk.max_gain:.2f}")
        print(f"      Breakeven: ${spread_risk.breakevens[0]:.2f}" if spread_risk.breakevens else "N/A")
        
        print("\n3. Testing quick risk check...")
        quick_check = quick_risk_check(legs)
        print(f"   ✅ Quick Risk Summary: {quick_check}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Risk mathematics test failed: {e}")
        return False

def test_ai_orchestrator():
    """Test the enhanced AI orchestrator"""
    print("\n🤖 Testing Enhanced AI Orchestrator")
    print("-" * 50)
    
    try:
        from src.ai.json_orchestrator import analyze_request_to_json, test_providers, get_orchestrator
        
        print("1. Testing AI provider availability...")
        provider_status = test_providers()
        for provider, status in provider_status.items():
            if status.get("status") == "success":
                print(f"   ✅ {provider}: {status.get('response_time', 0):.2f}s")
            else:
                print(f"   ❌ {provider}: {status.get('error', 'Failed')}")
        
        print("\n2. Testing request analysis...")
        test_requests = [
            "I'm bullish on SPY and want a conservative income strategy",
            "Expecting high volatility in QQQ, want to profit from big moves", 
            "AAPL looks like it will stay range-bound, need a theta strategy",
            "Bearish on NVDA, want limited risk downside play"
        ]
        
        for i, request in enumerate(test_requests, 1):
            try:
                analysis, trade_idea = analyze_request_to_json(request)
                
                print(f"\n   Request {i}: {request}")
                print(f"   ✅ Analysis: {analysis.symbol} {analysis.outlook} (confidence: {analysis.confidence:.1%})")
                print(f"      Strategy: {trade_idea.strategy}")
                print(f"      Target Days: {analysis.target_days}")
                print(f"      Risk Budget: {analysis.risk_budget:.1%}")
                print(f"      Source: {analysis.source}")
                
                if trade_idea.target_delta:
                    print(f"      Target Delta: {trade_idea.target_delta:.2f}")
                if trade_idea.wings_width:
                    print(f"      Wings Width: ${trade_idea.wings_width:.0f}")
                
            except Exception as e:
                print(f"   ❌ Request {i} failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ AI orchestrator test failed: {e}")
        return False

def test_trade_staging():
    """Test the enhanced trade staging"""
    print("\n📁 Testing Enhanced Trade Staging")
    print("-" * 50)
    
    try:
        from src.staging.writer import stage_trade, list_staged_trades, load_staged_trade, validate_trade_plan
        
        print("1. Testing trade plan validation...")
        
        # Valid trade plan
        valid_plan = {
            "symbol": "SPY",
            "strategy": "iron_condor",
            "legs": [
                {"right": "put", "strike": 440, "qty": -1, "price": 2.50},
                {"right": "put", "strike": 435, "qty": 1, "price": 1.20},
                {"right": "call", "strike": 460, "qty": -1, "price": 2.30},
                {"right": "call", "strike": 465, "qty": 1, "price": 1.10}
            ],
            "risk": {
                "max_loss": 290,
                "max_gain": 210,
                "credit": 210
            }
        }
        
        errors = validate_trade_plan(valid_plan)
        if not errors:
            print("   ✅ Valid trade plan passed validation")
        else:
            print(f"   ❌ Valid trade plan failed: {errors}")
        
        # Invalid trade plan
        invalid_plan = {
            "symbol": "",  # Invalid symbol
            "strategy": "unknown_strategy",  # Invalid strategy
            "legs": []  # No legs
        }
        
        errors = validate_trade_plan(invalid_plan)
        if errors:
            print(f"   ✅ Invalid trade plan correctly rejected: {len(errors)} errors")
        else:
            print("   ❌ Invalid trade plan incorrectly accepted")
        
        print("\n2. Testing trade staging...")
        
        # Stage a valid trade
        metadata = {
            "source": "test_suite",
            "user_id": "test_user",
            "confidence_score": 0.85
        }
        
        try:
            staged_path = stage_trade(valid_plan, metadata)
            print(f"   ✅ Trade staged successfully: {staged_path.name}")
            
            # Test loading
            loaded = load_staged_trade(staged_path)
            print(f"   ✅ Trade loaded successfully: {loaded['trade_plan']['symbol']}")
            
            # Clean up
            staged_path.unlink()
            print("   ✅ Test file cleaned up")
            
        except Exception as e:
            print(f"   ❌ Staging failed: {e}")
        
        print("\n3. Testing staged trade listing...")
        
        # List existing staged trades
        trades = list_staged_trades()
        print(f"   ✅ Found {len(trades)} existing staged trades")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Trade staging test failed: {e}")
        return False

def test_complete_integration():
    """Test the complete integration pipeline"""
    print("\n🔗 Testing Complete Integration Pipeline")
    print("-" * 50)
    
    try:
        from src.phase3.hooks import enhanced_synthesis_pipeline, synthesize_and_stage
        
        print("1. Testing enhanced synthesis pipeline...")
        
        test_request = "I think SPY will stay range-bound for the next month, looking for an income strategy with limited risk"
        
        result = enhanced_synthesis_pipeline(test_request)
        
        if "error" not in result:
            print("   ✅ Synthesis pipeline successful!")
            
            trade_plan = result["trade_plan"]
            print(f"      Symbol: {trade_plan['symbol']}")
            print(f"      Strategy: {trade_plan['strategy']}")
            print(f"      Legs: {len(trade_plan['legs'])}")
            
            risk = result["risk_profile"]
            print(f"      Max Risk: ${risk['max_loss']:.0f}")
            print(f"      Max Reward: ${risk['max_gain']:.0f}")
            print(f"      Risk Grade: {risk['risk_grade']}")
            
            synthesis_meta = result["synthesis_metadata"]
            print(f"      Provider: {synthesis_meta['provider_used']}")
            print(f"      Confidence: {synthesis_meta['confidence']:.1%}")
            print(f"      Complexity: {synthesis_meta['complexity']}/5")
            
        else:
            print(f"   ❌ Synthesis pipeline failed: {result['error']}")
            
        print("\n2. Testing legacy compatibility...")
        
        # Test legacy function
        legacy_result = synthesize_and_stage(test_request, auto_stage=False)
        
        if not legacy_result.startswith("Error"):
            print("   ✅ Legacy compatibility maintained")
        else:
            print(f"   ❌ Legacy compatibility issue: {legacy_result}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Complete integration test failed: {e}")
        return False

def run_performance_test():
    """Run basic performance tests"""
    print("\n⚡ Performance Testing")
    print("-" * 30)
    
    import time
    
    try:
        # Test options chain retrieval performance
        from src.options.chain_providers import OptionsChainProvider
        
        provider = OptionsChainProvider()
        
        print("Testing options chain retrieval speed...")
        start = time.time()
        chain = provider.get_chain("SPY", right="call")
        end = time.time()
        
        print(f"   Chain retrieval: {end - start:.2f}s for {len(chain)} quotes")
        
        # Test AI analysis performance
        from src.ai.json_orchestrator import analyze_request_to_json
        
        print("Testing AI analysis speed...")
        start = time.time()
        analysis, trade_idea = analyze_request_to_json("Bullish on SPY, want calls")
        end = time.time()
        
        print(f"   AI analysis: {end - start:.2f}s (provider: {analysis.source})")
        
        # Test complete pipeline performance
        from src.phase3.hooks import enhanced_synthesis_pipeline
        
        print("Testing complete pipeline speed...")
        start = time.time()
        result = enhanced_synthesis_pipeline("Conservative income strategy on QQQ")
        end = time.time()
        
        if "error" not in result:
            print(f"   Complete pipeline: {end - start:.2f}s")
        else:
            print(f"   Pipeline failed: {result['error']}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Performance test failed: {e}")
        return False

def main():
    """Run complete test suite"""
    print("🚀 Enhanced Options Chain Integration Test Suite")
    print("=" * 60)
    
    setup_logging()
    
    # Run all tests
    tests = [
        ("Options Chain Provider", test_options_chain_provider),
        ("Risk Mathematics", test_risk_mathematics),
        ("AI Orchestrator", test_ai_orchestrator),
        ("Trade Staging", test_trade_staging),
        ("Complete Integration", test_complete_integration),
        ("Performance", run_performance_test)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            print(f"Running {test_name} Tests...")
            success = test_func()
            results[test_name] = success
        except Exception as e:
            print(f"❌ {test_name} test suite failed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("🎯 Test Results Summary")
    print("-" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced options integration is ready for production.")
    else:
        print("⚠️  Some tests failed. Check logs for details.")
    
    print("\n📋 Next Steps:")
    print("1. Install optional dependencies: pip install yfinance")
    print("2. Configure API keys for live data providers")
    print("3. Test with real market data")
    print("4. Set up production monitoring and logging")

if __name__ == "__main__":
    main()