from __future__ import annotations
import psycopg2
from psycopg2.extras import RealDictCursor

SCHEMA = """
CREATE TABLE IF NOT EXISTS market_bars (
    ts TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    open DOUBLE PRECISION, 
    high DOUBLE PRECISION, 
    low DOUBLE PRECISION, 
    close DOUBLE PRECISION, 
    volume DOUBLE PRECISION,
    PRIMARY KEY (ts, symbol)
);

CREATE TABLE IF NOT EXISTS ml_outlook (
    ts TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    model TEXT NOT NULL,
    horizon TEXT NOT NULL,
    prediction DOUBLE PRECISION,
    confidence DOUBLE PRECISION,
    meta JSONB,
    PRIMARY KEY (ts, symbol, model, horizon)
);

CREATE TABLE IF NOT EXISTS strategy_orders (
    id SERIAL PRIMARY KEY,
    ts TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    strategy TEXT NOT NULL,
    side TEXT NOT NULL,
    qty INTEGER NOT NULL,
    order_type TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    meta JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS strategy_performance (
    id SERIAL PRIMARY KEY,
    strategy TEXT NOT NULL,
    symbol TEXT NOT NULL,
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    total_pnl DOUBLE PRECISION DEFAULT 0.0,
    win_rate DOUBLE PRECISION DEFAULT 0.0,
    sharpe_ratio DOUBLE PRECISION DEFAULT 0.0,
    max_drawdown DOUBLE PRECISION DEFAULT 0.0,
    trades_count INTEGER DEFAULT 0,
    meta JSONB
);

CREATE INDEX IF NOT EXISTS idx_market_bars_symbol_ts ON market_bars(symbol, ts);
CREATE INDEX IF NOT EXISTS idx_ml_outlook_symbol_ts ON ml_outlook(symbol, ts);
CREATE INDEX IF NOT EXISTS idx_strategy_orders_strategy_ts ON strategy_orders(strategy, ts);
"""

class TimescaleDB:
    def __init__(self, url: str):
        self.url = url

    def connect(self):
        return psycopg2.connect(self.url, cursor_factory=RealDictCursor)

    def ensure_schema(self):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA)
                # Create hypertables for time-series data
                try:
                    cur.execute("SELECT create_hypertable('market_bars','ts', if_not_exists => TRUE);")
                    cur.execute("SELECT create_hypertable('ml_outlook','ts', if_not_exists => TRUE);")
                    cur.execute("SELECT create_hypertable('strategy_orders','ts', if_not_exists => TRUE);")
                except Exception as e:
                    # Hypertables might already exist
                    print(f"Hypertable creation note: {e}")
            conn.commit()
            
    def execute(self, sql: str, params=None):
        with self.connect() as conn:
            with conn.cursor() as cur:
                if params:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
                conn.commit()
    
    def query(self, sql: str, params=None):
        with self.connect() as conn:
            with conn.cursor() as cur:
                if params:
                    cur.execute(sql, params)
                else:
                    cur.execute(sql)
                return cur.fetchall()
    
    def executemany(self, sql: str, params_list):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.executemany(sql, params_list)
                conn.commit()