"""
Phase 3 Integration Hub - LLM + Voice + Risk-Aware Trading
Orchestrates the complete flow from voice input to trade execution.
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

# Phase 3 Components
from llm.orchestrator import LLMOrchestrator
from llm.schemas import TradePlan, StrategySpec, RiskMetrics
from planner.synthesizer import TradeSynthesizer, MarketData, OptionChain
from risk.gates import RiskGate, PortfolioMetrics, RiskViolation

# Voice Interface
try:
    from voice.asr_tts import VoiceInterface, VoiceConfig
    VOICE_AVAILABLE = True
except ImportError:
    from voice.mock_interface import MockVoiceInterface
    VOICE_AVAILABLE = False

# I18n and Order Staging
from i18n.lang import TranslationManager
from exec.stage_order import StageOrderClient

logger = logging.getLogger(__name__)

class Phase3TradingSystem:
    """
    Complete Phase 3 trading system integrating:
    - LLM-powered trade analysis
    - Voice I/O for hands-free operation
    - Risk gates for safety
    - Order staging for validation
    - Multi-language support
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        
        # Initialize core components
        self.llm_orchestrator = LLMOrchestrator()
        self.trade_synthesizer = TradeSynthesizer(self.llm_orchestrator)
        self.risk_gate = RiskGate()
        self.translation_manager = TranslationManager()
        self.stage_order_client = StageOrderClient()
        
        # Initialize voice interface
        if VOICE_AVAILABLE:
            voice_config = VoiceConfig()
            self.voice = VoiceInterface(voice_config)
        else:
            self.voice = MockVoiceInterface()
        
        # Register voice command handlers
        self._register_voice_handlers()
        
        # System state
        self.is_active = False
        self.current_language = "en"
        self.session_id = f"session_{int(datetime.now().timestamp())}"
        
        logger.info("Phase 3 Trading System initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load system configuration"""
        default_config = {
            "account_equity": 100000,
            "default_language": "en",
            "voice_enabled": True,
            "paper_trading": True,
            "risk_management": {
                "max_daily_trades": 10,
                "max_position_size": 25,
                "require_voice_confirmation": True
            },
            "llm_provider": "openai",  # or "mock"
            "market_data_source": "mock"  # In production: "ib", "td", etc.
        }
        
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    custom_config = json.load(f)
                default_config.update(custom_config)
            except Exception as e:
                logger.warning(f"Could not load config: {e}")
        
        return default_config
    
    def _register_voice_handlers(self):
        """Register voice command handlers"""
        self.voice.register_command_handler("buy", self._handle_buy_command)
        self.voice.register_command_handler("sell", self._handle_sell_command)
        self.voice.register_command_handler("status", self._handle_status_command)
        self.voice.register_command_handler("help", self._handle_help_command)
        self.voice.register_command_handler("close", self._handle_close_command)
    
    async def start_system(self) -> bool:
        """Start the complete Phase 3 system"""
        try:
            # Start voice interface
            if self.config["voice_enabled"]:
                voice_started = self.voice.start()
                if voice_started:
                    logger.info("Voice interface started")
                else:
                    logger.warning("Voice interface failed to start")
            
            self.is_active = True
            
            # Welcome message
            welcome_msg = self.translation_manager.get_text(
                "system.welcome", 
                self.current_language
            )
            self.voice.speak(welcome_msg)
            
            logger.info("Phase 3 Trading System is active")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start system: {e}")
            return False
    
    def stop_system(self):
        """Stop the system gracefully"""
        self.is_active = False
        
        if self.voice:
            self.voice.stop()
        
        # Close any pending orders
        try:
            pending_orders = self.stage_order_client.list_orders(status="pending")
            for order in pending_orders:
                self.stage_order_client.cancel_order(order["id"])
        except Exception as e:
            logger.warning(f"Error closing pending orders: {e}")
        
        goodbye_msg = self.translation_manager.get_text(
            "system.goodbye", 
            self.current_language
        )
        logger.info(goodbye_msg)
    
    async def process_natural_language_request(self, 
                                             request: str, 
                                             voice_input: bool = False) -> Dict:
        """
        Process natural language trading request through complete pipeline:
        1. LLM Analysis -> 2. Trade Synthesis -> 3. Risk Gates -> 4. Order Staging
        """
        try:
            logger.info(f"Processing request: {request}")
            
            # Step 1: LLM Analysis
            self.voice.speak("Analyzing your request...")
            
            trade_plan = await self.llm_orchestrator.plan_trade(request)
            
            if not trade_plan:
                error_msg = self.translation_manager.get_text(
                    "errors.analysis_failed", 
                    self.current_language
                )
                self.voice.speak(error_msg)
                return {"success": False, "error": "LLM analysis failed"}
            
            # Step 2: Get Market Data (mock for now)
            market_data = await self._get_market_data(trade_plan.strategy.symbol)
            option_chains = await self._get_option_chains(trade_plan.strategy.symbol)
            
            # Step 3: Trade Synthesis
            self.voice.speak("Calculating optimal trade structure...")
            
            executable_trade = self.trade_synthesizer.synthesize_trade(
                trade_plan,
                market_data,
                option_chains,
                self.config["account_equity"]
            )
            
            # Step 4: Risk Gate Validation
            portfolio_metrics = await self._get_portfolio_metrics()
            
            is_valid, violations = self.risk_gate.validate_trade(
                executable_trade,
                portfolio_metrics,
                self.config["account_equity"]
            )
            
            if not is_valid:
                violation_msg = self._format_risk_violations(violations)
                self.voice.speak(f"Trade rejected due to risk violations: {violation_msg}")
                return {
                    "success": False,
                    "error": "Risk gate violations",
                    "violations": [v.__dict__ for v in violations]
                }
            
            # Step 5: Voice Confirmation (if required)
            if voice_input and self.config["risk_management"]["require_voice_confirmation"]:
                confirmation = await self._get_voice_confirmation(executable_trade)
                if not confirmation:
                    self.voice.speak("Trade cancelled by user.")
                    return {"success": False, "error": "User cancelled"}
            
            # Step 6: Order Staging
            self.voice.speak("Staging order for execution...")
            
            staged_order = self._stage_order(executable_trade, trade_plan)
            
            # Step 7: Success Response
            success_msg = self._format_trade_success(executable_trade, staged_order)
            self.voice.speak(success_msg)
            
            return {
                "success": True,
                "trade_plan": trade_plan.dict(),
                "executable_trade": executable_trade,
                "staged_order": staged_order,
                "session_id": self.session_id
            }
            
        except Exception as e:
            logger.error(f"Request processing error: {e}")
            error_msg = self.translation_manager.get_text(
                "errors.processing_failed", 
                self.current_language
            )
            self.voice.speak(f"{error_msg}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _get_market_data(self, symbol: str) -> MarketData:
        """Get current market data (mock implementation)"""
        # In production, this would connect to real market data
        mock_data = {
            "SPY": {"price": 450.0, "iv_rank": 25.0, "volume": 50000000},
            "QQQ": {"price": 380.0, "iv_rank": 30.0, "volume": 25000000},
            "AAPL": {"price": 175.0, "iv_rank": 35.0, "volume": 15000000},
        }
        
        data = mock_data.get(symbol, {"price": 100.0, "iv_rank": 50.0, "volume": 1000000})
        
        return MarketData(
            symbol=symbol,
            current_price=data["price"],
            iv_rank=data["iv_rank"],
            iv_percentile=data["iv_rank"],
            bid_ask_spread=0.02,
            volume=data["volume"]
        )
    
    async def _get_option_chains(self, symbol: str) -> List[OptionChain]:
        """Get option chains (mock implementation)"""
        from datetime import timedelta
        
        # Mock option chain
        expiration = datetime.now() + timedelta(days=30)
        current_price = (await self._get_market_data(symbol)).current_price
        
        # Generate mock options around current price
        calls = {}
        puts = {}
        
        for i in range(-10, 11):
            strike = current_price + (i * 5)
            
            calls[strike] = {
                "bid": max(0.5, 5 - abs(i) * 0.5),
                "ask": max(0.6, 5.1 - abs(i) * 0.5),
                "last": max(0.55, 5.05 - abs(i) * 0.5),
                "volume": max(100, 1000 - abs(i) * 50),
                "open_interest": max(500, 5000 - abs(i) * 200),
                "delta": max(0.05, 0.5 - (i * 0.05)),
                "gamma": 0.02,
                "theta": -0.05,
                "vega": 0.15,
                "iv": 0.25
            }
            
            puts[strike] = {
                "bid": max(0.5, 5 - abs(i) * 0.5),
                "ask": max(0.6, 5.1 - abs(i) * 0.5),
                "last": max(0.55, 5.05 - abs(i) * 0.5),
                "volume": max(100, 1000 - abs(i) * 50),
                "open_interest": max(500, 5000 - abs(i) * 200),
                "delta": -max(0.05, 0.5 - (i * 0.05)),
                "gamma": 0.02,
                "theta": -0.05,
                "vega": 0.15,
                "iv": 0.25
            }
        
        return [OptionChain(
            expiration=expiration,
            calls=calls,
            puts=puts,
            dte=30
        )]
    
    async def _get_portfolio_metrics(self) -> PortfolioMetrics:
        """Get current portfolio metrics (mock implementation)"""
        return PortfolioMetrics(
            total_equity=self.config["account_equity"],
            available_cash=self.config["account_equity"] * 0.8,
            total_delta=0,
            total_gamma=0,
            total_theta=0,
            total_vega=0,
            daily_pnl=0,
            unrealized_pnl=0,
            margin_used=0,
            positions_count=0,
            max_single_position_size=0
        )
    
    async def _get_voice_confirmation(self, trade: Dict) -> bool:
        """Get voice confirmation for trade"""
        if not VOICE_AVAILABLE:
            return True  # Skip confirmation in mock mode
        
        # Speak trade summary
        summary = self._format_trade_summary(trade)
        self.voice.speak(f"Ready to execute: {summary}. Say 'confirm' to proceed or 'cancel' to abort.")
        
        # Listen for confirmation
        confirmation_text = self.voice.asr.recognize_once(timeout=10)
        
        if confirmation_text:
            return "confirm" in confirmation_text.lower() or "yes" in confirmation_text.lower()
        
        return False
    
    def _stage_order(self, trade: Dict, plan: TradePlan) -> Dict:
        """Stage order for execution"""
        try:
            order_data = {
                "symbol": trade["symbol"],
                "strategy": trade["strategy_type"],
                "legs": trade["legs"],
                "max_loss": trade["risk_constraints"]["max_loss"],
                "rationale": plan.rationale.summary,
                "session_id": self.session_id
            }
            
            staged_order = self.stage_order_client.stage_order(order_data)
            return staged_order
            
        except Exception as e:
            logger.error(f"Order staging failed: {e}")
            raise
    
    def _format_risk_violations(self, violations: List[RiskViolation]) -> str:
        """Format risk violations for voice output"""
        if not violations:
            return "No violations"
        
        critical = [v for v in violations if v.severity == "critical"]
        errors = [v for v in violations if v.severity == "error"]
        
        if critical:
            return f"{len(critical)} critical violations including {critical[0].message}"
        elif errors:
            return f"{len(errors)} error violations including {errors[0].message}"
        else:
            return f"{len(violations)} warning violations"
    
    def _format_trade_summary(self, trade: Dict) -> str:
        """Format trade summary for voice output"""
        strategy = trade["strategy_type"].replace("_", " ")
        symbol = trade["symbol"]
        size = trade["position_size"]
        max_loss = trade["risk_constraints"]["max_loss"]
        
        return f"{strategy} on {symbol}, size {size}, max loss ${max_loss:.0f}"
    
    def _format_trade_success(self, trade: Dict, order: Dict) -> str:
        """Format success message"""
        order_id = order.get("id", "unknown")
        return f"Trade staged successfully with order ID {order_id}. You can review it before execution."
    
    # Voice Command Handlers
    
    def _handle_buy_command(self, command: Dict) -> str:
        """Handle voice buy command"""
        params = command["parameters"]
        symbol = params.get("symbol", "")
        strategy = params.get("strategy", "")
        
        if not symbol:
            return "Please specify a symbol to buy"
        
        # Create natural language request
        request = f"Buy {strategy} options on {symbol}"
        
        # Process asynchronously (simplified for voice)
        try:
            # In production, this would use asyncio.create_task()
            result = {"success": True, "message": f"Processing buy order for {symbol}"}
            return result["message"]
        except Exception as e:
            return f"Error processing buy command: {e}"
    
    def _handle_sell_command(self, command: Dict) -> str:
        """Handle voice sell command"""
        params = command["parameters"]
        return "Sell command received - checking positions to close"
    
    def _handle_status_command(self, command: Dict) -> str:
        """Handle voice status command"""
        try:
            # Get portfolio status
            orders = self.stage_order_client.list_orders()
            return f"You have {len(orders)} staged orders and 0 open positions"
        except Exception as e:
            return f"Status check failed: {e}"
    
    def _handle_help_command(self, command: Dict) -> str:
        """Handle voice help command"""
        return "I can help you buy or sell options, check your status, or close positions. Try saying 'buy SPY calls' or 'show my status'."
    
    def _handle_close_command(self, command: Dict) -> str:
        """Handle voice close command"""
        return "Checking for positions to close"

# Example usage and testing
async def main():
    """Test the Phase 3 system"""
    system = Phase3TradingSystem()
    
    # Start system
    await system.start_system()
    
    # Test natural language requests
    test_requests = [
        "I think SPY is going to trade sideways for the next month, what's a good strategy?",
        "Buy iron condor on QQQ with $500 max risk",
        "Show me my current positions and risk exposure"
    ]
    
    for request in test_requests:
        print(f"\n--- Processing: {request} ---")
        result = await system.process_natural_language_request(request)
        print(f"Result: {result['success']}")
        if not result["success"]:
            print(f"Error: {result.get('error')}")
    
    # Test voice commands (if available)
    if VOICE_AVAILABLE:
        print("\nVoice interface active - try saying commands...")
        try:
            await asyncio.sleep(10)  # Listen for 10 seconds
        except KeyboardInterrupt:
            pass
    
    # Stop system
    system.stop_system()

if __name__ == "__main__":
    asyncio.run(main())