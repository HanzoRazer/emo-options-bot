# tools/enhanced_agent_happy_path.py
"""
Enhanced AI Agent Happy Path - More Robust Implementation
Improvements: Better error handling, logging, configuration, state management, and extensibility.
"""

import threading
import time
import sys
import logging
import json
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.intent_router import parse, Intent
from agents.plan_synthesizer import build_plan, Plan
from agents.validators import risk_check, Validation
from voice.transcriber_stub import transcribe_from_microphone, transcribe_text
from voice.tts_stub import speak, speak_plan_summary, speak_validation_result
from api.rest_server import update_state, serve as serve_api

@dataclass
class AgentConfig:
    """Configuration for the AI agent."""
    api_host: str = "127.0.0.1"
    api_port: int = 8085
    default_netliq: float = 100000.0
    max_position_pct: float = 0.02
    voice_enabled: bool = False
    log_level: str = "INFO"
    session_timeout: int = 3600  # 1 hour
    max_retries: int = 3
    command_history_limit: int = 100
    auto_save_session: bool = True
    data_dir: str = "data/agent_sessions"

@dataclass
class SessionState:
    """Enhanced session state tracking."""
    session_id: str
    start_time: datetime
    commands_processed: int = 0
    errors_count: int = 0
    last_activity: Optional[datetime] = None
    user_preferences: Dict[str, Any] = None
    command_history: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.user_preferences is None:
            self.user_preferences = {}
        if self.command_history is None:
            self.command_history = []

class EnhancedAIAgent:
    """Enhanced AI Agent with robust error handling and state management."""
    
    def __init__(self, config: AgentConfig = None):
        """Initialize the enhanced AI agent."""
        self.config = config or AgentConfig()
        self.session = self._create_session()
        self.logger = self._setup_logging()
        self.api_thread = None
        self.is_running = False
        
        # Create data directory
        Path(self.config.data_dir).mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Enhanced AI Agent initialized (session: {self.session.session_id})")
    
    def _create_session(self) -> SessionState:
        """Create a new session."""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return SessionState(
            session_id=session_id,
            start_time=datetime.now()
        )
    
    def _setup_logging(self) -> logging.Logger:
        """Setup enhanced logging."""
        logger = logging.getLogger("ai_agent")
        logger.setLevel(getattr(logging, self.config.log_level))
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler
        log_file = Path(self.config.data_dir) / f"{self.session.session_id}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def start_api_server(self) -> bool:
        """Start the REST API server with better error handling."""
        try:
            self.logger.info(f"Starting REST API server on {self.config.api_host}:{self.config.api_port}")
            
            self.api_thread = threading.Thread(
                target=lambda: serve_api(
                    host=self.config.api_host, 
                    port=self.config.api_port
                ), 
                daemon=True,
                name="APIServer"
            )
            self.api_thread.start()
            
            # Wait for server to start with timeout
            for attempt in range(10):
                time.sleep(0.5)
                if self._test_api_connection():
                    self.logger.info("API server started successfully")
                    return True
                    
            self.logger.error("API server failed to start within timeout")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to start API server: {e}")
            return False
    
    def _test_api_connection(self) -> bool:
        """Test if API server is responding."""
        try:
            import urllib.request
            with urllib.request.urlopen(
                f"http://{self.config.api_host}:{self.config.api_port}/health", 
                timeout=1
            ) as response:
                return response.status == 200
        except:
            return False
    
    def run_interactive_mode(self):
        """Enhanced interactive mode with better UX."""
        self.logger.info("Starting interactive mode")
        self.is_running = True
        
        print("🤖 Enhanced EMO Options Bot - AI Agent")
        print("=" * 60)
        print(f"Session: {self.session.session_id}")
        print(f"Log Level: {self.config.log_level}")
        print(f"Voice Enabled: {self.config.voice_enabled}")
        print("=" * 60)
        
        if not self.start_api_server():
            print("⚠️  API server failed to start - continuing without API")
        else:
            print(f"✅ API server running at http://{self.config.api_host}:{self.config.api_port}")
            print(f"   - Health: http://{self.config.api_host}:{self.config.api_port}/health")
            print(f"   - Status: http://{self.config.api_host}:{self.config.api_port}/status")
        
        print("\n🎤 ENHANCED INTERACTIVE MODE")
        print("Available commands:")
        print("  • Trading: 'Build an iron condor on SPY with 7 DTE'")
        print("  • System: 'status', 'config', 'history', 'session'")
        print("  • Control: 'help', 'clear', 'save', 'quit'")
        print("  • Voice: 'voice on/off' (if supported)")
        print()
        
        while self.is_running:
            try:
                user_input = input("📝 Command: ").strip()
                
                if not user_input:
                    continue
                    
                # Handle special commands
                if self._handle_system_command(user_input):
                    continue
                
                # Process trading command
                result = self.process_command(user_input, mode="text")
                
                if result.get("error"):
                    print(f"❌ Error: {result['error']}")
                else:
                    print(f"✅ Command processed successfully")
                
                print()
                
            except KeyboardInterrupt:
                self._shutdown_gracefully()
                break
            except EOFError:
                self._shutdown_gracefully()
                break
            except Exception as e:
                self.logger.error(f"Unexpected error in interactive mode: {e}")
                print(f"❌ Unexpected error: {e}")
                self.session.errors_count += 1
    
    def _handle_system_command(self, command: str) -> bool:
        """Handle system commands (returns True if handled)."""
        cmd = command.lower().strip()
        
        if cmd in ['quit', 'exit', 'q']:
            self._shutdown_gracefully()
            return True
            
        elif cmd == 'help':
            self._show_help()
            return True
            
        elif cmd == 'status':
            self._show_status()
            return True
            
        elif cmd == 'config':
            self._show_config()
            return True
            
        elif cmd == 'history':
            self._show_history()
            return True
            
        elif cmd == 'session':
            self._show_session_info()
            return True
            
        elif cmd == 'clear':
            self._clear_history()
            return True
            
        elif cmd == 'save':
            self._save_session()
            return True
            
        elif cmd.startswith('voice '):
            self._handle_voice_command(cmd)
            return True
            
        return False
    
    def _show_help(self):
        """Show help information."""
        help_text = """
🆘 HELP - Available Commands

Trading Commands:
  • Build an iron condor on SPY with 7 DTE
  • Create a put credit spread on QQQ with low risk
  • Set up a covered call on AAPL with moderate risk
  • Build protective puts on TSLA

System Commands:
  • status     - Show system status
  • config     - Show configuration
  • history    - Show command history
  • session    - Show session information
  • clear      - Clear command history
  • save       - Save session manually
  • voice on/off - Toggle voice mode
  • help       - Show this help
  • quit       - Exit application

Parameters:
  • DTE: 7, 14, 30 days (or "weekly", "monthly")
  • Risk: low, moderate, high
  • Wings: 5, 10 points
  • Symbols: SPY, QQQ, AAPL, MSFT, TSLA, NVDA, etc.
        """
        print(help_text)
    
    def _show_status(self):
        """Show system status."""
        api_status = "✅ Running" if self._test_api_connection() else "❌ Not responding"
        
        print(f"""
📊 SYSTEM STATUS
Session ID: {self.session.session_id}
Uptime: {datetime.now() - self.session.start_time}
Commands Processed: {self.session.commands_processed}
Errors: {self.session.errors_count}
API Server: {api_status}
Voice Mode: {'✅ Enabled' if self.config.voice_enabled else '❌ Disabled'}
Data Directory: {self.config.data_dir}
        """)
    
    def _show_config(self):
        """Show current configuration."""
        print("⚙️  CONFIGURATION")
        for key, value in asdict(self.config).items():
            print(f"  {key}: {value}")
    
    def _show_history(self):
        """Show command history."""
        history = self.session.command_history[-10:]  # Last 10 commands
        
        print(f"📜 COMMAND HISTORY (last {len(history)} commands)")
        for i, cmd in enumerate(history, 1):
            timestamp = cmd.get('timestamp', 'unknown')
            command = cmd.get('command', 'unknown')
            status = cmd.get('status', 'unknown')
            print(f"  {i}. [{timestamp}] {command} - {status}")
    
    def _show_session_info(self):
        """Show detailed session information."""
        print(f"""
📋 SESSION INFORMATION
ID: {self.session.session_id}
Started: {self.session.start_time}
Last Activity: {self.session.last_activity or 'None'}
Commands: {self.session.commands_processed}
Errors: {self.session.errors_count}
History Length: {len(self.session.command_history)}
User Preferences: {self.session.user_preferences}
        """)
    
    def _clear_history(self):
        """Clear command history."""
        self.session.command_history.clear()
        print("✅ Command history cleared")
    
    def _save_session(self):
        """Manually save session."""
        if self._save_session_to_file():
            print("✅ Session saved successfully")
        else:
            print("❌ Failed to save session")
    
    def _handle_voice_command(self, cmd: str):
        """Handle voice commands."""
        if "on" in cmd:
            self.config.voice_enabled = True
            print("🔊 Voice mode enabled")
        elif "off" in cmd:
            self.config.voice_enabled = False
            print("🔇 Voice mode disabled")
        else:
            print("Use 'voice on' or 'voice off'")
    
    def process_command(self, text: str, mode: str = "text") -> Dict[str, Any]:
        """Enhanced command processing with comprehensive error handling."""
        start_time = datetime.now()
        
        try:
            self.logger.info(f"Processing command: {text}")
            
            # Update session
            self.session.last_activity = start_time
            self.session.commands_processed += 1
            
            # Voice processing
            if mode == "voice" and self.config.voice_enabled:
                try:
                    text = transcribe_from_microphone()
                    self.logger.info(f"Voice transcription: {text}")
                except Exception as e:
                    self.logger.error(f"Voice transcription failed: {e}")
                    return {"error": f"Voice transcription failed: {e}"}
            
            if self.config.voice_enabled:
                speak(f"Processing: {text}")
            
            # Parse intent with retries
            intent = None
            for attempt in range(self.config.max_retries):
                try:
                    intent = parse(text)
                    break
                except Exception as e:
                    self.logger.warning(f"Intent parsing attempt {attempt + 1} failed: {e}")
                    if attempt == self.config.max_retries - 1:
                        raise
            
            self.logger.info(f"Parsed intent: {intent}")
            
            # Handle different intent types
            result = self._process_intent(intent, text, mode)
            
            # Add to command history
            self._add_to_history(text, intent, result, start_time)
            
            # Auto-save session if enabled
            if self.config.auto_save_session:
                self._save_session_to_file()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Command processing failed: {e}")
            self.logger.error(traceback.format_exc())
            
            self.session.errors_count += 1
            error_result = {
                "error": str(e),
                "timestamp": start_time.isoformat(),
                "command": text
            }
            
            self._add_to_history(text, None, error_result, start_time)
            
            if self.config.voice_enabled:
                speak(f"Sorry, I encountered an error: {e}")
            
            return error_result
    
    def _process_intent(self, intent: Intent, original_text: str, mode: str) -> Dict[str, Any]:
        """Process different types of intents."""
        
        if intent.kind == "status":
            self._show_status()
            if self.config.voice_enabled:
                speak("System is operational. All components running normally.")
            update_state(intent, None, None)
            return {"status": "success", "intent": intent, "message": "Status displayed"}
        
        if intent.kind == "diagnose":
            message = "Portfolio analysis not implemented yet. Check back later."
            if self.config.voice_enabled:
                speak(message)
            update_state(intent, None, None)
            return {"status": "info", "intent": intent, "message": message}
        
        if intent.kind == "unknown":
            message = "I didn't understand that command. Try 'help' for available commands."
            if self.config.voice_enabled:
                speak(message)
            return {"status": "warning", "intent": intent, "message": message}
            
        if intent.kind != "build_strategy":
            message = "I didn't detect a strategy request. Try specifying a strategy."
            if self.config.voice_enabled:
                speak(message)
            update_state(intent, None, None)
            return {"status": "warning", "intent": intent, "message": message}

        if not intent.symbol or not intent.strategy:
            message = "I need both a symbol and a strategy. For example: build an iron condor on SPY."
            if self.config.voice_enabled:
                speak(message)
            update_state(intent, None, None)
            return {"status": "error", "intent": intent, "message": message}

        # Build and validate plan
        return self._build_and_validate_plan(intent)
    
    def _build_and_validate_plan(self, intent: Intent) -> Dict[str, Any]:
        """Build and validate trading plan with enhanced error handling."""
        
        try:
            # Build plan
            plan = build_plan(intent.symbol, intent.strategy, intent.params)
            self.logger.info(f"Plan created: {plan.strategy} on {plan.symbol}")
            
            # Enhanced plan info display
            print(f"📋 Plan Created: {plan.strategy.replace('_', ' ').title()} on {plan.symbol}")
            print(f"   DTE: {plan.dte}, Risk Level: {plan.risk_level.title()}")
            print(f"   Legs: {len(plan.legs)}")
            
            if plan.est_credit:
                print(f"   Estimated Credit: ${plan.est_credit:.2f}")
            if plan.est_debit:
                print(f"   Estimated Debit: ${plan.est_debit:.2f}")
            if plan.max_profit and plan.max_profit != float('inf'):
                print(f"   Max Profit: ${plan.max_profit:.2f}")
            if plan.max_loss and plan.max_loss != float('inf'):
                print(f"   Max Loss: ${plan.max_loss:.2f}")
            
            if self.config.voice_enabled:
                speak_plan_summary(plan)
            
        except ValueError as e:
            error_msg = f"Plan creation failed: {e}"
            self.logger.error(error_msg)
            if self.config.voice_enabled:
                speak(error_msg)
            update_state(intent, None, None)
            return {"status": "error", "intent": intent, "message": error_msg}

        # Validate plan
        try:
            validation = risk_check(plan, self.config.default_netliq, self.config.max_position_pct)
            self.logger.info(f"Validation completed: {'PASSED' if validation.ok else 'FAILED'}")
            
            # Enhanced validation display
            print(f"🛡️  Validation: {'✅ PASSED' if validation.ok else '❌ FAILED'}")
            print(f"   Risk Score: {validation.risk_score:.1f}/10")
            print(f"   Position Size: {validation.position_size_pct:.2%}")
            
            if validation.warnings:
                print(f"   ⚠️  Warnings ({len(validation.warnings)}):")
                for warning in validation.warnings[:3]:  # Show top 3
                    print(f"      • {warning}")
            
            if validation.errors:
                print(f"   ❌ Errors ({len(validation.errors)}):")
                for error in validation.errors[:3]:  # Show top 3
                    print(f"      • {error}")
            
            if self.config.voice_enabled:
                speak_validation_result(validation)
            
            if validation.ok:
                message = "Plan is ready for approval when you enable staging."
                if self.config.voice_enabled:
                    speak(message)
            else:
                message = "Plan has validation issues and cannot be executed."
                if self.config.voice_enabled:
                    speak(message)

            # Update API state
            update_state(intent, plan, validation)
            
            return {
                "status": "success" if validation.ok else "validation_failed",
                "intent": intent,
                "plan": plan,
                "validation": validation,
                "message": message
            }
            
        except Exception as e:
            error_msg = f"Plan validation failed: {e}"
            self.logger.error(error_msg)
            if self.config.voice_enabled:
                speak(error_msg)
            return {"status": "error", "intent": intent, "plan": plan, "message": error_msg}
    
    def _add_to_history(self, command: str, intent: Optional[Intent], result: Dict[str, Any], timestamp: datetime):
        """Add command to session history."""
        entry = {
            "timestamp": timestamp.isoformat(),
            "command": command,
            "intent": asdict(intent) if intent else None,
            "status": result.get("status", "unknown"),
            "message": result.get("message", ""),
            "processing_time": (datetime.now() - timestamp).total_seconds()
        }
        
        self.session.command_history.append(entry)
        
        # Limit history size
        if len(self.session.command_history) > self.config.command_history_limit:
            self.session.command_history = self.session.command_history[-self.config.command_history_limit:]
    
    def _save_session_to_file(self) -> bool:
        """Save session state to file."""
        try:
            session_file = Path(self.config.data_dir) / f"{self.session.session_id}.json"
            
            session_data = {
                "session": asdict(self.session),
                "config": asdict(self.config),
                "saved_at": datetime.now().isoformat()
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)
            
            self.logger.info(f"Session saved to {session_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save session: {e}")
            return False
    
    def _shutdown_gracefully(self):
        """Shutdown the agent gracefully."""
        self.logger.info("Shutting down agent gracefully")
        self.is_running = False
        
        if self.config.auto_save_session:
            self._save_session_to_file()
        
        print("\n👋 Goodbye! Session data saved.")
        if self.config.voice_enabled:
            speak("Agent shutting down. Goodbye!")

def create_config_from_args() -> AgentConfig:
    """Create configuration from command line arguments."""
    parser = argparse.ArgumentParser(description="Enhanced AI Trading Agent")
    parser.add_argument("--host", default="127.0.0.1", help="API server host")
    parser.add_argument("--port", type=int, default=8085, help="API server port")
    parser.add_argument("--netliq", type=float, default=100000.0, help="Default net liquidation value")
    parser.add_argument("--max-pos", type=float, default=0.02, help="Maximum position percentage")
    parser.add_argument("--voice", action="store_true", help="Enable voice mode")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--data-dir", default="data/agent_sessions", help="Data directory")
    
    args = parser.parse_args()
    
    return AgentConfig(
        api_host=args.host,
        api_port=args.port,
        default_netliq=args.netliq,
        max_position_pct=args.max_pos,
        voice_enabled=args.voice,
        log_level=args.log_level,
        data_dir=args.data_dir
    )

def main():
    """Main entry point for enhanced agent."""
    try:
        config = create_config_from_args()
        agent = EnhancedAIAgent(config)
        agent.run_interactive_mode()
    except KeyboardInterrupt:
        print("\n👋 Agent interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        logging.error(f"Fatal error: {e}")
        logging.error(traceback.format_exc())

if __name__ == "__main__":
    main()