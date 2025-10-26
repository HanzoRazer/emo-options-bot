import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "emo.sqlite"

print(f"Checking database at: {DB_PATH}")

if not DB_PATH.exists():
    print("Database does not exist")
else:
    conn = sqlite3.connect(DB_PATH)
    
    # Check if bars table exists
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f"Tables: {[t[0] for t in tables]}")
    
    if ('bars',) in tables:
        schema = conn.execute("PRAGMA table_info(bars)").fetchall()
        print(f"Bars table schema: {schema}")
        
        # Check sample data
        count = conn.execute("SELECT COUNT(*) FROM bars").fetchone()[0]
        print(f"Bars count: {count}")
        
        if count > 0:
            sample = conn.execute("SELECT * FROM bars LIMIT 1").fetchone()
            print(f"Sample row: {sample}")
    
    conn.close()