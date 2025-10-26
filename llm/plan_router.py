from __future__ import annotations
import os, json, uuid, datetime as dt
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from exec.safe_submit import SafeSubmitter
except Exception:
    SafeSubmitter = None  # Gracious fallback

ROOT = Path(__file__).resolve().parents[1]
STAGING_DIR = ROOT / "ops" / "staged_orders"
SCHEMA_FILE = ROOT / "config" / "schema" / "llm_plan.schema.json"  # optional
STAGING_DIR.mkdir(parents=True, exist_ok=True)

def _now_utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def _validate_plan(plan: Dict[str, Any]) -> None:
    """Minimal defensive checks. Keep lightweight to avoid runtime friction."""
    required_top = ["strategy_type", "legs"]
    for k in required_top:
        if k not in plan:
            raise ValueError(f"plan missing required field: {k}")
    if not isinstance(plan["legs"], list) or not plan["legs"]:
        raise ValueError("plan.legs must be a non-empty list")
    for leg in plan["legs"]:
        for field in ["action", "instrument", "strike", "quantity"]:
            if field not in leg:
                raise ValueError(f"leg missing required field: {field}")

def _stage_filename(symbol: str, strategy: str) -> Path:
    stamp = int(dt.datetime.now().timestamp())
    rand = uuid.uuid4().hex[:8]
    name = f"{stamp}_{symbol}_{strategy}_{rand}.json"
    return STAGING_DIR / name

def to_staged_payload(plan: Dict[str, Any], meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Transform LLM plan → staged order payload that downstream tools understand."""
    # Expect plan.shape:
    # { "strategy_type": "iron_condor",
    #   "symbol": "SPY", "expiry": "2025-11-15", "legs":[...],
    #   "risk_constraints":{"max_loss":1500}, "notes": "...", ... }
    symbol = plan.get("symbol", "UNKNOWN")
    payload = {
        "created_ts": _now_utc_iso(),
        "symbol": symbol,
        "strategy_type": plan["strategy_type"],
        "legs": plan["legs"],
        "expiry": plan.get("expiry"),
        "risk_constraints": plan.get("risk_constraints", {}),
        "notes": plan.get("notes", ""),
        "source": "llm",
        "meta": meta or {},
    }
    return payload

def route_plan(plan: Dict[str, Any],
               mode: str = None,
               broker: str = None,
               meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    mode:
      - 'stage' (default): write to ops/staged_orders/*.json
      - 'paper': submit via broker paper endpoint (if enabled)
      - 'live':  submit live (EXPLICITLY guarded in SafeSubmitter)
    """
    _validate_plan(plan)
    payload = to_staged_payload(plan, meta=meta or {})

    env_mode = (mode or os.getenv("EMO_ORDER_MODE", "stage")).lower()
    env_broker = (broker or os.getenv("EMO_BROKER", "alpaca")).lower()

    if env_mode == "stage" or SafeSubmitter is None:
        out = _stage_filename(payload["symbol"], payload["strategy_type"])
        with open(out, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        return {"status": "staged", "file": str(out), "mode": env_mode}

    # Otherwise go via SafeSubmitter
    submitter = SafeSubmitter(broker=env_broker, order_mode=env_mode)
    submitted = submitter.submit_strategy(payload)
    return {"status": "submitted", "details": submitted, "mode": env_mode}