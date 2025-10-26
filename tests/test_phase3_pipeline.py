import os
import sys
from pathlib import Path
import pytest

repo = Path(__file__).resolve().parents[1]
if str(repo) not in sys.path:
    sys.path.insert(0, str(repo))

def _importorskip(modname):
    try:
        return __import__(modname, fromlist=["*"])
    except Exception:
        pytest.skip(f"Module {modname} not available—Phase 3 not fully wired on this machine.")

@pytest.mark.asyncio
async def test_phase3_integration_smoke():
    """
    Smoke test: if Phase 3 integration exists, ensure it can start and handle a simple NL request.
    This will gracefully skip if not present yet.
    """
    # Try both namespaced and bare imports (auto_loader supports both)
    try:
        p3 = _importorskip("phase3.phase3_integration")
    except pytest.skip.Exception:
        p3 = _importorskip("phase3_integration")

    Phase3TradingSystem = getattr(p3, "Phase3TradingSystem", None)
    if Phase3TradingSystem is None:
        pytest.skip("Phase3TradingSystem not available yet.")
        return

    system = Phase3TradingSystem()
    await system.start_system()
    try:
        # Minimal request that shouldn't require live keys
        result = await system.process_natural_language_request(
            "Give me a neutral-market options approach for SPY with limited risk."
        )
        # We don't enforce a schema here—just ensure something is returned
        assert result is not None
    finally:
        system.stop_system()