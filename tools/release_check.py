"""
Phase 3 release smoke check:
 - Imports LLM/Voice/Synth/Risk/Integration
 - Runs a tiny end-to-end dry-run
"""
from __future__ import annotations
import sys
import os
from pathlib import Path

# Add project root to Python path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def main() -> int:
    try:
        from src.llm.orchestrator import Orchestrator
        from src.llm.schemas import MarketView
        from src.trade.synthesizer import TradeSynthesizer
        from src.risk.gates import RiskGate
        from src.phase3_integration import Phase3TradingSystem
        from src.voice.asr_tts import VoiceIO
        print("[OK] All Phase 3 imports successful")
    except Exception as e:
        print("❌ Import failure:", e)
        return 1

    try:
        # Basic E2E: neutral/range → iron condor
        sys.setrecursionlimit(10_000)
        system = Phase3TradingSystem()
        res = system.process_text("I think SPY trades sideways")
        assert res.trade is not None, "No trade produced"
        assert res.trade.strategy_type == "iron_condor", "Expected iron_condor"
        print("✅ Phase 3 smoke OK:", res.trade.strategy_type, res.trade.symbol)
        return 0
    except Exception as e:
        print("❌ E2E failure:", e)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())