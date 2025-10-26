from __future__ import annotations
import os, sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS market_bars (
    ts TEXT NOT NULL,
    symbol TEXT NOT NULL,
    open REAL, high REAL, low REAL, close REAL, volume REAL,
    PRIMARY KEY (ts, symbol)
);

CREATE TABLE IF NOT EXISTS ml_outlook (
    ts TEXT NOT NULL,
    symbol TEXT NOT NULL,
    model TEXT NOT NULL,
    horizon TEXT NOT NULL,
    prediction REAL,
    confidence REAL,
    meta JSON,
    PRIMARY KEY (ts, symbol, model, horizon)
);

CREATE TABLE IF NOT EXISTS strategy_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    symbol TEXT NOT NULL,
    strategy TEXT NOT NULL,
    side TEXT NOT NULL,
    qty INTEGER NOT NULL,
    order_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    meta JSON,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS strategy_performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy TEXT NOT NULL,
    symbol TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    total_pnl REAL DEFAULT 0.0,
    win_rate REAL DEFAULT 0.0,
    sharpe_ratio REAL DEFAULT 0.0,
    max_drawdown REAL DEFAULT 0.0,
    trades_count INTEGER DEFAULT 0,
    meta JSON
);

CREATE INDEX IF NOT EXISTS idx_market_bars_symbol_ts ON market_bars(symbol, ts);
CREATE INDEX IF NOT EXISTS idx_ml_outlook_symbol_ts ON ml_outlook(symbol, ts);
CREATE INDEX IF NOT EXISTS idx_strategy_orders_strategy_ts ON strategy_orders(strategy, ts);
"""

class SQLiteDB:
    def __init__(self, file_path: str):
        self.file_path = file_path
        Path(os.path.dirname(self.file_path)).mkdir(parents=True, exist_ok=True)

    def connect(self):
        conn = sqlite3.connect(self.file_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def ensure_schema(self):
        with self.connect() as conn:
            conn.executescript(SCHEMA)
            conn.commit()
            
    def execute(self, sql: str, params=None):
        with self.connect() as conn:
            if params:
                return conn.execute(sql, params)
            else:
                return conn.execute(sql)
    
    def query(self, sql: str, params=None):
        with self.connect() as conn:
            if params:
                return conn.execute(sql, params).fetchall()
            else:
                return conn.execute(sql).fetchall()
    
    def executemany(self, sql: str, params_list):
        with self.connect() as conn:
            return conn.executemany(sql, params_list)