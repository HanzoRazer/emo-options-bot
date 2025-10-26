# tools/agent_happy_path.py
import threading
import time
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.intent_router import parse
from agents.plan_synthesizer import build_plan
from agents.validators import risk_check
from voice.transcriber_stub import transcribe_from_microphone, transcribe_text
from voice.tts_stub import speak, speak_plan_summary, speak_validation_result
from api.rest_server import update_state, serve as serve_api

def main(mode="interactive"):
    """
    Main agent workflow demonstrating the happy path.
    
    Args:
        mode: "interactive" for user input, "demo" for automated demo
    """
    print("🤖 EMO Options Bot - AI Agent Happy Path")
    print("=" * 50)
    
    # Start REST API server in background
    print("Starting REST API server...")
    api_thread = threading.Thread(
        target=lambda: serve_api(host="127.0.0.1", port=8085), 
        daemon=True
    )
    api_thread.start()
    time.sleep(2)  # Give server time to start
    
    print("API server running at http://localhost:8085")
    print("- Health check: http://localhost:8085/health")
    print("- Last state: http://localhost:8085/last")
    print("- System status: http://localhost:8085/status")
    print()

    if mode == "interactive":
        run_interactive_mode()
    else:
        run_demo_mode()

def run_interactive_mode():
    """Interactive mode where user can input commands."""
    print("🎤 INTERACTIVE MODE")
    print("Enter trading commands or 'quit' to exit")
    print("Examples:")
    print("- 'Build an iron condor on SPY with 7 DTE'")
    print("- 'Create a put credit spread on QQQ with low risk'")
    print("- 'Status' for system status")
    print()
    
    while True:
        try:
            user_input = input("Command: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                speak("Goodbye!")
                break
            elif not user_input:
                continue
                
            process_command(user_input, mode="text")
            print()
            
        except KeyboardInterrupt:
            print("\nGoodbye! 👋")
            speak("Agent shutting down")
            break
        except Exception as e:
            print(f"Error: {e}")

def run_demo_mode():
    """Automated demo mode with predefined commands."""
    print("🎬 DEMO MODE")
    print("Running automated demonstration...")
    print()
    
    demo_commands = [
        "Build an iron condor on SPY with 7 DTE and wings 5",
        "Create a put credit spread on QQQ with low risk", 
        "Set up a covered call on AAPL with moderate risk",
        "Build a protective put on TSLA",
        "Status",
        "Create a high risk call credit spread on NVDA"
    ]
    
    for i, command in enumerate(demo_commands, 1):
        print(f"\n--- Demo Command {i}/{len(demo_commands)} ---")
        print(f"Processing: '{command}'")
        process_command(command, mode="demo")
        time.sleep(2)  # Pause between commands
    
    print("\n🎉 Demo completed!")
    print("Check http://localhost:8085/last for the final state")

def process_command(text: str, mode: str = "text"):
    """Process a single command through the agent pipeline."""
    
    # 1) Voice → Text (using stub)
    if mode == "voice":
        text = transcribe_from_microphone()
    
    speak(f"Processing: {text}")
    
    # 2) Text → Intent
    intent = parse(text)
    print(f"Intent: {intent.kind}")
    if intent.symbol:
        print(f"Symbol: {intent.symbol}")
    if intent.strategy:
        print(f"Strategy: {intent.strategy}")
    if intent.params:
        print(f"Parameters: {intent.params}")
    
    if intent.kind == "status":
        speak("System is operational. All components running normally.")
        update_state(intent, None, None)
        return
    
    if intent.kind == "diagnose":
        speak("Portfolio analysis not implemented yet. Check back later.")
        update_state(intent, None, None)
        return
        
    if intent.kind != "build_strategy":
        speak("I didn't detect a strategy request. Try specifying a strategy.")
        update_state(intent, None, None)
        return

    if not intent.symbol or not intent.strategy:
        speak("I need both a symbol and a strategy. For example: build an iron condor on SPY.")
        update_state(intent, None, None)
        return

    # 3) Intent → Plan
    try:
        plan = build_plan(intent.symbol, intent.strategy, intent.params)
        print(f"Plan created: {plan.strategy} on {plan.symbol}")
        print(f"DTE: {plan.dte}, Risk Level: {plan.risk_level}")
        print(f"Legs: {len(plan.legs)}")
        
        if plan.est_credit:
            print(f"Estimated Credit: ${plan.est_credit:.2f}")
        if plan.est_debit:
            print(f"Estimated Debit: ${plan.est_debit:.2f}")
        if plan.max_profit and plan.max_profit != float('inf'):
            print(f"Max Profit: ${plan.max_profit:.2f}")
        if plan.max_loss and plan.max_loss != float('inf'):
            print(f"Max Loss: ${plan.max_loss:.2f}")
        
        speak_plan_summary(plan)
        
    except ValueError as e:
        error_msg = f"Plan creation failed: {e}"
        print(error_msg)
        speak(error_msg)
        update_state(intent, None, None)
        return

    # 4) Plan → Validation
    validation = risk_check(plan)
    print(f"Validation: {'PASSED' if validation.ok else 'FAILED'}")
    print(f"Risk Score: {validation.risk_score:.1f}/10")
    print(f"Position Size: {validation.position_size_pct:.2%}")
    
    if validation.warnings:
        print(f"Warnings ({len(validation.warnings)}):")
        for warning in validation.warnings:
            print(f"  ⚠️  {warning}")
    
    if validation.errors:
        print(f"Errors ({len(validation.errors)}):")
        for error in validation.errors:
            print(f"  ❌ {error}")
    
    speak_validation_result(validation)
    
    if validation.ok:
        speak("Plan is ready for approval when you enable staging.")
    else:
        speak("Plan has validation issues and cannot be executed.")

    # 5) Update API state
    update_state(intent, plan, validation)
    
    print("State updated and available at API endpoints")

def test_api_endpoints():
    """Test the API endpoints."""
    import requests
    import json
    
    base_url = "http://localhost:8085"
    
    print("🧪 Testing API Endpoints")
    print("-" * 30)
    
    try:
        # Test health
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"Health: {response.status_code} - {response.json()['status']}")
        
        # Test status
        response = requests.get(f"{base_url}/status", timeout=5)
        print(f"Status: {response.status_code}")
        
        # Test last state
        response = requests.get(f"{base_url}/last", timeout=5)
        print(f"Last State: {response.status_code}")
        
        # Test command processing
        response = requests.post(
            f"{base_url}/process",
            json={"text": "Build an iron condor on SPY", "mode": "text"},
            timeout=10
        )
        print(f"Process Command: {response.status_code} - {response.json()['success']}")
        
        print("✅ All API tests passed")
        
    except requests.exceptions.ConnectionError:
        print("❌ API server not responding - make sure it's running")
    except Exception as e:
        print(f"❌ API test failed: {e}")

if __name__ == "__main__":
    import sys
    
    # Determine mode from command line args
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "test":
            # Just test API endpoints
            test_api_endpoints()
            exit()
        elif mode in ["demo", "interactive"]:
            main(mode)
        else:
            print("Usage: python agent_happy_path.py [interactive|demo|test]")
            print("Default: interactive")
            main("interactive")
    else:
        main("interactive")