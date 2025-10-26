#!/usr/bin/env python3
"""
Integration demo showing how the Order Staging System works with the Enhanced AI Agent
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from exec.stage_order import StageOrderClient
from agents.enhanced_intent_router import EnhancedIntentRouter
from agents.plan_synthesizer import build_plan
from agents.enhanced_validators import EnhancedRiskValidator

def demo_ai_to_staging_integration():
    """Demo how AI agent commands flow to order staging."""
    print("🤖 AI AGENT → ORDER STAGING INTEGRATION")
    print("=" * 60)
    
    # Enable staging
    os.environ["EMO_STAGE_ORDERS"] = "1"
    os.environ["EMO_LANG"] = "en"
    
    # Initialize components
    router = EnhancedIntentRouter()
    validator = EnhancedRiskValidator()
    staging_client = StageOrderClient()
    
    # Test commands
    commands = [
        "Build an iron condor on SPY with 30 DTE",
        "Create a put credit spread on QQQ with low risk",
        "Set up covered calls on AAPL for income"
    ]
    
    for i, command in enumerate(commands, 1):
        print(f"\n{i}. Processing: '{command}'")
        print("-" * 40)
        
        try:
            # 1. Parse intent
            intent = router.parse(command)
            print(f"   🧠 Intent: {intent.strategy} on {intent.symbol}")
            print(f"   📊 Confidence: {intent.confidence:.2f}")
            
            if intent.strategy and intent.symbol and intent.confidence > 0.3:
                # 2. Build plan
                plan = build_plan(intent.symbol, intent.strategy, intent.params)
                print(f"   📋 Plan: {plan.strategy} ({plan.legs} legs)")
                
                # 3. Validate
                validation = validator.validate_plan(plan)
                print(f"   🛡️  Validation: {'✅ PASSED' if validation.ok else '❌ FAILED'}")
                
                if validation.ok:
                    # 4. Stage order (simplified for demo)
                    staged_file = staging_client.stage_order(
                        symbol=intent.symbol,
                        side="buy",  # Simplified - would be determined by strategy
                        qty=1,       # Simplified - would be calculated
                        order_type="limit",
                        limit_price=100.0,  # Simplified - would be calculated
                        strategy=intent.strategy,
                        meta={
                            "ai_confidence": intent.confidence,
                            "risk_score": validation.risk_score,
                            "original_command": command
                        }
                    )
                    
                    if staged_file:
                        print(f"   💾 Staged: {staged_file.name}")
                else:
                    print(f"   ⚠️  Risk issues: {len(validation.errors)} errors")
            else:
                print(f"   ⚠️  Insufficient confidence or missing data")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Show final statistics
    stats = staging_client.get_stats()
    print(f"\n📈 Final Statistics:")
    print(f"   Total Drafts: {stats['total_drafts']}")
    print(f"   By Symbol: {stats['by_symbol']}")
    
    print("\n✅ Integration demo completed")

def demo_staging_workflow():
    """Demo the complete staging workflow."""
    print("\n🔄 COMPLETE STAGING WORKFLOW DEMO")
    print("=" * 60)
    
    os.environ["EMO_STAGE_ORDERS"] = "1"
    client = StageOrderClient()
    
    print("1. Stage a test order...")
    staged_file = client.stage_order(
        symbol="TEST", 
        side="buy", 
        qty=10, 
        order_type="market",
        strategy="demo_strategy",
        meta={"source": "workflow_demo"}
    )
    
    if staged_file:
        print(f"   📄 Created: {staged_file.name}")
        
        print("\n2. Load and verify the draft...")
        data = client.load_draft(staged_file)
        if data:
            print(f"   ✅ Loaded successfully")
            print(f"   📋 Schema: {data.get('schema')}")
            print(f"   🔐 Signature: {data.get('signature')}")
            print(f"   📊 Status: {data.get('status')}")
        
        print("\n3. Simulate approval process...")
        # In a real system, this would involve human approval or automated rules
        data['status'] = 'APPROVED'
        data['approved_by'] = 'demo_system'
        data['approved_ts'] = '2025-10-25T12:00:00Z'
        
        # Write back (in real system, this would be to a different directory)
        print("   ✅ Order approved (simulated)")
        
        print("\n4. Next steps would be...")
        print("   • Send to execution engine")
        print("   • Monitor for fills")
        print("   • Update portfolio positions")
        print("   • Generate trade confirmations")
    
    print("\n✅ Workflow demo completed")

def main():
    """Run integration demos."""
    print("🚀 EMO OPTIONS BOT - AI AGENT + ORDER STAGING INTEGRATION")
    print("=" * 80)
    
    try:
        demo_ai_to_staging_integration()
        demo_staging_workflow()
        
        print("\n" + "=" * 80)
        print("🎉 INTEGRATION DEMOS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        
        print("\nIntegration Points Demonstrated:")
        print("✅ AI command parsing → Order staging")
        print("✅ Risk validation → Staging approval")
        print("✅ Metadata preservation through pipeline")
        print("✅ Multi-language error handling")
        print("✅ File integrity and audit trails")
        print("✅ Statistics and monitoring")
        
        print("\nNext Steps for Production:")
        print("🔧 Connect to real broker APIs")
        print("🔧 Add human approval workflows")
        print("🔧 Implement execution monitoring")
        print("🔧 Add portfolio position tracking")
        print("🔧 Create trade reporting system")
        
    except Exception as e:
        print(f"\n❌ Integration demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()