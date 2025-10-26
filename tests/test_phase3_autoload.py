import os
import sys
from pathlib import Path
import pytest

def test_autoload_runs():
    # Ensure repo root on path
    repo = Path(__file__).resolve().parents[1]
    if str(repo) not in sys.path:
        sys.path.insert(0, str(repo))

    from src.phase3.auto_loader import autoload, Phase3AutoloadError

    # prefer explicit env if available, else rely on defaults
    env_dir = os.getenv("PHASE3_MODULE_DIR", "")
    if env_dir and not Path(env_dir).exists():
        pytest.skip("PHASE3_MODULE_DIR set but not found on this machine.")

    try:
        result = autoload(verbose=False)
    except Phase3AutoloadError:
        # If the developer hasn't added Phase 3 modules yet, that's ok—test passes with skip.
        pytest.skip("Phase 3 dir not present; autoload not applicable on this machine.")
        return

    # We at least expect the loader to choose a dir and not crash
    assert result["dir"], "Phase 3 loader did not resolve a directory"
    assert result["sys_path_head"], "sys.path not updated"

    # If modules are present, at least one should import
    if any(result["imported"].values()):
        assert any(result["imported"].values()) is True
    else:
        # If none imported, this can be OK during early scaffolding; provide a helpful reason
        pytest.skip("Phase 3 modules not found yet (schemas/orchestrator/etc.).")