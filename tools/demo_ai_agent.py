"""
AI Trading Agent Demo
Comprehensive demonstration of the voice-driven AI trading assistant.
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agents import AITradingAgent, ApprovalAction

class TradingAgentDemo:
    """Demonstration of the AI Trading Agent capabilities."""
    
    def __init__(self):
        """Initialize the demo."""
        self.agent = AITradingAgent(
            data_dir=Path("demo_data"),
            voice_enabled=False,  # Disable voice for demo
            auto_approve_safe_trades=False  # Manual approval for demo
        )
        
        print("="*70)
        print("🤖 AI TRADING AGENT DEMO")
        print("="*70)
        print("Voice-driven AI trading assistant with natural language understanding")
        print()
    
    def run_complete_demo(self):
        """Run the complete demonstration."""
        
        print("📋 DEMO OVERVIEW")
        print("-" * 50)
        print("This demo showcases:")
        print("• Natural language trading command processing")
        print("• Intent parsing and strategy translation")
        print("• Risk validation and approval workflow")
        print("• Complete audit trail and session management")
        print()
        
        # Demo 1: Basic trading commands
        self.demo_basic_commands()
        
        # Demo 2: Risk validation
        self.demo_risk_validation()
        
        # Demo 3: Approval workflow
        self.demo_approval_workflow()
        
        # Demo 4: Agent status and history
        self.demo_agent_status()
        
        print("="*70)
        print("✅ DEMO COMPLETED SUCCESSFULLY")
        print("="*70)
        print("The AI Trading Agent is ready for production use!")
        print()
    
    def demo_basic_commands(self):
        """Demonstrate basic trading command processing."""
        
        print("🗣️  DEMO 1: NATURAL LANGUAGE COMMANDS")
        print("-" * 50)
        
        commands = [
            "Generate low risk income from SPY this month",
            "Create a bullish strategy on QQQ with moderate risk",
            "Build an iron condor on Apple with high probability of profit",
            "Set up protective puts for my Tesla position"
        ]
        
        for i, command in enumerate(commands, 1):
            print(f"\n{i}. Processing: '{command}'")
            print("   " + "─" * 60)
            
            result = self.agent.process_user_input(command)
            
            print(f"   Status: {result['status'].upper()}")
            print(f"   Strategy: {result.get('plan', {}).get('strategy', 'N/A')}")
            print(f"   Symbol: {result.get('plan', {}).get('symbol', 'N/A')}")
            print(f"   Risk Level: {result.get('plan', {}).get('risk_level', 'N/A')}")
            
            if result.get('validation_errors'):
                print(f"   ⚠️  Validation Issues: {len(result['validation_errors'])}")
            else:
                print("   ✅ Passed Validation")
        
        print()
    
    def demo_risk_validation(self):
        """Demonstrate risk validation system."""
        
        print("🛡️  DEMO 2: RISK VALIDATION SYSTEM")
        print("-" * 50)
        
        # Test risky commands that should be rejected
        risky_commands = [
            "Put my entire portfolio in high risk TSLA options",
            "Create a naked call strategy with unlimited risk",
            "Trade options expiring tomorrow with maximum leverage"
        ]
        
        for i, command in enumerate(risky_commands, 1):
            print(f"\n{i}. Testing Risky Command: '{command}'")
            print("   " + "─" * 60)
            
            result = self.agent.process_user_input(command)
            
            if result['status'] == 'rejected':
                print("   ❌ CORRECTLY REJECTED")
                errors = result.get('validation_errors', [])
                print(f"   Risk Issues Found: {len(errors)}")
                for error in errors[:2]:  # Show top 2 errors
                    print(f"   • {error}")
            else:
                print("   ⚠️  UNEXPECTEDLY APPROVED (Risk system needs tuning)")
        
        print()
    
    def demo_approval_workflow(self):
        """Demonstrate the approval workflow."""
        
        print("✋ DEMO 3: APPROVAL WORKFLOW")
        print("-" * 50)
        
        # Generate a plan that needs approval
        command = "Create a covered call strategy on SPY with low risk"
        print(f"Creating plan: '{command}'")
        result = self.agent.process_user_input(command)
        
        if result['status'] == 'pending_approval':
            plan_id = result['request_id']
            print(f"✅ Plan created and pending approval (ID: {plan_id})")
            
            # Show pending approvals
            pending = self.agent.get_pending_approvals()
            print(f"\n📋 Pending Approvals: {len(pending)}")
            
            if pending:
                approval = pending[0]
                print(f"   Plan: {approval['strategy']} on {approval['symbol']}")
                print(f"   Risk: {approval['risk_level']} ({approval['max_loss_pct']:.1%} max loss)")
                print(f"   Return: {approval['estimated_return']:.1%}")
                
                # Demonstrate approval
                print(f"\n👍 Approving plan {plan_id}...")
                approval_result = self.agent.handle_approval_response(
                    plan_id, 
                    "approve", 
                    "Demo approval - looks good!"
                )
                
                if approval_result['status'] == 'success':
                    print("   ✅ Plan approved successfully!")
                else:
                    print(f"   ❌ Approval failed: {approval_result.get('error')}")
        else:
            print(f"   Plan status: {result['status']}")
        
        print()
    
    def demo_agent_status(self):
        """Demonstrate agent status and history tracking."""
        
        print("📊 DEMO 4: AGENT STATUS & HISTORY")
        print("-" * 50)
        
        # Get agent status
        status = self.agent.get_agent_status()
        print("Agent Status:")
        print(f"   Session ID: {status['session_id']}")
        print(f"   Commands Processed: {status['conversation_count']}")
        print(f"   Pending Approvals: {status['pending_approvals']}")
        print(f"   Voice Enabled: {status['voice_enabled']}")
        print(f"   Auto-Approve: {status['auto_approve_enabled']}")
        
        # Get conversation history
        history = self.agent.get_conversation_history()
        print(f"\n📝 Recent Conversation History ({len(history)} entries):")
        
        for i, entry in enumerate(history[-3:], 1):  # Show last 3
            print(f"   {i}. '{entry['user_input'][:50]}...'")
            print(f"      Status: {entry['response']['status']}")
            print(f"      Time: {entry['timestamp']}")
        
        # Save session data
        print(f"\n💾 Saving session data...")
        session_file = self.agent.save_session_data()
        print(f"   Session saved to: {session_file}")
        
        print()
    
    def demo_voice_capabilities(self):
        """Demonstrate voice interface capabilities (if available)."""
        
        print("🎤 VOICE INTERFACE CAPABILITIES")
        print("-" * 50)
        
        voice_info = self.agent.voice_interface.get_voice_info()
        
        print("Voice System Status:")
        print(f"   Libraries Available: {voice_info['libraries_available']}")
        print(f"   Voice Enabled: {voice_info['voice_enabled']}")
        
        if voice_info['voice_enabled']:
            print(f"   Available Voices: {voice_info.get('available_voices', 'Unknown')}")
            print(f"   Speech Rate: {voice_info.get('current_rate', 'Unknown')}")
            print(f"   Volume: {voice_info.get('current_volume', 'Unknown')}")
            
            # Test voice system
            print("\n🧪 Testing voice system...")
            test_results = self.agent.voice_interface.test_voice_system()
            
            for test, passed in test_results.items():
                status = "✅ PASS" if passed else "❌ FAIL"
                print(f"   {test.replace('_', ' ').title()}: {status}")
        else:
            print("   Voice system not available")
            print("   Install requirements: pip install SpeechRecognition pyttsx3")
        
        print()


def run_interactive_demo():
    """Run an interactive demo where user can test commands."""
    
    print("🎮 INTERACTIVE MODE")
    print("-" * 50)
    print("Enter trading commands to test the AI agent.")
    print("Type 'quit' to exit, 'status' for agent info, 'pending' for approvals.")
    print()
    
    agent = AITradingAgent(voice_enabled=False, auto_approve_safe_trades=False)
    
    while True:
        try:
            user_input = input("Trading Command: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 👋")
                break
            elif user_input.lower() == 'status':
                status = agent.get_agent_status()
                print(f"Status: {json.dumps(status, indent=2)}")
                continue
            elif user_input.lower() == 'pending':
                pending = agent.get_pending_approvals()
                print(f"Pending Approvals: {len(pending)}")
                for approval in pending:
                    print(f"  • {approval['plan_id']}: {approval['strategy']} on {approval['symbol']}")
                continue
            elif not user_input:
                continue
            
            # Process command
            result = agent.process_user_input(user_input)
            
            print(f"Result: {result['status'].upper()}")
            print(f"Explanation: {result['explanation']}")
            
            if result.get('requires_approval'):
                plan_id = result['request_id']
                approve = input(f"Approve plan {plan_id}? (y/n): ").lower().startswith('y')
                
                if approve:
                    agent.handle_approval_response(plan_id, "approve", "User approved in interactive mode")
                    print("✅ Plan approved!")
                else:
                    agent.handle_approval_response(plan_id, "reject", "User rejected in interactive mode")
                    print("❌ Plan rejected!")
            
            print()
            
        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    """Run the demo based on command line arguments."""
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        run_interactive_demo()
    else:
        demo = TradingAgentDemo()
        demo.run_complete_demo()
        
        print("To run interactive mode: python demo_ai_agent.py interactive")
        print("To start voice assistant: python -m agents.ai_agent")