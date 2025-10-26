"""
EMO Options Bot - Live Data Collector
Real-time market data collection from Alpaca Markets API
"""

import os
import requests
import datetime as dt
import time
from pathlib import Path
from .models import DB

# Configuration
ALPACA_DATA_URL = os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets/v2")
KEY = os.getenv("ALPACA_KEY_ID", "")
SEC = os.getenv("ALPACA_SECRET_KEY", "")
SYMBOLS = [s.strip().upper() for s in os.getenv("EMO_SYMBOLS", "SPY,QQQ").split(",") if s.strip()]

def _headers():
    """Generate Alpaca API headers"""
    return {
        "APCA-API-KEY-ID": KEY,
        "APCA-API-SECRET-KEY": SEC
    }

def fetch_latest_bar(symbol: str):
    """
    Fetch the latest 1-minute bar for a symbol from Alpaca
    
    Args:
        symbol: Stock symbol (e.g., "SPY")
        
    Returns:
        dict: Bar data with OHLCV information or None if no data
    """
    url = f"{ALPACA_DATA_URL}/stocks/{symbol}/bars"
    params = {"timeframe": "1Min", "limit": 1}
    
    try:
        r = requests.get(url, headers=_headers(), params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        
        bars = data.get("bars") or data.get("results") or []
        if not bars:
            return None
            
        b = bars[-1]
        return {
            "symbol": symbol,
            "ts": b.get("t") or b.get("timestamp") or b.get("time"),
            "open": b.get("o"),
            "high": b.get("h"),
            "low": b.get("l"),
            "close": b.get("c"),
            "volume": b.get("v")
        }
    except Exception as e:
        print(f"[data_collector] {symbol} error: {e}")
        return None

def collect_live_data():
    """
    Collect live data for all configured symbols and store in database
    
    Returns:
        int: Number of bars successfully stored
    """
    if not KEY or not SEC:
        raise RuntimeError("ALPACA credentials missing (ALPACA_KEY_ID / ALPACA_SECRET_KEY)")
    
    # Connect to bars database
    db = DB(db_type="bars").connect()
    rows = []
    
    # Fetch data for each symbol
    for sym in SYMBOLS:
        try:
            bar = fetch_latest_bar(sym)
            if bar and bar["ts"]:
                rows.append(bar)
        except Exception as e:
            print(f"[data_collector] {sym} error: {e}")
    
    # Store in database
    if rows:
        n = db.upsert_bars(rows)
        print(f"[data_collector] upserted {n} bars")
        return n
    
    return 0

def main_once():
    """Legacy compatibility function"""
    return collect_live_data()

if __name__ == "__main__":
    collect_live_data()