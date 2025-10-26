#!/usr/bin/env python
"""
Phase 3 Release Check (Smoke Tests)

Fast, dependency-light validations that ensure the Phase 3 surface area
is importable and minimally operational before tagging a release.

Exit codes:
  0  success
  1  general failure
  2  missing configuration / credentials in strict mode

Usage:
  python tools/release_check.py
  python tools/release_check.py --strict
  python tools/release_check.py --verbose
"""
from __future__ import annotations
import argparse
import importlib
import os
import sys
import time
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OK = "[OK]"
WARN = "[WARN]"
ERR = "[ERR]"

class CheckFailure(Exception):
    pass

def section(title: str):
    print(f"\n== {title} ==")

def timed(fn, *args, **kwargs):
    t0 = time.time()
    result = fn(*args, **kwargs)
    dt = time.time() - t0
    return result, dt

def check_import(module: str):
    try:
        importlib.import_module(module)
        print(f"{OK} import {module}")
        return True
    except Exception as e:
        print(f"{ERR} import {module}: {e}")
        return False

def check_env(required: List[str], strict: bool) -> Tuple[bool, List[str]]:
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        if strict:
            print(f"{ERR} missing env: {', '.join(missing)}")
        else:
            print(f"{WARN} missing env (non-strict): {', '.join(missing)}")
    else:
        print(f"{OK} required env present")
    return (len(missing) == 0 or not strict), missing

def check_db_router():
    # Best-effort import + basic probe
    try:
        db_router = importlib.import_module("src.database.db_router")
        get_engine = getattr(db_router, "get_engine", None)
        if not callable(get_engine):
            print(f"{ERR} db_router.get_engine not found")
            return False
        engine = get_engine()  # should choose SQLite in dev by EMO_ENV
        try:
            # Use text() for proper SQL execution in SQLAlchemy
            from sqlalchemy import text
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
        except Exception as e:
            print(f"{WARN} db connectivity issue: {e}")
            return False
        print(f"{OK} database router basic connectivity")
        return True
    except Exception as e:
        print(f"{ERR} database router check: {e}")
        return False

def check_broker():
    # Import broker module and ensure constructor exists
    candidates = [
        "exec.alpaca_broker",
        "src.exec.alpaca_broker",
        "exec.broker",  # fallback / mock
        "src.exec.broker",
    ]
    ok_any = False
    for m in candidates:
        try:
            mod = importlib.import_module(m)
            cls = getattr(mod, "AlpacaBroker", None) or getattr(mod, "Broker", None)
            if callable(cls):
                _ = cls(paper=True) if "Alpaca" in (cls.__name__ or "") else cls()
                print(f"{OK} broker ready via {m}.{cls.__name__}")
                ok_any = True
                break
        except Exception as e:
            print(f"{WARN} broker import failed for {m}: {e}")
    if not ok_any:
        print(f"{ERR} no broker available")
    return ok_any

def check_phase3_surfaces():
    # Critical Phase 3 surfaces (adapted to our current project structure)
    surfaces = [
        "src.phase3.schemas",
        "src.phase3.orchestrator", 
        "src.phase3.synthesizer",
        "src.phase3.gates",
        "src.phase3.mock_llm",
        "schemas",  # fallback for top-level import
    ]
    ok_count = 0
    for name in surfaces:
        if check_import(name):
            ok_count += 1
    if ok_count >= 3:  # At least 3 core Phase 3 components working
        print(f"{OK} Phase 3 core surfaces available ({ok_count} found)")
        return True
    else:
        print(f"{ERR} Insufficient Phase 3 surfaces ({ok_count} found)")
        return False

def check_ml_hooks():
    # Ensure ML pipeline entry points exist if present in repo
    hooks = [
        "src.ml.models", "src.ml.features", "src.ml.outlook",
        "predict_ml", "train_ml", "test_ml",
    ]
    any_found = False
    for h in hooks:
        try:
            importlib.import_module(h)
            print(f"{OK} ML hook {h}")
            any_found = True
        except Exception:
            # Not fatal: ML might be optional in some deployments
            pass
    if not any_found:
        print(f"{WARN} no ML hooks detected (ok if ML is optional here)")
    return True

def check_dashboard():
    # Ensure dashboard can be imported (no server start here)
    candidates = [
        "src.web.enhanced_dashboard", "src.web.dashboard", "dashboard",
        "enhanced_dashboard", "tools.build_dashboard"
    ]
    for c in candidates:
        try:
            importlib.import_module(c)
            print(f"{OK} dashboard import ok: {c}")
            return True
        except Exception:
            continue
    print(f"{WARN} dashboard module not found (skipping)")
    return True

def main():
    ap = argparse.ArgumentParser(description="Phase 3 Smoke Tests")
    ap.add_argument("--strict", action="store_true", help="Fail on missing credentials/config")
    ap.add_argument("--verbose", action="store_true", help="Print extra details")
    args = ap.parse_args()

    if args.verbose:
        print(f"ROOT = {ROOT}")
        print(f"PYTHON = {sys.executable}")
        print(f"EMO_ENV = {os.getenv('EMO_ENV', '(unset)')}")

    status = True

    section("Environment")
    env_ok, missing = check_env(
        required=["ALPACA_KEY_ID", "ALPACA_SECRET_KEY", "ALPACA_DATA_URL"],
        strict=args.strict
    )
    status &= env_ok

    section("Database Router")
    status &= check_db_router()

    section("Broker")
    status &= check_broker()

    section("Phase 3 Surfaces")
    status &= check_phase3_surfaces()

    section("ML Hooks (optional)")
    status &= check_ml_hooks()

    section("Dashboard (import only)")
    status &= check_dashboard()

    print("\nSummary:")
    if status:
        print(f"{OK} Phase 3 smoke tests passed")
        sys.exit(0)
    else:
        code = 2 if (args.strict and missing) else 1
        print(f"{ERR} Phase 3 smoke tests failed (exit {code})")
        sys.exit(code)

if __name__ == "__main__":
    main()