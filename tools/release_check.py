"""
Phase 3 Smoke Tests for Release Readiness
Run:
  .venv\Scripts\python.exe tools\release_check.py
This verifies imports + a dry-run staging flow.
"""
import os, sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def ok(msg): print(f"[OK] {msg}")
def warn(msg): print(f"[WARN] {msg}")
def fail(msg): print(f"[ERROR] {msg}")

def test_imports():
    try:
        import src.config.enhanced_config as _cfg
        import src.phase3.orchestrator as _o
        import src.phase3.synthesizer as _s
        import src.phase3.gates as _g
        import src.ops.order_staging as _st
        ok("Imports: config, orchestrator, synthesizer, gates, order_staging")
        return True
    except Exception as e:
        fail(f"Import error: {e}")
        return False

def test_staging_dry_run():
    try:
        from src.ops.order_staging import write_draft
        from src.config.enhanced_config import SETTINGS
        draft_dir = Path(SETTINGS.drafts_dir)
        draft_dir.mkdir(parents=True, exist_ok=True)
        trade = {
            "symbol": "SPY",
            "strategy_type": "iron_condor",
            "legs": [
                {"action": "sell", "instrument": "put", "strike": 440, "qty": 1},
                {"action": "buy",  "instrument": "put", "strike": 435, "qty": 1},
                {"action": "sell", "instrument": "call","strike": 460, "qty": 1},
                {"action": "buy",  "instrument": "call","strike": 465, "qty": 1},
            ],
            "risk_constraints": {"max_loss": 500}
        }
        p = write_draft(trade, drafts_dir=str(draft_dir), fmt=os.getenv("EMO_DRAFTS_FORMAT", "yaml"), meta={"test":"release_check"})
        ok(f"Draft created: {p}")
        if not p.exists():
            fail("Draft file was not created")
            return False
        # Keep the file—useful for verifying in PR
        return True
    except Exception as e:
        fail(f"Staging dry-run error: {e}")
        return False

def main():
    print("[INFO] Phase 3 Release Smoke Test")
    print("="*32)
    all_ok = True
    if not test_imports(): all_ok = False
    if not test_staging_dry_run(): all_ok = False
    print("="*32)
    if all_ok:
        ok("Release check passed")
        sys.exit(0)
    else:
        fail("Release check FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()