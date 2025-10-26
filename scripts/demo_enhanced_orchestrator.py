#!/usr/bin/env python3
"""
Enhanced Trade Orchestrator - Integration Demo
Demonstrates the production-ready trade orchestration system
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.schemas import AnalysisPlan, create_default_risk_constraints
from src.llm.orchestrator import LLMOrchestrator, test_llm_providers
from src.risk.gates import RiskGates, create_conservative_limits
from src.trade.synthesizer import TradeSynthesizer, create_options_provider
from src.voice.asr_tts import VoiceIO, test_voice_capabilities, get_optimal_voice_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_system_capabilities():
    """Test all system capabilities and provide status report"""
    print("🚀 EMO Options Bot - Enhanced System Capabilities Test")
    print("=" * 60)
    
    # Test LLM providers
    print("\n📡 Testing LLM Providers...")
    llm_status = test_llm_providers()
    for provider, available in llm_status.items():
        status = "✅ Available" if available else "❌ Not Available"
        print(f"  {provider}: {status}")
    
    # Test voice capabilities
    print("\n🎤 Testing Voice Interface...")
    voice_status = test_voice_capabilities()
    print(f"  Microphone: {'✅ Available' if voice_status['microphone_test'] else '❌ Not Available'}")
    print(f"  Speaker: {'✅ Available' if voice_status['speaker_test'] else '❌ Not Available'}")
    
    for provider, available in voice_status['providers_available'].items():
        status = "✅ Available" if available else "❌ Not Available"
        print(f"  {provider}: {status}")
    
    if voice_status['recommended_setup']:
        print("  Recommendations:")
        for rec in voice_status['recommended_setup']:
            print(f"    - {rec}")
    
    # Test options provider
    print("\n📊 Testing Options Chain Provider...")
    try:
        provider = create_options_provider("mock")
        chain = provider.get_chain("SPY", dte=30)
        if chain and "calls" in chain and "puts" in chain:
            print("  ✅ Options chain provider working")
            print(f"    - Symbol: {chain.get('symbol', 'Unknown')}")
            print(f"    - Current Price: ${chain.get('current_price', 0):.2f}")
            print(f"    - Calls available: {len(chain.get('calls', []))}")
            print(f"    - Puts available: {len(chain.get('puts', []))}")
        else:
            print("  ❌ Options chain provider issues")
    except Exception as e:
        print(f"  ❌ Options provider error: {e}")
    
    return {
        "llm_providers": llm_status,
        "voice_capabilities": voice_status,
        "system_ready": any(llm_status.values()) and voice_status.get('microphone_test', False)
    }

def demo_text_based_analysis():
    """Demo text-based trading analysis"""
    print("\n💡 Text-Based Trading Analysis Demo")
    print("-" * 40)
    
    # Initialize orchestrator
    orchestrator = LLMOrchestrator()
    synthesizer = TradeSynthesizer()
    risk_gates = RiskGates()
    
    # Sample trading requests
    requests = [
        "I think SPY is going to stay range-bound for the next month, looking for income strategies",
        "Expecting high volatility in QQQ around earnings season, want to profit from big moves",
        "Bullish on AAPL but want some downside protection, holding 500 shares",
        "Market feels toppy, want to profit from a potential pullback in SPY"
    ]
    
    for i, request in enumerate(requests, 1):
        print(f"\n{i}. Request: {request}")
        
        try:
            # Analyze intent
            analysis = orchestrator.analyze_intent(request)
            print(f"   Analysis: {analysis.outlook} outlook on {analysis.underlying}")
            print(f"   Strategy Hint: {analysis.strategy_hint}")
            print(f"   Confidence: {analysis.confidence:.1%}")
            
            # Synthesize trade
            trade_plan = synthesizer.from_analysis(analysis)
            print(f"   Trade Plan: {trade_plan.strategy_type} with {len(trade_plan.legs)} legs")
            
            # Risk validation
            from src.core.schemas import PortfolioSnapshot
            mock_portfolio = PortfolioSnapshot(
                equity=50000.0,
                risk_exposure_pct=0.05
            )
            
            violations = risk_gates.validate_trade(trade_plan, mock_portfolio)
            if violations:
                print(f"   ⚠️  Risk Violations: {len(violations)}")
                for violation in violations[:2]:  # Show first 2
                    print(f"      - {violation.code}: {violation.message}")
            else:
                print("   ✅ Risk validation passed")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def demo_voice_interface():
    """Demo voice interface if available"""
    print("\n🎤 Voice Interface Demo")
    print("-" * 30)
    
    # Get optimal voice config
    voice_config = get_optimal_voice_config()
    print(f"Voice Config: {voice_config}")
    
    if voice_config['asr_provider'] == 'text_fallback':
        print("Voice not available, using text fallback")
        
        # Initialize voice interface with text fallback
        voice = VoiceIO(
            asr_provider="text_fallback",
            tts_provider="text_fallback"
        )
        
        print("\nText-based voice simulation:")
        voice.speak("Welcome to EMO Options Bot voice interface!")
        
        command = voice.listen_once("Enter a trading command: ")
        if command:
            print(f"Received command: {command}")
            
            if voice.is_wake_word_detected(command):
                extracted = voice.extract_command(command)
                print(f"Extracted command: {extracted}")
            else:
                print("No wake word detected, processing full text")
    else:
        print("🎙️  Voice interface available!")
        print("Note: Voice demo requires microphone interaction")
        
        try:
            voice = VoiceIO(**voice_config)
            voice.speak("Voice interface test successful!")
            print("✅ Voice interface ready for use")
        except Exception as e:
            print(f"❌ Voice interface error: {e}")

def demo_complete_workflow():
    """Demo complete trading workflow"""
    print("\n🔄 Complete Trading Workflow Demo")
    print("-" * 40)
    
    # Initialize all components
    orchestrator = LLMOrchestrator()
    synthesizer = TradeSynthesizer()
    risk_gates = RiskGates()
    
    # Sample workflow
    user_input = "EMO bot, I'm bullish on SPY but want limited risk, maybe a credit spread?"
    
    print(f"User Input: {user_input}")
    
    try:
        # Step 1: Analyze intent
        print("\n1️⃣ Analyzing intent...")
        analysis = orchestrator.analyze_intent(user_input)
        print(f"   Outlook: {analysis.outlook}")
        print(f"   Underlying: {analysis.underlying}")
        print(f"   Strategy: {analysis.strategy_hint}")
        print(f"   Confidence: {analysis.confidence:.1%}")
        
        # Step 2: Synthesize trade
        print("\n2️⃣ Synthesizing trade plan...")
        trade_plan = synthesizer.from_analysis(analysis)
        print(f"   Strategy: {trade_plan.strategy_type}")
        print(f"   Legs: {len(trade_plan.legs)}")
        for i, leg in enumerate(trade_plan.legs, 1):
            print(f"     {i}. {leg.action.upper()} {leg.instrument} {leg.symbol} {leg.strike or ''} {leg.expiry or ''}")
        
        # Step 3: Risk validation
        print("\n3️⃣ Validating risk...")
        from src.core.schemas import PortfolioSnapshot
        portfolio = PortfolioSnapshot(
            equity=100000.0,
            risk_exposure_pct=0.03
        )
        
        violations = risk_gates.validate_trade(trade_plan, portfolio)
        if violations:
            print(f"   ⚠️  {len(violations)} risk violations found:")
            for violation in violations:
                print(f"     - {violation.severity.upper()}: {violation.message}")
        else:
            print("   ✅ All risk checks passed")
        
        # Step 4: Generate summary
        print("\n4️⃣ Trade Summary:")
        estimated_risk = trade_plan.estimate_max_risk()
        print(f"   Max Risk: ${estimated_risk:.0f}")
        print(f"   Risk %: {estimated_risk/portfolio.equity:.1%}")
        print(f"   Status: {'Approved' if not violations else 'Requires Review'}")
        
    except Exception as e:
        print(f"❌ Workflow error: {e}")
        logger.exception("Workflow failed")

def main():
    """Main demo function"""
    print("🤖 EMO Options Bot - Enhanced Production System Demo")
    print("=" * 60)
    
    # Test system capabilities
    capabilities = test_system_capabilities()
    
    # Run demos
    demo_text_based_analysis()
    demo_voice_interface()
    demo_complete_workflow()
    
    # Final status
    print("\n" + "=" * 60)
    print("🎯 Demo Complete!")
    
    if capabilities['system_ready']:
        print("✅ System is ready for production use")
    else:
        print("⚠️  System has limited capabilities - check provider setup")
    
    print("\nNext Steps:")
    print("1. Configure API keys for LLM providers (OPENAI_API_KEY, ANTHROPIC_API_KEY)")
    print("2. Install voice dependencies: make install-voice")
    print("3. Set up Alpaca trading credentials")
    print("4. Run production system: python main.py")

if __name__ == "__main__":
    main()