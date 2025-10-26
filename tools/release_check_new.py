"""
Phase 3 smoke: imports + minimal runtime probes.
Run: python tools/release_check_new.py
Exit non-zero on failure.
"""
import importlib, sys
from pathlib import Path

# Add project root to Python path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REQUIRED_IMPORTS = [
    "src.llm.orchestrator",           # LLM layer
    "src.trade.synthesizer",          # trade synthesis
    "src.risk.gates",                 # risk gates
    "src.voice.asr_tts",              # voice I/O (may fallback)
    "src.phase3_integration",         # glue
    "src.ops.order_staging",          # order staging
]

def try_import(mod):
    try:
        importlib.import_module(mod)
        print(f"[OK] import {mod}")
        return True
    except Exception as e:
        print(f"[FAIL] import {mod}: {e}")
        return False

def main():
    ok = True
    for m in REQUIRED_IMPORTS:
        ok &= try_import(m)
    
    # Optional: quick Phase 3 integration test
    try:
        from src.phase3_integration import Phase3TradingSystem
        system = Phase3TradingSystem()
        res = system.process_text("SPY neutral strategy")
        if res.trade and res.trade.strategy_type:
            print(f"[OK] Phase 3 integration: {res.trade.strategy_type}")
        else:
            print("[WARN] Phase 3 integration: no trade generated")
    except Exception as e:
        print(f"[WARN] Phase 3 integration test: {e}")
    
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
