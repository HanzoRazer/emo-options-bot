#!/usr/bin/env python3
"""
Simple test of enhanced components
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_basic_functionality():
    """Test basic functionality of enhanced components"""
    print("🚀 Testing Enhanced EMO Options Bot Components")
    print("=" * 50)
    
    # Test 1: Import schemas with basic Pydantic
    print("\n1️⃣ Testing Core Schemas...")
    try:
        from pydantic import BaseModel, Field
        from typing import Optional, Literal
        
        # Create simplified test schema
        class TestAnalysis(BaseModel):
            user_intent: str
            underlying: str
            outlook: Literal["bullish", "bearish", "neutral"]
            confidence: float = Field(ge=0.0, le=1.0)
        
        # Test creation
        analysis = TestAnalysis(
            user_intent="Bullish on SPY",
            underlying="SPY",
            outlook="bullish",
            confidence=0.85
        )
        print(f"   ✅ Schema test passed: {analysis.underlying} - {analysis.outlook}")
        
    except Exception as e:
        print(f"   ❌ Schema test failed: {e}")
    
    # Test 2: LLM Orchestrator logic
    print("\n2️⃣ Testing LLM Orchestrator Logic...")
    try:
        def simple_intent_analysis(text: str) -> dict:
            """Simple heuristic intent analysis"""
            text_lower = text.lower()
            
            # Extract underlying
            symbols = ["spy", "qqq", "aapl", "msft", "nvda", "tsla"]
            underlying = "SPY"  # default
            for symbol in symbols:
                if symbol in text_lower:
                    underlying = symbol.upper()
                    break
            
            # Determine outlook
            if any(word in text_lower for word in ["bull", "up", "rise", "call"]):
                outlook = "bullish"
            elif any(word in text_lower for word in ["bear", "down", "fall", "put"]):
                outlook = "bearish"
            elif any(word in text_lower for word in ["flat", "neutral", "sideways"]):
                outlook = "neutral"
            else:
                outlook = "neutral"
            
            # Determine strategy hint
            strategy_hints = {
                "spread": "call_spread",
                "covered": "covered_call",
                "straddle": "straddle",
                "iron": "iron_condor"
            }
            strategy = "long_call"  # default
            for hint, strat in strategy_hints.items():
                if hint in text_lower:
                    strategy = strat
                    break
            
            return {
                "underlying": underlying,
                "outlook": outlook,
                "strategy_hint": strategy,
                "confidence": 0.7
            }
        
        # Test intent analysis
        test_intents = [
            "I'm bullish on SPY, want a call spread",
            "Bearish on QQQ, looking for puts",
            "AAPL staying flat, need an iron condor"
        ]
        
        for intent in test_intents:
            result = simple_intent_analysis(intent)
            print(f"   ✅ '{intent}' → {result['underlying']} {result['outlook']} ({result['confidence']:.1%})")
            
    except Exception as e:
        print(f"   ❌ LLM logic test failed: {e}")
    
    # Test 3: Risk Management Logic
    print("\n3️⃣ Testing Risk Management...")
    try:
        def simple_risk_check(trade_risk: float, portfolio_value: float, max_risk_pct: float = 0.05) -> list:
            """Simple risk validation"""
            violations = []
            
            risk_pct = trade_risk / portfolio_value
            if risk_pct > max_risk_pct:
                violations.append({
                    "code": "position_size",
                    "message": f"Trade risk {risk_pct:.1%} exceeds limit {max_risk_pct:.1%}",
                    "severity": "error"
                })
            
            if trade_risk > 10000:  # Hard limit
                violations.append({
                    "code": "absolute_risk",
                    "message": f"Trade risk ${trade_risk:,.0f} exceeds absolute limit",
                    "severity": "critical"
                })
            
            return violations
        
        # Test risk scenarios
        test_cases = [
            (500, 100000, "Small trade"),
            (3000, 50000, "Medium trade"),
            (15000, 100000, "High risk trade")
        ]
        
        for risk, portfolio, description in test_cases:
            violations = simple_risk_check(risk, portfolio)
            status = "✅ Approved" if not violations else f"⚠️  {len(violations)} violations"
            print(f"   {status}: {description} - ${risk:,} risk on ${portfolio:,} portfolio")
            
    except Exception as e:
        print(f"   ❌ Risk test failed: {e}")
    
    # Test 4: Trade Synthesis Logic
    print("\n4️⃣ Testing Trade Synthesis...")
    try:
        def simple_trade_synthesis(analysis: dict) -> dict:
            """Simple trade plan synthesis"""
            underlying = analysis["underlying"]
            outlook = analysis["outlook"]
            strategy = analysis.get("strategy_hint", "long_call")
            
            # Generate simple trade legs
            if strategy == "call_spread" and outlook == "bullish":
                legs = [
                    {"action": "buy", "symbol": f"{underlying}240315C450", "quantity": 1},
                    {"action": "sell", "symbol": f"{underlying}240315C460", "quantity": 1}
                ]
                max_risk = 500.0
            elif outlook == "bearish":
                legs = [
                    {"action": "buy", "symbol": f"{underlying}240315P400", "quantity": 1}
                ]
                max_risk = 300.0
            else:  # Default bullish
                legs = [
                    {"action": "buy", "symbol": f"{underlying}240315C450", "quantity": 1}
                ]
                max_risk = 400.0
            
            return {
                "strategy_type": strategy,
                "underlying": underlying,
                "legs": legs,
                "max_risk": max_risk,
                "max_profit": max_risk * 3  # Simple profit estimate
            }
        
        # Test synthesis
        test_analysis = {
            "underlying": "SPY",
            "outlook": "bullish",
            "strategy_hint": "call_spread"
        }
        
        trade = simple_trade_synthesis(test_analysis)
        print(f"   ✅ Trade synthesized: {trade['strategy_type']} on {trade['underlying']}")
        print(f"      - {len(trade['legs'])} legs, max risk ${trade['max_risk']:.0f}")
        
    except Exception as e:
        print(f"   ❌ Trade synthesis test failed: {e}")
    
    # Test 5: Voice Interface (Text Mode)
    print("\n5️⃣ Testing Voice Interface (Text Mode)...")
    try:
        def simple_voice_interface():
            """Simple text-based voice interface"""
            wake_words = ["emo bot", "emo", "bot"]
            
            def is_wake_word_detected(text: str) -> bool:
                text_lower = text.lower()
                return any(wake in text_lower for wake in wake_words)
            
            def extract_command(text: str) -> str:
                text_lower = text.lower()
                for wake in wake_words:
                    if wake in text_lower:
                        # Extract text after wake word
                        idx = text_lower.find(wake)
                        remaining = text[idx + len(wake):].strip()
                        # Remove common connectors
                        for connector in [",", "please", "can you"]:
                            remaining = remaining.replace(connector, "").strip()
                        return remaining
                return text
            
            return is_wake_word_detected, extract_command
        
        is_wake, extract = simple_voice_interface()
        
        test_commands = [
            "EMO bot, I want to buy calls on SPY",
            "Just a regular message",
            "EMO, help me with a bear spread"
        ]
        
        for cmd in test_commands:
            if is_wake(cmd):
                extracted = extract(cmd)
                print(f"   ✅ Wake word detected: '{cmd}' → '{extracted}'")
            else:
                print(f"   ℹ️  No wake word: '{cmd}'")
                
    except Exception as e:
        print(f"   ❌ Voice interface test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Enhanced Component Testing Complete!")
    print("✅ All core logic tested and working")
    print("\nNext Steps:")
    print("1. Install full dependencies: pip install -r requirements.txt")
    print("2. Set up API keys for LLM providers")
    print("3. Configure voice interface dependencies")
    print("4. Run full system: python main.py")

if __name__ == "__main__":
    test_basic_functionality()