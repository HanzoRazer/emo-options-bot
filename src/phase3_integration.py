from __future__ import annotations
from typing import Optional, Dict, Any
from src.llm.orchestrator import Orchestrator
from src.trade.synthesizer import TradeSynthesizer
from src.risk.gates import RiskGate
from src.llm.schemas import SynthesisResult
from src.voice.asr_tts import VoiceIO
from src.config.enhanced_config import SETTINGS
from src.ops.order_staging import write_draft

class Phase3TradingSystem:
    """Voice -> LLM -> Synthesis -> Risk Gates -> (Stage/Submit elsewhere)."""
    def __init__(self,
                 account_equity: float = 100_000.0,
                 open_positions_count: int = 0):
        self.voice = VoiceIO()
        self.llm = Orchestrator()
        self.syn = TradeSynthesizer()
        self.risk = RiskGate()
        self.account_equity = account_equity
        self.open_positions_count = open_positions_count

    async def start_system(self):
        pass  # future: start any background services

    def process_text(self, text: str) -> SynthesisResult:
        mv = self.llm.analyze(text)
        synth = self.syn.synthesize(mv)
        if synth.trade:
            hard = self.risk.validate_trade(
                trade=synth.trade,
                account_equity=self.account_equity,
                open_positions_count=self.open_positions_count
            )
            synth.violations.extend(hard)
            synth.ok = synth.ok and all(v.severity != "block" for v in synth.violations)
        return synth

    async def process_natural_language_request(self, text: str, *, meta: Optional[Dict[str, Any]] = None) -> SynthesisResult:
        """
        End-to-end: voice/text → LLM analysis → trade synthesis → risk gates → staging
        """
        result = self.process_text(text)
        
        # NEW: auto-stage validated trades if enabled and passed risk gates
        if SETTINGS.stage_orders and result.ok and result.trade:
            try:
                # Convert trade object to dict for staging
                trade_dict = {
                    "symbol": result.trade.symbol,
                    "strategy_type": result.trade.strategy_type,
                    "legs": [leg.__dict__ for leg in result.trade.legs] if result.trade.legs else [],
                    "expected_profit": getattr(result.trade, 'expected_profit', None),
                    "max_loss": getattr(result.trade, 'max_loss', None),
                    "expiry": getattr(result.trade, 'expiry', None),
                }
                
                path = write_draft(
                    trade_dict,
                    drafts_dir=SETTINGS.drafts_dir,
                    fmt=SETTINGS.drafts_format,
                    meta=meta or {"source": "phase3", "request": text}
                )
                
                # Add staging info to result (extend the result if needed)
                if hasattr(result, '__dict__'):
                    result.__dict__["staged_path"] = str(path)
                    
            except Exception as e:
                # Log staging error but don't fail the main flow
                print(f"Warning: Trade staging failed: {e}")
                
        return result

    def stop_system(self):
        pass