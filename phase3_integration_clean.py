"""
Phase 3 Integration - End-to-end orchestration system
Combines all Phase 3 components into a unified trading system
"""

from __future__ import annotations
import os
from typing import Dict, Any, Optional
from datetime import datetime

# Import Phase 3 components
try:
    from schemas import Phase3Request, Phase3Response, OptionsOrder, MarketAnalysis, RiskAssessment
    from orchestrator import Orchestrator
    from synthesizer import TradeSynthesizer 
    from gates import RiskGate
    from asr_tts import VoiceInterface
    from prompt_kits import PromptManager
    from src.database.db_router import DBRouter
except ImportError as e:
    print(f"Warning: Some Phase 3 components not available: {e}")
    # Fallback types for development
    Phase3Request = Dict[str, Any]
    Phase3Response = Dict[str, Any]
    OptionsOrder = Dict[str, Any]


class Phase3TradingSystem:
    """
    Complete Phase 3 trading system integration
    Orchestrates the entire flow from natural language input to executable orders
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Phase 3 system with all components"""
        self.config = config or {}
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize components
        self._init_components()
        
        # System state
        self.is_active = False
        self.voice_mode = self.config.get("voice_mode", False)
        self.debug_mode = self.config.get("debug", False)
    
    def _init_components(self):
        """Initialize all Phase 3 components"""
        try:
            # Core components
            self.orchestrator = Orchestrator(
                provider=self.config.get("llm_provider", "mock")
            )
            self.synthesizer = TradeSynthesizer()
            self.risk_gate = RiskGate(
                max_per_trade_risk=self.config.get("max_per_trade_risk", 0.02),
                max_portfolio_risk=self.config.get("max_portfolio_risk", 0.10)
            )
            
            # Optional components
            self.voice_interface = VoiceInterface() if self.voice_mode else None
            self.prompt_manager = PromptManager()
            self.db_router = DBRouter()
            
            # Component health status
            self.components_healthy = True
            
        except Exception as e:
            print(f"Error initializing components: {e}")
            self.components_healthy = False
    
    def process_request(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main request processing pipeline
        Natural Language → Analysis → Strategy → Risk Check → Order
        """
        context = context or {}
        start_time = datetime.now()
        
        try:
            # Step 1: Natural language processing and market analysis
            if self.debug_mode:
                print(f"🔍 Step 1: Analyzing input: '{user_input[:50]}...'")
            
            analysis_result = self.orchestrator.process_request(user_input, context)
            
            if not analysis_result.get("success", False):
                return self._create_error_response(
                    "Analysis failed", 
                    analysis_result.get("error", "Unknown analysis error")
                )
            
            # Step 2: Strategy synthesis
            if self.debug_mode:
                print(f"⚙️ Step 2: Synthesizing strategy...")
            
            trade_plan = analysis_result.get("plan", {})
            order_result = self.synthesizer.suggest(trade_plan)
            
            if "error" in order_result:
                return self._create_error_response(
                    "Strategy synthesis failed",
                    order_result["error"]
                )
            
            # Step 3: Risk assessment
            if self.debug_mode:
                print(f"🛡️ Step 3: Assessing risk...")
            
            portfolio_context = context.get("portfolio", {"total_risk": 0.05})
            account_equity = context.get("account_equity", 10000)
            
            risk_result = self.risk_gate.validate_trade(
                order_result, 
                portfolio_context, 
                account_equity
            )
            
            # Step 4: Create final response
            processing_time = (datetime.now() - start_time).total_seconds()
            
            response = {
                "success": True,
                "user_input": user_input,
                "analysis": analysis_result.get("analysis", {}),
                "order": order_result,
                "risk_assessment": risk_result,
                "approved": risk_result.get("approved", False),
                "processing_time": processing_time,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # Step 5: Voice response if enabled
            if self.voice_interface:
                response_text = self._generate_voice_response(response)
                voice_result = self.voice_interface.speak_response(response_text)
                response["voice_response"] = voice_result
            
            if self.debug_mode:
                print(f"✅ Processing complete ({processing_time:.2f}s)")
            
            return response
            
        except Exception as e:
            return self._create_error_response(
                "System error",
                str(e),
                processing_time=(datetime.now() - start_time).total_seconds()
            )
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive system health check"""
        health_status = {
            "system_status": "healthy",
            "session_id": self.session_id,
            "components": {},
            "overall_healthy": True
        }
        
        # Check each component
        components = [
            ("orchestrator", self.orchestrator),
            ("synthesizer", self.synthesizer), 
            ("risk_gate", self.risk_gate),
            ("prompt_manager", self.prompt_manager),
            ("db_router", self.db_router)
        ]
        
        if self.voice_interface:
            components.append(("voice_interface", self.voice_interface))
        
        for name, component in components:
            try:
                if hasattr(component, "health_check"):
                    component_health = component.health_check()
                    health_status["components"][name] = component_health
                    
                    if component_health.get("status") != "healthy":
                        health_status["overall_healthy"] = False
                else:
                    health_status["components"][name] = {"status": "no_health_check"}
            except Exception as e:
                health_status["components"][name] = {"status": "error", "error": str(e)}
                health_status["overall_healthy"] = False
        
        if not health_status["overall_healthy"]:
            health_status["system_status"] = "degraded"
        
        return health_status
    
    def _create_error_response(self, error_type: str, message: str, processing_time: float = 0) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "success": False,
            "error_type": error_type,
            "error_message": message,
            "processing_time": processing_time,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_voice_response(self, response: Dict[str, Any]) -> str:
        """Generate voice response text from processing result"""
        if not response.get("success", False):
            return f"I encountered an error: {response.get('error_message', 'Unknown error')}"
        
        order = response.get("order", {})
        risk = response.get("risk_assessment", {})
        
        if response.get("approved", False):
            strategy = order.get("strategy_type", "strategy")
            symbol = order.get("symbol", "")
            max_loss = risk.get("max_loss", 0)
            
            return f"I've analyzed your request for {symbol}. The recommended {strategy} strategy has a maximum risk of ${max_loss:.0f} and has passed all risk checks. The order is ready for your review."
        else:
            violations = len(risk.get("violations", []))
            return f"I've analyzed your request, but the strategy has {violations} risk violations and cannot be approved automatically. Please review the risk assessment."


# Convenience functions for quick access
def create_trading_system(config: Optional[Dict[str, Any]] = None) -> Phase3TradingSystem:
    """Create Phase 3 trading system with configuration"""
    return Phase3TradingSystem(config)


def quick_analysis(user_input: str, **kwargs) -> Dict[str, Any]:
    """Quick trading analysis without full system setup"""
    system = create_trading_system({"debug": kwargs.get("debug", False)})
    return system.process_request(user_input, kwargs)


# Example usage and testing
if __name__ == "__main__":
    print("🚀 Testing Phase 3 Integration System")
    
    # Test system initialization
    config = {
        "llm_provider": "mock",
        "voice_mode": True,
        "debug": True
    }
    
    system = Phase3TradingSystem(config)
    print(f"✅ Phase 3 system initialized")
    
    # Health check
    health = system.health_check()
    print(f"System health: {health['system_status']}")
    print(f"Components healthy: {health['overall_healthy']}")
    
    # Test trading request
    result = system.process_request(
        "I want to trade SPY with a neutral outlook and max risk of 500 dollars",
        context={
            "account_equity": 20000,
            "portfolio": {"total_risk": 0.03}
        }
    )
    
    if result.get("success", False):
        order = result.get("order", {})
        risk = result.get("risk_assessment", {})
        
        print(f"   ✅ Success: {order.get('strategy_type', 'unknown')} strategy")
        print(f"   Risk: ${risk.get('max_loss', 0):.0f} ({risk.get('risk_level', 'unknown')})")
        print(f"   Approved: {'✅' if result.get('approved') else '❌'}")
        print(f"   Time: {result.get('processing_time', 0):.2f}s")
    else:
        print(f"   ❌ Failed: {result.get('error_message', 'Unknown error')}")
    
    print(f"\n🚀 Phase 3 integration testing complete")