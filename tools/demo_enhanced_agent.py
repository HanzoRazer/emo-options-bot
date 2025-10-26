#!/usr/bin/env python3
"""
Comprehensive Demo of Enhanced AI Trading Agent
Showcases robust error handling, enhanced parsing, sophisticated validation, and monitoring.
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.enhanced_intent_router import parse_enhanced, EnhancedIntentRouter
from agents.enhanced_validators import validate_enhanced, EnhancedRiskValidator
from agents.plan_synthesizer import build_plan
from tools.enhanced_agent_happy_path import EnhancedAIAgent, AgentConfig

def demo_enhanced_parsing():
    """Demonstrate enhanced intent parsing capabilities."""
    print("🧠 ENHANCED INTENT PARSING DEMO")
    print("=" * 60)
    
    router = EnhancedIntentRouter()
    
    test_commands = [
        "Build a low risk iron condor on SPY with 14 DTE and 5 point wings",
        "Create aggressive put credit spread QQQ monthly expiration",
        "Set up covered calls on AAPL for income",
        "I want to buy some protective puts on TSLA with moderate risk",
        "Show me the system status please",
        "Help me understand what commands are available",
        "Build something on SPY",  # Ambiguous
        "Make money fast with options",  # Vague
        "",  # Empty input
    ]
    
    for i, command in enumerate(test_commands, 1):
        print(f"\n{i}. Testing: '{command}'")
        print("-" * 40)
        
        intent = router.parse(command)
        
        print(f"Intent: {intent.kind.value}")
        print(f"Symbol: {intent.symbol or 'None'}")
        print(f"Strategy: {intent.strategy or 'None'}")
        print(f"Confidence: {intent.confidence:.2f}")
        print(f"Params: {intent.params}")
        
        if intent.ambiguities:
            print(f"⚠️  Ambiguities: {intent.ambiguities}")
        
        if intent.suggestions:
            print(f"💡 Suggestions: {intent.suggestions}")
    
    print("\n✅ Enhanced parsing demo completed")

def demo_enhanced_validation():
    """Demonstrate enhanced validation capabilities."""
    print("\n🛡️  ENHANCED VALIDATION DEMO")
    print("=" * 60)
    
    validator = EnhancedRiskValidator()
    
    # Create test plans with different risk profiles
    test_cases = [
        {
            "name": "Conservative Iron Condor",
            "symbol": "SPY",
            "strategy": "iron_condor",
            "params": {"dte": 30, "risk_level": "low", "wings": 10}
        },
        {
            "name": "Aggressive Short-Term Spread",
            "symbol": "TSLA", 
            "strategy": "put_credit_spread",
            "params": {"dte": 3, "risk_level": "high", "wings": 3}
        },
        {
            "name": "High-Vol Straddle",
            "symbol": "NVDA",
            "strategy": "long_straddle", 
            "params": {"dte": 7, "risk_level": "moderate", "contracts": 5}
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{i}. Validating: {case['name']}")
        print("-" * 40)
        
        try:
            # Build plan
            plan = build_plan(case["symbol"], case["strategy"], case["params"])
            
            # Enhanced validation
            validation = validator.validate_plan(plan, netliq=100000)
            
            print(f"Status: {'✅ PASSED' if validation.ok else '❌ FAILED'}")
            print(f"Risk Score: {validation.risk_score:.1f}/10")
            print(f"Position Size: {validation.position_size_pct:.2%}")
            
            if validation.risk_metrics:
                print(f"Probability of Profit: {validation.risk_metrics.probability_of_profit:.1%}")
                print(f"Gamma Risk: {validation.risk_metrics.gamma_risk:.1f}/10")
                print(f"Delta Exposure: {validation.risk_metrics.delta_exposure:.2f}")
            
            # Show critical issues
            critical_errors = [e for e in validation.errors if e.severity.value == "critical"]
            high_warnings = [w for w in validation.warnings if w.severity.value == "high"]
            
            if critical_errors:
                print(f"🚨 Critical Errors: {len(critical_errors)}")
                for error in critical_errors[:2]:
                    print(f"   • {error.message}")
            
            if high_warnings:
                print(f"⚠️  High Warnings: {len(high_warnings)}")
                for warning in high_warnings[:2]:
                    print(f"   • {warning.message}")
            
            # Show recommendations
            if validation.recommendations:
                print(f"💡 Recommendations:")
                for rec in validation.recommendations[:2]:
                    print(f"   • {rec}")
            
            # Stress test results
            if validation.stress_test_results:
                print(f"📊 Stress Test Results:")
                for scenario, result in validation.stress_test_results.items():
                    print(f"   {scenario}: ${result:.2f}")
            
        except Exception as e:
            print(f"❌ Validation failed: {e}")
    
    print("\n✅ Enhanced validation demo completed")

def demo_agent_robustness():
    """Demonstrate agent robustness and error handling."""
    print("\n💪 AGENT ROBUSTNESS DEMO")
    print("=" * 60)
    
    # Create agent with test configuration
    config = AgentConfig(
        api_port=8086,  # Different port to avoid conflicts
        voice_enabled=False,
        log_level="DEBUG",
        auto_save_session=True,
        max_retries=2
    )
    
    agent = EnhancedAIAgent(config)
    
    # Test various scenarios
    test_scenarios = [
        {
            "name": "Valid Command",
            "command": "Build an iron condor on SPY with 30 DTE",
            "expected": "success"
        },
        {
            "name": "Invalid Symbol",
            "command": "Create strategy on INVALIDTICKER",
            "expected": "warning"
        },
        {
            "name": "Ambiguous Command",
            "command": "Make money with options",
            "expected": "warning"
        },
        {
            "name": "Risky Command",
            "command": "Put entire portfolio in TSLA options expiring tomorrow",
            "expected": "validation_failed"
        },
        {
            "name": "Empty Command",
            "command": "",
            "expected": "warning"
        },
        {
            "name": "System Command",
            "command": "status",
            "expected": "success"
        }
    ]
    
    print("Testing agent robustness with various scenarios...")
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n{i}. Testing: {scenario['name']}")
        print(f"   Command: '{scenario['command']}'")
        
        try:
            start_time = time.time()
            result = agent.process_command(scenario["command"])
            processing_time = time.time() - start_time
            
            status = result.get("status", "unknown")
            print(f"   Result: {status.upper()}")
            print(f"   Processing Time: {processing_time:.3f}s")
            
            if result.get("error"):
                print(f"   Error: {result['error']}")
            elif result.get("message"):
                print(f"   Message: {result['message'][:60]}...")
            
            # Check if result matches expectation
            if status == scenario["expected"]:
                print("   ✅ Matches expectation")
            else:
                print(f"   ⚠️  Expected {scenario['expected']}, got {status}")
            
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    # Check session state
    print(f"\n📊 Session Summary:")
    print(f"   Commands Processed: {agent.session.commands_processed}")
    print(f"   Errors: {agent.session.errors_count}")
    print(f"   Session ID: {agent.session.session_id}")
    print(f"   History Length: {len(agent.session.command_history)}")
    
    print("\n✅ Agent robustness demo completed")

def demo_performance_monitoring():
    """Demonstrate performance monitoring and metrics."""
    print("\n📈 PERFORMANCE MONITORING DEMO")
    print("=" * 60)
    
    router = EnhancedIntentRouter()
    validator = EnhancedRiskValidator()
    
    # Performance test with multiple commands
    test_commands = [
        "Build iron condor on SPY with 30 DTE",
        "Create put credit spread on QQQ with low risk", 
        "Set up covered call on AAPL monthly",
        "Build protective puts on TSLA with 14 DTE",
        "Make iron condor on NVDA with high risk"
    ] * 5  # Repeat 5 times for 25 total commands
    
    print(f"Processing {len(test_commands)} commands for performance analysis...")
    
    parsing_times = []
    validation_times = []
    total_times = []
    
    for i, command in enumerate(test_commands):
        # Parse timing
        start_time = time.time()
        intent = router.parse(command)
        parse_time = time.time() - start_time
        parsing_times.append(parse_time)
        
        if intent.strategy and intent.symbol:
            try:
                # Plan building timing
                plan_start = time.time()
                plan = build_plan(intent.symbol, intent.strategy, intent.params)
                
                # Validation timing
                val_start = time.time()
                validation = validator.validate_plan(plan)
                val_time = time.time() - val_start
                validation_times.append(val_time)
                
                total_time = time.time() - start_time
                total_times.append(total_time)
                
            except Exception:
                continue
        
        if (i + 1) % 10 == 0:
            print(f"   Processed {i + 1}/{len(test_commands)} commands...")
    
    # Calculate statistics
    if parsing_times:
        print(f"\n📊 Performance Metrics:")
        print(f"   Parsing:")
        print(f"     Average: {sum(parsing_times)/len(parsing_times)*1000:.2f}ms")
        print(f"     Min: {min(parsing_times)*1000:.2f}ms")
        print(f"     Max: {max(parsing_times)*1000:.2f}ms")
    
    if validation_times:
        print(f"   Validation:")
        print(f"     Average: {sum(validation_times)/len(validation_times)*1000:.2f}ms")
        print(f"     Min: {min(validation_times)*1000:.2f}ms")
        print(f"     Max: {max(validation_times)*1000:.2f}ms")
    
    if total_times:
        print(f"   End-to-End:")
        print(f"     Average: {sum(total_times)/len(total_times)*1000:.2f}ms")
        print(f"     Min: {min(total_times)*1000:.2f}ms")
        print(f"     Max: {max(total_times)*1000:.2f}ms")
        print(f"     Throughput: {len(total_times)/sum(total_times):.1f} commands/second")
    
    print("\n✅ Performance monitoring demo completed")

def main():
    """Run comprehensive enhanced agent demo."""
    print("🚀 ENHANCED AI TRADING AGENT - COMPREHENSIVE DEMO")
    print("=" * 80)
    print("Demonstrating robust error handling, enhanced parsing, sophisticated validation")
    print("=" * 80)
    
    try:
        # Run all demo sections
        demo_enhanced_parsing()
        demo_enhanced_validation()
        demo_agent_robustness()
        demo_performance_monitoring()
        
        print("\n" + "=" * 80)
        print("🎉 ALL ENHANCED DEMOS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\nKey Enhancements Demonstrated:")
        print("✅ Confidence scoring for intent parsing")
        print("✅ Sophisticated risk analysis with multiple metrics")
        print("✅ Comprehensive error handling and recovery")
        print("✅ Session state management and audit trails")
        print("✅ Performance monitoring and optimization")
        print("✅ Detailed recommendations and suggestions")
        print("✅ Stress testing and scenario analysis")
        
        print(f"\nTo run the enhanced interactive agent:")
        print(f"python tools/enhanced_agent_happy_path.py")
        
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()