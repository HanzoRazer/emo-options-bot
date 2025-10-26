from __future__ import annotations
import math, time, datetime as dt
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

@dataclass
class Snapshot:
    symbol: str
    price: float
    iv: float            # simple "blended" IV for demo
    spread: float        # bid/ask width
    ts: str

def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def _approx_iv(symbol: str) -> float:
    # crude IV heuristic (replace with real IV if available)
    base = 0.18
    bump = 0.06 if symbol in ("QQQ","IWM") else 0.03
    return round(base + bump, 4)

def _approx_spread(symbol: str, price: float) -> float:
    # basic spread heuristic
    return round(max(0.01, min(0.5, price * 0.0008)), 3)

def _price_seed(symbol: str) -> float:
    return {
        "SPY": 475.0,
        "QQQ": 410.0,
        "IWM": 210.0,
        "DIA": 379.0,
    }.get(symbol, 100.0)

def generate_snapshot(symbols: List[str]) -> Dict[str, Snapshot]:
    out: Dict[str, Snapshot] = {}
    t = time.time()
    for s in symbols:
        base = _price_seed(s)
        # wiggle the price in a smooth way for testing
        w = 1.0 + 0.004 * math.sin(t / 60.0 + hash(s) % 17)
        px = round(base * w, 2)
        out[s] = Snapshot(
            symbol=s,
            price=px,
            iv=_approx_iv(s),
            spread=_approx_spread(s, px),
            ts=_now_iso(),
        )
    return out

def to_dict(snapshots: Dict[str, Snapshot]) -> Dict[str, dict]:
    return {k: asdict(v) for k, v in snapshots.items()}