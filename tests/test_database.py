#!/usr/bin/env python3
"""
Test the database router functionality
"""
import sys
from pathlib import Path
import datetime as dt

# Add the project root to Python path
ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(ROOT))

from db.router import DB

def test_database():
    print("🧪 Testing EMO Database Router...")
    
    # Initialize database
    db = DB().connect()
    print(f"✅ Database connected: {db.kind}")
    
    # Test data
    test_rows = [
        {
            "symbol": "SPY",
            "ts": "2025-10-25T15:30:00Z",
            "open": 580.50,
            "high": 582.75,
            "low": 579.25,
            "close": 581.40,
            "volume": 1500000
        },
        {
            "symbol": "QQQ", 
            "ts": "2025-10-25T15:30:00Z",
            "open": 495.20,
            "high": 496.80,
            "low": 494.10,
            "close": 495.95,
            "volume": 850000
        }
    ]
    
    # Test upsert
    print("📊 Inserting test bars...")
    n = db.upsert_bars(test_rows)
    print(f"✅ Upserted {n} bars")
    
    # Test query
    print("🔍 Querying database...")
    if db.kind == "sqlite":
        cur = db.conn.cursor()
        cur.execute("SELECT symbol, ts, close, volume FROM bars ORDER BY symbol")
        rows = cur.fetchall()
        cur.close()
        print("📈 Current bars in database:")
        for row in rows:
            print(f"   {row[0]}: {row[1]} - Close: ${row[2]:.2f}, Volume: {row[3]:,}")
    
    print("✅ Database test complete!")

if __name__ == "__main__":
    test_database()