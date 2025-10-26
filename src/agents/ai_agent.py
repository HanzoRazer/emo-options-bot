"""
AI Trading Agent - Main Orchestrator for Voice-Driven Trading
Coordinates all agent components: NLU, Planning, Validation, Approval, Voice.
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import json
from pathlib import Path
import uuid

from .nlu_router import NLURouter
from .planner import TradingPlanner
from .approval_flow import ApprovalFlow, ApprovalAction
from .voice_interface import VoiceInterface, VoiceCommandProcessor
from ..logic.risk_manager import PortfolioSnapshot

class AITradingAgent:
    """Main AI agent orchestrating voice-driven trading workflow."""
    
    def __init__(
        self, 
        data_dir: Optional[Path] = None,
        voice_enabled: bool = True,
        auto_approve_safe_trades: bool = False
    ):
        """
        Initialize the AI trading agent.
        
        Args:
            data_dir: Directory for saving agent data
            voice_enabled: Enable voice interface
            auto_approve_safe_trades: Auto-approve very safe trades
        """
        self.data_dir = data_dir or Path("data/agent")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize core components
        self.nlu_router = NLURouter()
        self.planner = TradingPlanner(self.data_dir / "plans")
        self.approval_flow = ApprovalFlow(approval_callback=self._on_approval_decision)
        self.voice_interface = VoiceInterface(voice_enabled)
        
        # Configuration
        self.auto_approve_safe = auto_approve_safe_trades
        self.session_id = str(uuid.uuid4())[:8]
        
        # State tracking
        self.conversation_history: List[Dict[str, Any]] = []
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        print(f"[Agent] AI Trading Agent initialized (session: {self.session_id})")
        print(f"[Agent] Voice enabled: {voice_enabled}")
        print(f"[Agent] Auto-approve safe trades: {auto_approve_safe_trades}")
    
    def process_user_input(
        self, 
        user_input: str, 
        input_mode: str = "text",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for processing user trading requests.
        
        Args:
            user_input: User's trading request (voice or text)
            input_mode: "voice" or "text"
            context: Additional context
            
        Returns:
            Complete response with plan, status, explanation
        """
        request_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now()
        
        print(f"[Agent] Processing {input_mode} input: '{user_input}' (ID: {request_id})")
        
        try:
            # Step 1: Parse natural language to structured intent
            intent = self.nlu_router.parse_free_text(user_input)
            intent["request_id"] = request_id
            intent["input_mode"] = input_mode
            
            print(f"[Agent] Parsed intent: {intent.get('user_goal', 'unknown')}")
            
            # Step 2: Create market context
            symbol = intent.get("symbol", "SPY")
            market_ctx = self.planner.create_market_context(symbol)
            
            # Step 3: Build and validate trading plan
            plan, validation_errors = self.planner.build_and_validate(
                intent, 
                market_ctx, 
                portfolio=None  # TODO: Integrate with actual portfolio
            )
            
            # Step 4: Determine next action based on validation
            if validation_errors:
                # Plan failed validation
                response = self._handle_validation_failure(plan, validation_errors, user_input)
            else:
                # Plan passed validation - submit for approval
                response = self._handle_successful_plan(plan, user_input, intent)
            
            # Step 5: Store conversation
            conversation_entry = {
                "request_id": request_id,
                "timestamp": timestamp.isoformat(),
                "user_input": user_input,
                "input_mode": input_mode,
                "intent": intent,
                "plan": plan,
                "validation_errors": validation_errors,
                "response": response,
                "session_id": self.session_id
            }
            
            self.conversation_history.append(conversation_entry)
            
            # Step 6: Handle voice response
            if input_mode == "voice" and response.get("speak_response"):
                self.voice_interface.speak_response(response["explanation"])
            
            return response
            
        except Exception as e:
            error_response = {
                "status": "error",
                "error": str(e),
                "explanation": f"I encountered an error processing your request: {e}",
                "request_id": request_id,
                "timestamp": timestamp.isoformat(),
                "speak_response": input_mode == "voice"
            }
            
            print(f"[Agent] Error processing input: {e}")
            
            if input_mode == "voice":
                self.voice_interface.speak_response(error_response["explanation"])
            
            return error_response
    
    def _handle_validation_failure(
        self, 
        plan: Dict[str, Any], 
        errors: List[str], 
        user_input: str
    ) -> Dict[str, Any]:
        """Handle a plan that failed validation."""
        
        explanation = f"I can't execute this request due to {len(errors)} risk concern{'s' if len(errors) > 1 else ''}:"
        for i, error in enumerate(errors[:3], 1):  # Show top 3 errors
            explanation += f" {i}) {error}."
        
        if len(errors) > 3:
            explanation += f" Plus {len(errors) - 3} other issues."
        
        explanation += " Please modify your request or adjust risk parameters."
        
        return {
            "status": "rejected",
            "plan": plan,
            "validation_errors": errors,
            "explanation": explanation,
            "request_id": plan.get("request_id"),
            "timestamp": datetime.now().isoformat(),
            "speak_response": True,
            "suggestions": self._generate_error_suggestions(errors)
        }
    
    def _handle_successful_plan(
        self, 
        plan: Dict[str, Any], 
        user_input: str, 
        intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle a plan that passed validation."""
        
        explanation = self.planner.explain_plan(plan)
        
        # Submit for approval
        approval_request = self.approval_flow.submit_for_approval(
            plan, 
            user_input, 
            explanation
        )
        
        # Check for auto-approval
        auto_approved = False
        if self.auto_approve_safe:
            auto_approved = self.approval_flow.auto_approve_if_criteria_met(plan["request_id"])
        
        if auto_approved:
            status = "approved"
            explanation += " This trade meets safety criteria and has been automatically approved."
        else:
            status = "pending_approval"
            explanation += " This plan requires your approval before execution."
        
        return {
            "status": status,
            "plan": plan,
            "approval_request": approval_request.to_dict(),
            "explanation": explanation,
            "auto_approved": auto_approved,
            "request_id": plan.get("request_id"),
            "timestamp": datetime.now().isoformat(),
            "speak_response": True,
            "requires_approval": not auto_approved
        }
    
    def _generate_error_suggestions(self, errors: List[str]) -> List[str]:
        """Generate helpful suggestions based on validation errors."""
        
        suggestions = []
        
        for error in errors:
            if "risk" in error.lower():
                suggestions.append("Try requesting a lower risk level or smaller position size")
            elif "strategy" in error.lower():
                suggestions.append("Consider a different options strategy")
            elif "expiry" in error.lower():
                suggestions.append("Try a different expiration date")
            elif "symbol" in error.lower():
                suggestions.append("Check the symbol and try again")
        
        if not suggestions:
            suggestions.append("Try rephrasing your request with more specific parameters")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _on_approval_decision(self, response) -> None:
        """Callback for approval decisions."""
        
        print(f"[Agent] Approval decision: {response.action.value} for plan {response.plan_id}")
        
        if response.action == ApprovalAction.APPROVE:
            print(f"[Agent] Plan approved: {response.user_comments}")
            # TODO: Integrate with execution system
        elif response.action == ApprovalAction.REJECT:
            print(f"[Agent] Plan rejected: {response.user_comments}")
        elif response.action == ApprovalAction.MODIFY:
            print(f"[Agent] Modifications requested: {response.user_comments}")
    
    def handle_approval_response(
        self, 
        plan_id: str, 
        action: str, 
        comments: str = "",
        modifications: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle user's approval response.
        
        Args:
            plan_id: Plan being responded to
            action: "approve", "reject", "modify", or "defer"
            comments: User comments
            modifications: Requested changes
            
        Returns:
            Response status
        """
        try:
            approval_action = ApprovalAction(action)
            
            response = self.approval_flow.process_approval(
                plan_id, 
                approval_action, 
                comments, 
                modifications
            )
            
            return {
                "status": "success",
                "action": action,
                "plan_id": plan_id,
                "response": response.to_dict(),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "plan_id": plan_id,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all plans awaiting approval."""
        
        pending = self.approval_flow.get_pending_approvals()
        
        return [
            self.approval_flow.get_approval_summary(req.plan_id) 
            for req in pending
        ]
    
    def start_voice_assistant(self, wake_word: str = "trading assistant") -> None:
        """Start the voice assistant interface."""
        
        print(f"[Agent] Starting voice assistant with wake word: '{wake_word}'")
        
        def process_voice_command(command: str) -> Dict[str, Any]:
            """Process voice commands through the agent."""
            return self.process_user_input(command, input_mode="voice")
        
        # Create voice processor
        voice_processor = VoiceCommandProcessor(process_voice_command)
        
        # Start listening
        voice_processor.start_voice_assistant(wake_word)
    
    def get_conversation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation history."""
        return self.conversation_history[-limit:] if self.conversation_history else []
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get current agent status and statistics."""
        
        return {
            "session_id": self.session_id,
            "uptime": datetime.now().isoformat(),
            "conversation_count": len(self.conversation_history),
            "pending_approvals": len(self.approval_flow.get_pending_approvals()),
            "voice_enabled": self.voice_interface.voice_enabled,
            "auto_approve_enabled": self.auto_approve_safe,
            "approval_stats": self.approval_flow.get_approval_stats(),
            "components_status": {
                "nlu_router": "active",
                "planner": "active", 
                "approval_flow": "active",
                "voice_interface": "active" if self.voice_interface.voice_enabled else "disabled"
            }
        }
    
    def save_session_data(self) -> Path:
        """Save session data to disk."""
        
        session_data = {
            "session_id": self.session_id,
            "conversation_history": self.conversation_history,
            "agent_config": {
                "voice_enabled": self.voice_interface.voice_enabled,
                "auto_approve_safe": self.auto_approve_safe
            },
            "saved_at": datetime.now().isoformat()
        }
        
        session_file = self.data_dir / f"session_{self.session_id}.json"
        
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)
        
        print(f"[Agent] Session data saved to: {session_file}")
        return session_file
    
    def create_demo_conversation(self) -> List[Dict[str, Any]]:
        """Create a demonstration conversation for testing."""
        
        demo_commands = [
            "Generate low risk income from SPY this month",
            "Create a bullish strategy on QQQ with moderate risk", 
            "Set up protective puts for my portfolio",
            "Build an iron condor on Apple with high probability of profit"
        ]
        
        demo_results = []
        
        for command in demo_commands:
            print(f"\n[Demo] Processing: '{command}'")
            result = self.process_user_input(command, input_mode="text")
            demo_results.append(result)
        
        return demo_results


# Convenience functions for easy usage
def create_ai_agent(voice_enabled: bool = True, auto_approve: bool = False) -> AITradingAgent:
    """Create an AI trading agent instance."""
    return AITradingAgent(
        voice_enabled=voice_enabled,
        auto_approve_safe_trades=auto_approve
    )

def start_voice_trading_assistant(wake_word: str = "trading assistant") -> None:
    """Start the voice trading assistant."""
    agent = create_ai_agent(voice_enabled=True, auto_approve=True)
    agent.start_voice_assistant(wake_word)

if __name__ == "__main__":
    # Demo mode
    print("Starting AI Trading Agent Demo...")
    
    agent = create_ai_agent(voice_enabled=False, auto_approve=True)
    
    # Run demo conversation
    demo_results = agent.create_demo_conversation()
    
    print(f"\n[Demo] Completed {len(demo_results)} demo requests")
    print(f"[Demo] Agent status: {agent.get_agent_status()}")
    
    # Save session
    session_file = agent.save_session_data()
    print(f"[Demo] Session saved to: {session_file}")