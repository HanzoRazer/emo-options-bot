"""
DB Router: choose SQLite (default) or Timescale/Postgres based on EMO_ENV.

Usage:
  from src.database.router import get_db
  db = get_db()                  # auto-selects
  db.execute("CREATE TABLE IF NOT EXISTS ...")
  rows = db.query("SELECT * FROM table WHERE ts >= ?", (cutoff,))

Env:
  EMO_ENV=production           -> try Timescale first
  TIMESCALE_URL=postgres://user:pass@host:5432/dbname
  EMO_DB_PATH=data/describer.db (sqlite fallback / dev)

Dependencies:
  - sqlite3 (stdlib) always available
  - psycopg (optional) if using Timescale/Postgres
"""

from __future__ import annotations
import os
import sqlite3
from pathlib import Path
from typing import Any, Iterable, Optional, Sequence, Tuple, List

# Project paths
ROOT = Path(__file__).resolve().parents[2]  # src/database/ -> project root
DATA_DIR = ROOT / "data"

PSYCOPG_AVAILABLE = False
try:
    import psycopg  # type: ignore
    PSYCOPG_AVAILABLE = True
except Exception:
    pass

class BaseDB:
    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> None:
        raise NotImplementedError
    def query(self, sql: str, params: Optional[Sequence[Any]] = None) -> List[Tuple]:
        raise NotImplementedError
    def executemany(self, sql: str, seq_of_params: Iterable[Sequence[Any]]) -> None:
        raise NotImplementedError
    def close(self) -> None:
        raise NotImplementedError

class SQLiteDB(BaseDB):
    def __init__(self, path: str):
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.conn = sqlite3.connect(path, timeout=30)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA temp_store=MEMORY")
        
    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> None:
        self.conn.execute(sql, params or [])
        self.conn.commit()
        
    def executemany(self, sql: str, seq_of_params: Iterable[Sequence[Any]]) -> None:
        self.conn.executemany(sql, seq_of_params)
        self.conn.commit()
        
    def query(self, sql: str, params: Optional[Sequence[Any]] = None) -> List[Tuple]:
        cur = self.conn.execute(sql, params or [])
        return cur.fetchall()
        
    def close(self) -> None:
        self.conn.close()

class TimescaleDB(BaseDB):
    def __init__(self, dsn: str):
        if not PSYCOPG_AVAILABLE:
            raise RuntimeError("psycopg is not installed; cannot use TimescaleDB")
        # autocommit; simple connection for app use
        self.conn = psycopg.connect(dsn, autocommit=True)
        
    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> None:
        with self.conn.cursor() as cur:
            cur.execute(sql, params or ())
            
    def executemany(self, sql: str, seq_of_params: Iterable[Sequence[Any]]) -> None:
        with self.conn.cursor() as cur:
            for params in seq_of_params:
                cur.execute(sql, params)
                
    def query(self, sql: str, params: Optional[Sequence[Any]] = None) -> List[Tuple]:
        with self.conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()
            
    def close(self) -> None:
        self.conn.close()

def get_db() -> BaseDB:
    """Get database connection based on environment configuration"""
    env = (os.environ.get("EMO_ENV") or "development").lower()
    ts_url = os.environ.get("TIMESCALE_URL")
    
    # Try Timescale/Postgres if production environment
    if env in ("prod", "production", "timescale") and ts_url:
        try:
            return TimescaleDB(ts_url)
        except Exception as e:
            print(f"[DB Router] Timescale requested but unavailable: {e}. Falling back to SQLite.")
    
    # Default to SQLite
    path = os.environ.get("EMO_DB_PATH") or str(DATA_DIR / "describer.db")
    return SQLiteDB(path)

# Optional helper: create minimal tables used by describer & analytics
def ensure_minimum_schema(db: BaseDB) -> None:
    """Create essential tables for EMO Options Bot"""
    db.execute("""
    CREATE TABLE IF NOT EXISTS equity_curve(
        ts      TEXT PRIMARY KEY,
        equity  REAL NOT NULL
    )""")
    
    db.execute("""
    CREATE TABLE IF NOT EXISTS market_bars(
        ts      TEXT NOT NULL,
        symbol  TEXT NOT NULL,
        open    REAL, high REAL, low REAL, close REAL, volume REAL,
        PRIMARY KEY (ts, symbol)
    )""")
    
    db.execute("""
    CREATE TABLE IF NOT EXISTS iv_history(
        ts      TEXT NOT NULL,
        symbol  TEXT NOT NULL,
        iv_rank REAL,
        PRIMARY KEY (ts, symbol)
    )""")
    
    db.execute("""
    CREATE TABLE IF NOT EXISTS risk_metrics(
        ts              TEXT PRIMARY KEY,
        equity          REAL NOT NULL,
        positions_count INTEGER DEFAULT 0,
        risk_used       REAL DEFAULT 0.0,
        risk_cap        REAL DEFAULT 0.0,
        risk_util       REAL DEFAULT 0.0,
        beta_exposure   REAL DEFAULT 0.0,
        drawdown        REAL DEFAULT 0.0
    )""")
    
    db.execute("""
    CREATE TABLE IF NOT EXISTS position_history(
        ts          TEXT NOT NULL,
        symbol      TEXT NOT NULL,
        qty         REAL NOT NULL,
        mark        REAL NOT NULL,
        value       REAL NOT NULL,
        max_loss    REAL NOT NULL,
        beta        REAL DEFAULT 1.0,
        sector      TEXT,
        PRIMARY KEY (ts, symbol)
    )""")
    
    print("[DB Router] Minimum schema ensured")