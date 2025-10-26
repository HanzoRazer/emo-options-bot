#!/usr/bin/env python
"""
Phase 3 Completion Gate — runs all validation + staging + health checks before release.

Exit codes:
  0 = All good
  1 = Soft warnings only (proceed w/ caution)
  2 = Hard failures (do not release)
"""

import os, sys, time, json, socket, importlib, subprocess
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

WARNINGS = []
FAILURES = []

def ok(msg):     print(f"OK: {msg}")
def warn(msg):   print(f"WARN: {msg}"); WARNINGS.append(msg)
def fail(msg):   print(f"FAIL: {msg}"); FAILURES.append(msg)

def _require_env(keys, allow_empty=False):
    missing = [k for k in keys if (k not in os.environ) or (not allow_empty and not os.environ[k].strip())]
    if missing:
        fail(f"Missing required env vars: {', '.join(missing)}")
        return False
    ok(f"Env present: {', '.join(keys)}")
    return True

def _import(name):
    try:
        return importlib.import_module(name)
    except Exception as e:
        fail(f"Import failed: {name} ({e})")
        return None

def _http_ping(host="127.0.0.1", port=8082, path="/health", timeout=1.5):
    try:
        import http.client
        conn = http.client.HTTPConnection(host, port, timeout=timeout)
        conn.request("GET", path)
        resp = conn.getresponse()
        data = resp.read().decode(errors="ignore")
        conn.close()
        return resp.status, data
    except Exception as e:
        return None, str(e)

def section(title):
    print("\n" + "="*80)
    print(title)
    print("="*80)

def check_python():
    section("1) Python & dependencies")
    ok(f"Python {sys.version.split()[0]}")
    # core deps that Phase 3 typically uses
    for pkg in ["pandas","numpy","statsmodels","yaml"]:
        mod = _import(pkg.replace("_","-")) or _import(pkg)  # tolerate import-name variation
        if mod:
            ok(f"Package available: {pkg}")
    # special case for scikit-learn (imports as sklearn)
    sklearn = _import("sklearn")
    if sklearn:
        ok("Package available: scikit-learn")
    else:
        fail("Import failed: scikit-learn (No module named 'sklearn')")
    # optional ML/deep learning
    torch = _import("torch")
    if torch:
        ok("PyTorch available")
    else:
        warn("PyTorch not available (ok if you use classical models only)")

def check_env_config():
    section("2) Environment & config")
    # Support either env switching via EMO_ENV or multiple .env files (documented pattern)
    emo_env = os.environ.get("EMO_ENV","dev").lower()
    ok(f"EMO_ENV = {emo_env}")

    # Broker/data required for paper/live
    need = ["ALPACA_KEY_ID","ALPACA_SECRET_KEY"]
    if _require_env(need):
        ok("Alpaca credentials configured")

    # Optional broker base (paper/live)
    if not os.environ.get("ALPACA_API_BASE"):
        warn("ALPACA_API_BASE not set (defaulting may be OK for paper)")

def check_database_router():
    section("3) Database router & connectivity")
    # Expect database router from earlier phases
    candidates = [
        "src.database.db_router",
        "ops.db",
        "db.router",
        "database.router"
    ]
    mod = None
    for name in candidates:
        m = _import(name)
        if m and (hasattr(m, "get_engine") or hasattr(m, "engine") or hasattr(m, "Session")):
            mod = m
            ok(f"Database module found: {name}")
            break
    if not mod:
        warn("Database router not found (checking for basic database functionality)")
        return

    # Try to get database connection
    try:
        if hasattr(mod, "get_engine"):
            engine = mod.get_engine()
            ok(f"DB engine accessible: {engine}")
        elif hasattr(mod, "engine"):
            ok(f"DB engine available: {mod.engine}")
        else:
            ok("Database module loaded successfully")
    except Exception as e:
        warn(f"Database connection issue: {e}")

def check_migrations():
    section("4) Database migrations")
    # If you have a migration tool, call it in dry-run mode
    tools = [
        (ROOT / "tools" / "migrate.py"),
        (ROOT / "scripts" / "migrate.py"),
        (ROOT / "tools" / "db_manage.py"),
    ]
    for t in tools:
        if t.exists():
            try:
                res = subprocess.run([sys.executable, str(t), "--help"],
                                     capture_output=True, text=True, timeout=30)
                if res.returncode == 0:
                    ok(f"Migration tool available: {t.name}")
                    return
                else:
                    warn(f"Migration tool exists but not responsive: {t.name}")
            except Exception as e:
                warn(f"Migration tool check error ({t.name}): {e}")
    warn("No migration checker found (skipping). Ensure DB schema matches your models.")

def check_broker_reachability():
    section("5) Broker reachability (Alpaca)")
    # Lightweight test of Alpaca connectivity
    try:
        # Try basic import test
        alpaca_mod = _import("alpaca_trade_api") or _import("alpaca.trading") or _import("alpaca")
        if alpaca_mod:
            ok("Alpaca SDK available")
        else:
            warn("No Alpaca SDK found - install alpaca-trade-api if needed")
            
        # Check for test scripts
        testers = [
            (ROOT / "tools" / "test_alpaca.py"),
            (ROOT / "tools" / "alpaca_full_test.py"),
            (ROOT / "scripts" / "test_broker.py")
        ]
        
        for t in testers:
            if t.exists():
                try:
                    res = subprocess.run([sys.executable, str(t)],
                                         capture_output=True, text=True, timeout=60)
                    if res.returncode == 0:
                        ok(f"Broker test passed: {t.name}")
                        return
                    else:
                        warn(f"Broker test issues: {t.name}")
                except Exception as e:
                    warn(f"Broker test execution error: {e}")
        
        warn("No broker test scripts found — manual verification recommended")
    except Exception as e:
        warn(f"Broker check error: {e}")

def check_health_and_dashboard():
    section("6) Health & dashboard")
    # Health server check
    status, data = _http_ping(port=8082, path="/health")
    if status == 200:
        ok("Health endpoint /health is responding")
    else:
        warn(f"Health server not responding on 8082 (/health). Start with: python tools/emit_health.py")

    # Dashboard files
    dashboard_candidates = [
        (ROOT / "dashboard" / "index.html"),
        (ROOT / "dashboard.html"),
        (ROOT / "dashboard" / "enhanced_dashboard.py"),
        (ROOT / "tools" / "emit_health.py")
    ]
    
    found_dashboard = False
    for d in dashboard_candidates:
        if d.exists():
            ok(f"Dashboard component found: {d.relative_to(ROOT)}")
            found_dashboard = True
    
    if not found_dashboard:
        warn("No dashboard components found")

def check_ml_artifacts():
    section("7) ML artifacts & prediction service")
    # Look for model registry file(s) or directory
    candidates = [
        ROOT / "models",
        ROOT / "data" / "ml_models",
        ROOT / "ml" / "registry.json",
        ROOT / "src" / "ml",
    ]
    found = any(p.exists() for p in candidates)
    if found:
        ok("ML artifacts directory detected")
    else:
        warn("No ML artifacts detected — ok if you plan to train post-release")

    # Try to import prediction service entry point
    preds = [
        "src.ml.outlook",
        "ml.predict_ml",
        "ml.prediction_service",
        "tools.ml_outlook_bridge"
    ]
    for name in preds:
        if _import(name):
            ok(f"ML prediction module importable: {name}")
            break
    else:
        warn("No ML prediction module found")

def dry_run_staging():
    section("8) Order staging dry-run")
    # Test Phase 3 staging CLI
    cli_candidates = [
        ROOT / "scripts" / "stage_order_cli.py",
        ROOT / "tools" / "stage_order_cli.py",
    ]
    
    cli = None
    for c in cli_candidates:
        if c.exists():
            cli = c
            break
    
    if not cli:
        warn("No stage_order_cli.py found — skipping order staging test")
        return
        
    try:
        cmd = [
            sys.executable, str(cli),
            "--text", "test market view for release validation",
            "--symbol", "SPY"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
        if res.returncode == 0:
            ok("Phase 3 order staging dry-run successful")
        else:
            warn(f"Order staging issues: {res.stderr[:200] if res.stderr else res.stdout[:200]}")
    except Exception as e:
        warn(f"Order staging dry-run error: {e}")

def check_source_integrity():
    section("9) Source integrity & lint (lightweight)")
    # basic syntax check on key entrypoints
    entrypoints = [
        ROOT / "app_describer.py",
        ROOT / "main.py",
        ROOT / "validate_patch8.py",
        ROOT / "validate_patch7.py"
    ]
    
    syntax_ok = 0
    for p in entrypoints:
        if p.exists():
            try:
                subprocess.check_call([sys.executable, "-m", "py_compile", str(p)],
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                ok(f"Syntax OK: {p.relative_to(ROOT)}")
                syntax_ok += 1
            except Exception as e:
                fail(f"Syntax check failed: {p.relative_to(ROOT)} ({e})")
    
    if syntax_ok > 0:
        ok(f"Syntax validation passed for {syntax_ok} files")

def check_phase3_integration():
    section("10) Phase 3 integration validation")
    # Test Phase 3 components
    try:
        # Test schemas
        schemas = _import("src.phase3.schemas")
        if schemas:
            ok("Phase 3 schemas module importable")
        
        # Test orchestrator
        orch = _import("src.phase3.orchestrator")
        if orch:
            ok("Phase 3 orchestrator module importable")
            
        # Test synthesizer
        synth = _import("src.phase3.synthesizer")
        if synth:
            ok("Phase 3 synthesizer module importable")
            
        # Test gates
        gates = _import("src.phase3.gates")
        if gates:
            ok("Phase 3 gates module importable")
            
        # Quick integration test
        if all([schemas, orch, synth, gates]):
            from src.phase3.schemas import AnalysisRequest
            from src.phase3.orchestrator import LLMOrchestrator
            req = AnalysisRequest(user_text="test integration")
            orchestrator = LLMOrchestrator()
            view = orchestrator.analyze(req)
            ok("Phase 3 integration test successful")
            
    except Exception as e:
        warn(f"Phase 3 integration test failed: {e}")

def summary_and_exit():
    section("Summary")
    if FAILURES:
        print("Hard failures:")
        for f in FAILURES:
            print(f"  - {f}")
    if WARNINGS:
        print("\nWarnings:")
        for w in WARNINGS:
            print(f"  - {w}")

    print(f"\nResults: {len(FAILURES)} failures, {len(WARNINGS)} warnings")

    if FAILURES:
        print("\nExit code: 2 (hard failures) — DO NOT CUT RELEASE TAG.")
        sys.exit(2)
    elif WARNINGS:
        print("\nExit code: 1 (warnings present) — proceed with caution.")
        sys.exit(1)
    else:
        print("\nExit code: 0 (all good) — release may proceed.")
        sys.exit(0)

def main():
    print("Phase 3 Completion Gate — Validation, Staging, Health Checks\n")
    check_python()
    check_env_config()
    check_database_router()
    check_migrations()
    check_broker_reachability()
    check_health_and_dashboard()
    check_ml_artifacts()
    dry_run_staging()
    check_source_integrity()
    check_phase3_integration()
    summary_and_exit()

if __name__ == "__main__":
    main()