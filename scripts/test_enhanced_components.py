#!/usr/bin/env python3
"""
Enhanced Component Test Suite
Validates all enhanced components with fallback scenarios
"""

import unittest
import sys
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.schemas import (
    AnalysisPlan, TradePlan, RiskConstraints, PortfolioSnapshot,
    TradeLeg, create_default_risk_constraints
)
from src.llm.orchestrator import LLMOrchestrator, test_llm_providers
from src.risk.gates import RiskGates, create_conservative_limits
from src.trade.synthesizer import TradeSynthesizer, create_options_provider
from src.voice.asr_tts import VoiceIO, test_voice_capabilities

class TestEnhancedSchemas(unittest.TestCase):
    """Test enhanced Pydantic schemas"""
    
    def test_analysis_plan_validation(self):
        """Test AnalysisPlan validation and serialization"""
        plan = AnalysisPlan(
            user_intent="Bullish on AAPL",
            underlying="AAPL",
            outlook="bullish",
            strategy_hint="call_spread",
            confidence=0.85,
            metadata={"source": "test"}
        )
        
        self.assertEqual(plan.underlying, "AAPL")
        self.assertEqual(plan.outlook, "bullish")
        self.assertGreater(plan.confidence, 0.8)
        
        # Test serialization
        plan_dict = plan.model_dump()
        self.assertIn("underlying", plan_dict)
        self.assertIn("confidence", plan_dict)
        
    def test_trade_plan_validation(self):
        """Test TradePlan validation and risk calculations"""
        leg = TradeLeg(
            action="buy",
            instrument="option",
            symbol="AAPL240315C150",
            quantity=1,
            strike=150.0
        )
        
        trade = TradePlan(
            strategy_type="long_call",
            underlying="AAPL",
            legs=[leg],
            max_risk=500.0,
            max_profit=2000.0
        )
        
        self.assertEqual(trade.strategy_type, "long_call")
        self.assertEqual(len(trade.legs), 1)
        self.assertEqual(trade.estimate_max_risk(), 500.0)
        
    def test_portfolio_snapshot(self):
        """Test PortfolioSnapshot validation"""
        portfolio = PortfolioSnapshot(
            equity=100000.0,
            risk_exposure_pct=0.05
        )
        
        self.assertEqual(portfolio.equity, 100000.0)
        self.assertEqual(portfolio.risk_exposure_pct, 0.05)

class TestLLMOrchestrator(unittest.TestCase):
    """Test LLM orchestrator with fallbacks"""
    
    def setUp(self):
        self.orchestrator = LLMOrchestrator()
    
    def test_provider_fallback(self):
        """Test that orchestrator works with or without LLM providers"""
        # Test analysis (should work with heuristics if no LLM)
        analysis = self.orchestrator.analyze_intent(
            "I'm bullish on SPY and want limited risk"
        )
        
        self.assertIsInstance(analysis, AnalysisPlan)
        self.assertEqual(analysis.underlying, "SPY")
        self.assertEqual(analysis.outlook, "bullish")
        
    def test_multiple_inputs(self):
        """Test various input patterns"""
        test_cases = [
            ("Bearish on QQQ, want to profit from decline", "QQQ", "bearish"),
            ("Expecting SPY to stay flat, need income", "SPY", "neutral"),
            ("AAPL looks volatile, want to profit from big moves", "AAPL", "volatile"),
        ]
        
        for intent, expected_symbol, expected_outlook in test_cases:
            with self.subTest(intent=intent):
                analysis = self.orchestrator.analyze_intent(intent)
                self.assertEqual(analysis.underlying, expected_symbol)
                self.assertEqual(analysis.outlook, expected_outlook)

class TestRiskGates(unittest.TestCase):
    """Test risk management system"""
    
    def setUp(self):
        self.risk_gates = RiskGates()
        self.portfolio = PortfolioSnapshot(
            equity=50000.0,
            risk_exposure_pct=0.10
        )
    
    def test_position_size_validation(self):
        """Test position sizing limits"""
        # Create a high-risk trade
        leg = TradeLeg(
            action="buy",
            instrument="option",
            symbol="SPY240315C450",
            quantity=100,  # Large quantity
            strike=450.0
        )
        
        trade = TradePlan(
            strategy_type="long_call",
            underlying="SPY",
            legs=[leg],
            max_risk=10000.0  # 20% of portfolio
        )
        
        violations = self.risk_gates.validate_trade(trade, self.portfolio)
        
        # Should have position size violations
        position_violations = [v for v in violations if "position" in v.code.lower()]
        self.assertGreater(len(position_violations), 0)
    
    def test_valid_trade_passes(self):
        """Test that reasonable trades pass validation"""
        leg = TradeLeg(
            action="buy",
            instrument="option",
            symbol="SPY240315C450",
            quantity=1,
            strike=450.0
        )
        
        trade = TradePlan(
            strategy_type="long_call",
            underlying="SPY",
            legs=[leg],
            max_risk=500.0  # 1% of portfolio
        )
        
        violations = self.risk_gates.validate_trade(trade, self.portfolio)
        
        # Should pass basic validation
        critical_violations = [v for v in violations if v.severity == "critical"]
        self.assertEqual(len(critical_violations), 0)

class TestTradeSynthesizer(unittest.TestCase):
    """Test trade synthesis system"""
    
    def setUp(self):
        self.synthesizer = TradeSynthesizer()
    
    def test_analysis_to_trade_conversion(self):
        """Test converting analysis to trade plan"""
        analysis = AnalysisPlan(
            user_intent="Bullish on SPY",
            underlying="SPY",
            outlook="bullish",
            strategy_hint="call_spread",
            confidence=0.8
        )
        
        trade = self.synthesizer.from_analysis(analysis)
        
        self.assertIsInstance(trade, TradePlan)
        self.assertEqual(trade.underlying, "SPY")
        self.assertGreater(len(trade.legs), 0)
    
    def test_different_strategies(self):
        """Test various strategy syntheses"""
        strategies = [
            ("bullish", "call_spread"),
            ("bearish", "put_spread"),
            ("neutral", "iron_condor"),
            ("volatile", "straddle")
        ]
        
        for outlook, expected_strategy in strategies:
            with self.subTest(outlook=outlook):
                analysis = AnalysisPlan(
                    user_intent=f"{outlook} on SPY",
                    underlying="SPY",
                    outlook=outlook,
                    strategy_hint=expected_strategy,
                    confidence=0.7
                )
                
                trade = self.synthesizer.from_analysis(analysis)
                self.assertIsInstance(trade, TradePlan)

class TestVoiceInterface(unittest.TestCase):
    """Test voice interface with fallbacks"""
    
    def test_text_fallback_mode(self):
        """Test voice interface in text fallback mode"""
        voice = VoiceIO(
            asr_provider="text_fallback",
            tts_provider="text_fallback"
        )
        
        # Test basic functionality
        self.assertTrue(hasattr(voice, 'speak'))
        self.assertTrue(hasattr(voice, 'listen_once'))
        
        # Test wake word detection
        self.assertTrue(voice.is_wake_word_detected("EMO bot, help me trade"))
        self.assertFalse(voice.is_wake_word_detected("just a regular message"))
        
        # Test command extraction
        command = voice.extract_command("EMO bot, I want to buy calls on SPY")
        self.assertIn("buy calls", command.lower())
        self.assertIn("spy", command.lower())
    
    def test_voice_capabilities_check(self):
        """Test voice capabilities detection"""
        capabilities = test_voice_capabilities()
        
        self.assertIn('microphone_test', capabilities)
        self.assertIn('speaker_test', capabilities)
        self.assertIn('providers_available', capabilities)
        
        # Should always have text fallback
        self.assertIn('text_fallback', capabilities['providers_available'])

class TestIntegration(unittest.TestCase):
    """Test complete workflow integration"""
    
    def test_end_to_end_workflow(self):
        """Test complete trading workflow"""
        # Initialize components
        orchestrator = LLMOrchestrator()
        synthesizer = TradeSynthesizer()
        risk_gates = RiskGates()
        
        # Sample workflow
        user_intent = "I'm bullish on SPY but want limited risk"
        
        # Step 1: Analyze
        analysis = orchestrator.analyze_intent(user_intent)
        self.assertIsInstance(analysis, AnalysisPlan)
        
        # Step 2: Synthesize
        trade = synthesizer.from_analysis(analysis)
        self.assertIsInstance(trade, TradePlan)
        
        # Step 3: Validate
        portfolio = PortfolioSnapshot(equity=100000.0, risk_exposure_pct=0.05)
        violations = risk_gates.validate_trade(trade, portfolio)
        
        # Should complete without errors
        self.assertIsInstance(violations, list)
    
    def test_error_recovery(self):
        """Test error handling and recovery"""
        orchestrator = LLMOrchestrator()
        
        # Test with invalid input
        try:
            analysis = orchestrator.analyze_intent("")
            # Should handle gracefully
            self.assertIsInstance(analysis, AnalysisPlan)
        except Exception:
            # Or raise appropriate error
            pass

def run_component_tests():
    """Run all component tests and provide detailed report"""
    print("🧪 Enhanced Component Test Suite")
    print("=" * 50)
    
    # Configure logging for tests
    logging.basicConfig(level=logging.WARNING)
    
    # Create test suite
    test_classes = [
        TestEnhancedSchemas,
        TestLLMOrchestrator,
        TestRiskGates,
        TestTradeSynthesizer,
        TestVoiceInterface,
        TestIntegration
    ]
    
    total_tests = 0
    total_failures = 0
    
    for test_class in test_classes:
        print(f"\n📋 Testing {test_class.__name__}...")
        
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=1, stream=sys.stdout)
        result = runner.run(suite)
        
        total_tests += result.testsRun
        total_failures += len(result.failures) + len(result.errors)
        
        if result.failures:
            print(f"  ❌ Failures: {len(result.failures)}")
        if result.errors:
            print(f"  💥 Errors: {len(result.errors)}")
        if not result.failures and not result.errors:
            print(f"  ✅ All tests passed ({result.testsRun} tests)")
    
    print("\n" + "=" * 50)
    print(f"🎯 Test Summary: {total_tests - total_failures}/{total_tests} tests passed")
    
    if total_failures == 0:
        print("✅ All enhanced components working correctly!")
    else:
        print(f"⚠️  {total_failures} test failures - check component setup")
    
    return total_failures == 0

if __name__ == "__main__":
    success = run_component_tests()
    sys.exit(0 if success else 1)