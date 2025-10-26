import os
import sys
import importlib
from pathlib import Path

"""
Auto Loader for Phase 3 modules.

Goals:
- Let you develop Phase 3 in a separate folder or submodule.
- Auto-detect and import: schemas, orchestrator, synthesizer, gates, asr_tts, phase3_integration.
- Fail gracefully with helpful diagnostics.

How it works:
- Looks for PHASE3_MODULE_DIR env var first.
- Falls back to: ./src/phase3, ./phase3, ./src
- Adds chosen dir to sys.path (front).
"""

PHASE3_CANDIDATES = [
    lambda: os.getenv("PHASE3_MODULE_DIR", "").strip(),
    lambda: str(Path(__file__).resolve().parent),              # ./src/phase3
    lambda: str(Path(__file__).resolve().parent.parent / "phase3"), # ./src/phase3 (fallback)
    lambda: str(Path(__file__).resolve().parents[1]),          # ./src
]

PHASE3_MODULES = [
    "schemas",
    "orchestrator",
    "synthesizer",
    "gates",
    "asr_tts",
    "phase3_integration",
]

class Phase3AutoloadError(Exception):
    pass

def _is_usable_dir(p: str) -> bool:
    if not p:
        return False
    return Path(p).exists()

def choose_phase3_dir():
    for cand in PHASE3_CANDIDATES:
        path = cand()
        if _is_usable_dir(path):
            return path
    return None

def ensure_on_syspath(path: str):
    # put in front so local dev wins
    if path and path not in sys.path:
        sys.path.insert(0, path)

def try_import_all(base_pkg: str | None = None):
    """
    Attempt to import all key Phase 3 modules.
    If base_pkg is provided (e.g., 'phase3'), import as 'phase3.schemas', etc.
    Else import as top-level 'schemas', etc.
    Returns dict of {name: module or None}, plus list of failures.
    """
    imported = {}
    failures = []

    for name in PHASE3_MODULES:
        fq_name = f"{base_pkg}.{name}" if base_pkg else name
        try:
            imported[name] = importlib.import_module(fq_name)
        except Exception as e:
            imported[name] = None
            failures.append((name, str(e)))
    return imported, failures

def autoload(verbose: bool = True):
    """
    Main entry:
    1) Pick a Phase 3 directory.
    2) Put it on sys.path.
    3) Try importing modules as either 'phase3.NAME' or bare NAME.
    4) Return a result dict with diagnostics.
    """
    result = {
        "dir": None,
        "base_pkg": None,
        "imported": {},
        "failures": [],
        "sys_path_head": None,
    }

    p3_dir = choose_phase3_dir()
    if not p3_dir:
        raise Phase3AutoloadError("Could not find Phase 3 module directory. Set PHASE3_MODULE_DIR or ensure src/phase3 exists.")

    ensure_on_syspath(p3_dir)
    result["dir"] = p3_dir
    result["sys_path_head"] = sys.path[0]

    # Try importing as a package "phase3" if available
    base_pkg = None
    try:
        _pkg = importlib.import_module("phase3")
        base_pkg = "phase3"
    except Exception:
        base_pkg = None
    result["base_pkg"] = base_pkg

    imported, failures = try_import_all(base_pkg=base_pkg)
    result["imported"] = {k: bool(v) for k, v in imported.items()}
    result["failures"] = failures

    if verbose:
        print("🔎 Phase 3 Autoload")
        print(f"   • chosen_dir: {result['dir']}")
        print(f"   • base_pkg:   {result['base_pkg'] or '(bare)'}")
        print(f"   • sys.path[0]: {result['sys_path_head']}")
        for name, ok in result["imported"].items():
            status = "✅" if ok else "❌"
            print(f"   • {status} {name}")
        if failures:
            print("   • Failures:")
            for name, err in failures:
                print(f"     - {name}: {err}")

    return result

if __name__ == "__main__":
    autoload(verbose=True)