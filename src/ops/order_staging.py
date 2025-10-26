"""
Lightweight order staging helper.
Writes validated trade drafts to src/ops/drafts as YAML (default) or JSON.
Safe to call from Phase3TradingSystem after risk gates pass.
"""
from __future__ import annotations
import os, json, uuid, datetime as dt
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import yaml  # PyYAML
except Exception:
    yaml = None

DEFAULT_DIR = Path("src/ops/drafts")

def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

def _sanitize_filename(s: str) -> str:
    return "".join(c for c in s if c.isalnum() or c in ("-", "_", "."))[:80]

def _now_utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def write_draft(
    trade: Dict[str, Any],
    *,
    drafts_dir: Optional[str] = None,
    fmt: str = "yaml",
    meta: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Persist a validated trade to drafts as {ts}_{symbol}_{action}_{rand}.yaml/json
    - trade: normalized dict (legs, strategy_type, risk, etc.)
    - drafts_dir: override destination folder (default: src/ops/drafts)
    - fmt: "yaml" or "json"
    - meta: optional metadata (user, note, source, confidence, llm_model, etc.)
    Returns: Path to the written draft file.
    """
    dd = Path(drafts_dir) if drafts_dir else DEFAULT_DIR
    _ensure_dir(dd)

    symbol = (trade.get("symbol") or trade.get("underlying") or "UNK").upper()
    primary_action = trade.get("action") or trade.get("strategy_type") or "trade"
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    rand = uuid.uuid4().hex[:8]

    fname_base = f"{ts}_{_sanitize_filename(symbol)}_{_sanitize_filename(str(primary_action))}_{rand}"
    if fmt.lower() == "json":
        path = dd / f"{fname_base}.json"
        payload = {
            "version": 1,
            "created_utc": _now_utc_iso(),
            "type": "trade_draft",
            "trade": trade,
            "meta": meta or {},
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return path

    # default YAML
    if yaml is None:
        # fall back to JSON if PyYAML not installed
        path = dd / f"{fname_base}.json"
        payload = {
            "version": 1,
            "created_utc": _now_utc_iso(),
            "type": "trade_draft",
            "trade": trade,
            "meta": meta or {},
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        return path

    path = dd / f"{fname_base}.yaml"
    payload = {
        "version": 1,
        "created_utc": _now_utc_iso(),
        "type": "trade_draft",
        "trade": trade,
        "meta": meta or {},
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=True)
    return path

__all__ = ["write_draft"]