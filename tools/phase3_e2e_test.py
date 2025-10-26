#!/usr/bin/env python
from __future__ import annotations
import json, sys, os
sys.path.insert(0, os.path.abspath("."))  # ensure local src is importable

from src.phase3.test_harness import run_phase3_flow

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def _ok(msg: str):
    print(f"{GREEN}OK: {msg}{RESET}")

def _warn(msg: str):
    print(f"{YELLOW}WARN: {msg}{RESET}")

def _err(msg: str):
    print(f"{RED}ERR: {msg}{RESET}")

def main():
    print("\n== Phase 3 End-to-End Acceptance Test ==")
    tests = [
        ("I think SPY will trade sideways next 2 weeks", ["SPY","QQQ"]),
        ("QQQ could be volatile into earnings", ["QQQ","SPY"]),
        ("Mildly bullish outlook on SPY; income preferred", ["SPY"]),
    ]
    passed = 0
    for text, symbols in tests:
        out = run_phase3_flow(text, symbols=symbols, equity=100_000.0)
        artp = out["artifact_path"]
        res  = out["result"]
        status = res.get("status")
        order = res.get("order", {})
        legs  = order.get("legs", [])
        if status not in ("ok","blocked"):
            _fail("Invalid status")
            continue
        if not isinstance(legs, list) or len(legs) == 0:
            _fail("No legs produced")
            continue
        if status == "blocked":
            _warn(f"Order blocked by risk gate (expected in some configs): {artp}")
        else:
            _ok(f"Order OK: {order.get('strategy')} {order.get('symbol','?')} (legs={len(legs)})")
            _ok(f"Staged artifact: {artp}")
        passed += 1
    print(f"\n{GREEN}All {passed}/{len(tests)} test flows executed.{RESET}\n")

if __name__ == "__main__":
    main()