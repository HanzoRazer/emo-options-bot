from __future__ import annotations
from typing import Optional
from src.llm.orchestrator import Orchestrator
from src.trade.synthesizer import TradeSynthesizer
from src.risk.gates import RiskGate
from src.llm.schemas import SynthesisResult
from src.voice.asr_tts import VoiceIO

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

    async def process_natural_language_request(self, text: str) -> SynthesisResult:
        return self.process_text(text)

    def stop_system(self):
        pass