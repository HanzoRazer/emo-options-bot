"""
Phase 3 Smoke Test Runner
- Verifies Python env, required files, env vars
- Imports & instantiates Phase 3 core components (LLM Orchestrator, Synthesizer, Risk Gates, Voice IO)
- Validates DB router dev-mode (SQLite) connectivity
- Ensures dashboard & health endpoints scaffolds exist
- No network calls; safe for CI

Exit codes:
  0 = all good
  1 = failures detected
"""

from __future__ import annotations
import os
import sys
import json
import argparse
import importlib
import subprocess
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[1]  # repo root
SRC  = ROOT / "src"

# Optional: add src to path if your project is package-based under /src
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Add root directory for Phase 3 modules in development
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# -------- util helpers --------------------------------------------------------
class CheckResult:
    def __init__(self, name: str, ok: bool, info: str = ""):
        self.name = name
        self.ok = ok
        self.info = info

    def __repr__(self):
        return f"{'[OK ]' if self.ok else '[FAIL]'} {self.name} {('- ' + self.info) if self.info else ''}"

def run(cmd: List[str]) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True)
        return (p.returncode, p.stdout.strip(), p.stderr.strip())
    except Exception as e:
        return (127, "", str(e))

def exists_any(paths: List[Path]) -> bool:
    return any(p.exists() for p in paths)

# -------- checks --------------------------------------------------------------
def check_python_version(min_major=3, min_minor=10) -> CheckResult:
    ok = (sys.version_info.major > min_major) or \
         (sys.version_info.major == min_major and sys.version_info.minor >= min_minor)
    return CheckResult(
        "Python version",
        ok,
        info=f"found {sys.version.split()[0]} (need >= {min_major}.{min_minor})"
    )

def check_virtualenv() -> CheckResult:
    in_venv = bool(os.environ.get("VIRTUAL_ENV") or hasattr(sys, "real_prefix"))
    return CheckResult("Virtualenv active", in_venv, info=os.environ.get("VIRTUAL_ENV",""))

def check_env_vars(required: List[str]) -> CheckResult:
    missing = [k for k in required if not os.environ.get(k)]
    ok = not missing
    info = "all present" if ok else f"missing: {', '.join(missing)}"
    return CheckResult("Env vars (Phase 3 minimal)", ok, info)

def check_files_exist() -> List[CheckResult]:
    targets = [
        ("README.md", ROOT / "README.md"),
        ("CONFIG.md", ROOT / "CONFIG.md"),
        ("DEVELOPER_QUICK_START.md", ROOT / "DEVELOPER_QUICK_START.md"),
        (".env.example", ROOT / ".env.example"),
        ("Dashboard builder", ROOT / "tools" / "build_dashboard.py"),
    ]
    return [CheckResult(name, path.exists(), info=str(path)) for name, path in targets]

def check_git_basics() -> List[CheckResult]:
    results: List[CheckResult] = []
    # git exists
    rc, out, err = run(["git", "--version"])
    results.append(CheckResult("git available", rc == 0, info=out or err))

    # git status clean?
    rc, out, err = run(["git", "status", "--porcelain"])
    clean = (rc == 0 and out.strip() == "")
    results.append(CheckResult("git working tree clean", clean, info="dirty" if not clean else ""))

    # remote configured?
    rc, out, err = run(["git", "remote", "-v"])
    results.append(CheckResult("git remote configured", rc == 0 and out.strip() != "", info=out or err))
    return results

def check_imports_phase3() -> List[CheckResult]:
    """
    Import the Phase 3 modules by their expected names.
    Adjust import paths below to match your repo layout if needed.
    """
    modules = [
        ("schemas",           "schemas"),                      # Pydantic models
        ("orchestrator",      "orchestrator"),                 # LLM orchestrator
        ("synthesizer",       "synthesizer"),                  # Trade synthesis
        ("gates",             "gates"),                        # Risk gates
        ("phase3_integration","phase3_integration"),           # End-to-end orchestrator
        ("asr_tts",           "asr_tts"),                      # Voice IO
        ("prompt_kits",       "prompt_kits"),                  # Prompts (pkg or module)
    ]
    results: List[CheckResult] = []
    for friendly, mod in modules:
        try:
            importlib.import_module(mod)
            results.append(CheckResult(f"import {friendly}", True))
        except Exception as e:
            results.append(CheckResult(f"import {friendly}", False, info=str(e)))
    return results

def check_db_router() -> List[CheckResult]:
    """
    Verifies that the DB router can choose SQLite for dev/test and connect.
    Expects: src/database/db_router.py (DBRouter or get_conn)
    """
    results: List[CheckResult] = []
    try:
        db_router = importlib.import_module("database.db_router")
    except Exception as e:
        return [CheckResult("db.router import", False, info=str(e))]

    # Force dev
    old_env = os.environ.get("EMO_ENV")
    os.environ["EMO_ENV"] = os.environ.get("EMO_ENV", "development") or "development"

    try:
        # Expected router entrypoints:
        # - DBRouter().connect()
        # - or get_conn()
        conn = None
        if hasattr(db_router, "DBRouter"):
            r = db_router.DBRouter()
            conn = r.connect()
        elif hasattr(db_router, "get_conn"):
            conn = db_router.get_conn()
        else:
            results.append(CheckResult("db.router entrypoint", False, info="no DBRouter or get_conn"))
            return results

        ok = conn is not None
        results.append(CheckResult("db.router SQLite dev connect", ok))
        # quick smoke query (SQLite only)
        try:
            cur = conn.cursor()
            cur.execute("SELECT 1")
            cur.fetchone()
            results.append(CheckResult("db.router SELECT 1", True))
        except Exception as e:
            results.append(CheckResult("db.router SELECT 1", False, info=str(e)))
        finally:
            try:
                conn.close()
            except Exception:
                pass
    except Exception as e:
        results.append(CheckResult("db.router SQLite dev connect", False, info=str(e)))
    finally:
        # restore env
        if old_env is None:
            os.environ.pop("EMO_ENV", None)
        else:
            os.environ["EMO_ENV"] = old_env

    return results

def check_voice_optional() -> List[CheckResult]:
    """
    Ensure voice module degrades gracefully (mock interface).
    """
    results: List[CheckResult] = []
    try:
        mod = importlib.import_module("asr_tts")
        # expect maybe a `has_real_audio()` or fall back symbol, else just import OK
        ok = True
        info = "import ok"
        if hasattr(mod, "HAS_AUDIO"):
            info = f"HAS_AUDIO={getattr(mod, 'HAS_AUDIO')}"
        results.append(CheckResult("voice IO (ASR/TTS) import", ok, info))
    except Exception as e:
        results.append(CheckResult("voice IO (ASR/TTS) import", False, info=str(e)))
    return results

def check_llm_orchestrator_smoke() -> List[CheckResult]:
    """
    Instantiate orchestrator in MOCK mode (no real API).
    Expect orchestrator.Orchestrator(provider='mock') or similar based on your implementation.
    """
    results: List[CheckResult] = []
    try:
        orch = importlib.import_module("orchestrator")
        ok = False
        info = ""
        if hasattr(orch, "Orchestrator"):
            try:
                o = orch.Orchestrator(provider=os.getenv("LLM_PROVIDER","mock"))
                # try a tiny no-network call if supported
                if hasattr(o, "analyze") and "mock" in (os.getenv("LLM_PROVIDER","mock") or "").lower():
                    _ = o.analyze("health check", {"symbol":"SPY"})
                ok = True
                info = f"provider={getattr(o,'provider','unknown')}"
            except Exception as e:
                info = f"init/analyze error: {e}"
        else:
            info = "Orchestrator class not found"
        results.append(CheckResult("LLM Orchestrator (mock)", ok, info))
    except Exception as e:
        results.append(CheckResult("LLM Orchestrator import", False, info=str(e)))
    return results

def check_synthesizer_smoke() -> List[CheckResult]:
    """
    Ensure synthesizer can construct a trivial neutral-IRON-CONDOR suggestion given a mock context.
    """
    results: List[CheckResult] = []
    try:
        synth = importlib.import_module("synthesizer")
        ok = True
        info = ""
        if hasattr(synth, "TradeSynthesizer"):
            try:
                s = synth.TradeSynthesizer()
                # Provide minimal context to not rely on live data
                plan = {
                    "thesis": "range-bound",
                    "symbol": "SPY",
                    "constraints": {"max_loss": 500}
                }
                out = s.suggest(plan)
                ok = isinstance(out, dict) and "strategy_type" in out
                info = out.get("strategy_type","")
            except Exception as e:
                ok = False
                info = str(e)
        else:
            ok = False
            info = "TradeSynthesizer not found"
        results.append(CheckResult("Synthesizer suggest() (mock)", ok, info))
    except Exception as e:
        results.append(CheckResult("Synthesizer import", False, info=str(e)))
    return results

def check_risk_gates_smoke() -> List[CheckResult]:
    results: List[CheckResult] = []
    try:
        gates = importlib.import_module("gates")
        ok = True
        info = ""
        # Expect RiskGate or validate_trade function
        if hasattr(gates, "RiskGate"):
            try:
                rg = gates.RiskGate(max_per_trade_risk=0.02, max_portfolio_risk=0.10)
                fake_trade = {"max_loss": 400, "notional": 10000, "legs": []}
                fake_portfolio = {"total_risk": 0.08}
                viol = rg.validate_trade(fake_trade, fake_portfolio, account_equity=20000)
                ok = isinstance(viol, dict) and "violations" in viol
                info = f"violations={len(viol.get('violations',[]))}"
            except Exception as e:
                ok = False
                info = str(e)
        elif hasattr(gates, "validate_trade"):
            try:
                viol = gates.validate_trade({}, {}, 10000)
                ok = True
                info = "validate_trade() exists"
            except Exception as e:
                ok = False
                info = str(e)
        else:
            ok = False
            info = "No RiskGate or validate_trade found"
        results.append(CheckResult("Risk Gates (mock)", ok, info))
    except Exception as e:
        results.append(CheckResult("Risk Gates import", False, info=str(e)))
    return results

def check_dashboard_artifacts() -> List[CheckResult]:
    # Just ensure dashboard code exists; do not execute/serve here.
    paths = [
        ROOT / "enhanced_dashboard.py",
        ROOT / "dashboard.py",
        SRC / "web" / "dashboard.py",
        ROOT / "tools" / "market_dashboard.py",
    ]
    ok = exists_any(paths)
    info = " / ".join(str(p) for p in paths if p.exists())
    return [CheckResult("Dashboard code present", ok, info=info or "missing common locations")]

# -------- main ---------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Phase 3 Smoke Tests")
    parser.add_argument("--quick", action="store_true", help="Skip git checks")
    parser.add_argument("--fast", action="store_true", help="Minimal checks for CI")
    args = parser.parse_args()

    results: List[CheckResult] = []

    # 1) Environment basics
    results.append(check_python_version())
    if not args.fast:
        results.append(check_virtualenv())

    # 2) Required env (Phase 3 minimal: no network, just ensure presence where relevant)
    # Keep these minimal & optional; not all tests need live credentials.
    results.append(check_env_vars([
        "EMO_ENV",             # dev/staging/prod
        # optional LLM provider; default mock
        # "OPENAI_API_KEY"     # Not required for mock run
    ]))

    # 3) Repo files
    results.extend(check_files_exist())

    # 4) Git checks (optional)
    if not args.quick and not args.fast:
        results.extend(check_git_basics())

    # 5) Imports for Phase 3 core modules
    if not args.fast:
        results.extend(check_imports_phase3())

    # 6) DB router (dev sqlite)
    if not args.fast:
        results.extend(check_db_router())

    # 7) LLM Orchestrator (mock)
    if not args.fast:
        results.extend(check_llm_orchestrator_smoke())

    # 8) Synthesizer (mock)
    if not args.fast:
        results.extend(check_synthesizer_smoke())

    # 9) Risk Gates (mock)
    if not args.fast:
        results.extend(check_risk_gates_smoke())

    # 10) Dashboard presence
    results.extend(check_dashboard_artifacts())

    # 11) Voice fallback presence
    if not args.fast:
        results.extend(check_voice_optional())

    # ---- report
    failures = [r for r in results if not r.ok]
    print("\n=== Phase 3 Smoke Summary ===")
    for r in results:
        print(r)

    if failures:
        print("\n❌ FAILURES:")
        for f in failures:
            print(f" - {f.name}: {f.info}")
        print("\nExit: 1 (fail)")
        sys.exit(1)

    print("\n✅ SUCCESS: Phase 3 smoke checks passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()