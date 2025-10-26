import os, requests, datetime as dt, time
from pathlib import Path
from db.router import DB

ALPACA_DATA_URL = os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets/v2")
KEY = os.getenv("ALPACA_KEY_ID", "")
SEC = os.getenv("ALPACA_SECRET_KEY", "")
SYMBOLS = [s.strip().upper() for s in os.getenv("EMO_SYMBOLS", "SPY,QQQ").split(",") if s.strip()]

def _headers():
    return {
        "APCA-API-KEY-ID": KEY,
        "APCA-API-SECRET-KEY": SEC
    }

def fetch_latest_bar(symbol: str):
    # 1-min bar, limit=1
    url = f"{ALPACA_DATA_URL}/stocks/{symbol}/bars"
    params = {"timeframe": "1Min", "limit": 1}
    r = requests.get(url, headers=_headers(), params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    bars = data.get("bars") or data.get("results") or []
    if not bars:
        return None
    b = bars[-1]
    # Alpaca returns ISO8601 (e.g. 2024-01-01T15:31:00Z)
    return {
        "symbol": symbol,
        "ts": b.get("t") or b.get("timestamp") or b.get("time"),
        "open": b.get("o"),
        "high": b.get("h"),
        "low": b.get("l"),
        "close": b.get("c"),
        "volume": b.get("v")
    }

def main_once():
    if not KEY or not SEC:
        raise RuntimeError("ALPACA credentials missing (ALPACA_KEY_ID / ALPACA_SECRET_KEY)")
    db = DB().connect()
    rows = []
    for sym in SYMBOLS:
        try:
            bar = fetch_latest_bar(sym)
            if bar and bar["ts"]:
                rows.append(bar)
        except Exception as e:
            print(f"[live_logger] {sym} error: {e}")
    if rows:
        n = db.upsert_bars(rows)
        print(f"[live_logger] upserted {n} bars")

if __name__ == "__main__":
    main_once()