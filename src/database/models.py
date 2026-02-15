"""
EMO Options Bot - Database Models
Consolidated database layer supporting both analysis data and market bars
"""

import os
import sqlite3
import contextlib
import datetime as dt
from pathlib import Path
from contextlib import closing

# Configuration
EMO_ENV = os.getenv("EMO_ENV", "dev").lower()
ROOT = Path(__file__).resolve().parents[2]  # src/database/ -> project root
DATA_DIR = ROOT / "data"

# Database paths
SQLITE_BARS_PATH = DATA_DIR / "emo.sqlite"
SQLITE_ANALYSIS_PATH = DATA_DIR / "describer.db"

# Schema definitions
ANALYSIS_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_utc TEXT NOT NULL,
    regime TEXT NOT NULL,
    info_shock REAL NOT NULL,
    z_perp REAL NOT NULL,
    z_vix REAL NOT NULL,
    z_sent REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS symbols (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    close REAL,
    ret_5m REAL,
    atrp REAL,
    vol_z REAL,
    ivr REAL,
    skew_25d REAL,
    term_slope REAL,
    vix REAL,
    vix_change REAL,
    avg_sentiment REAL,
    sent_var REAL,
    avg_perplexity REAL,
    perp_z REAL,
    topic_entropy REAL,
    FOREIGN KEY(run_id) REFERENCES runs(id)
);
CREATE INDEX IF NOT EXISTS idx_runs_ts ON runs(ts_utc);
CREATE INDEX IF NOT EXISTS idx_symbols_run ON symbols(run_id);
"""

class DB:
    """
    Unified database class supporting both market bars and analysis data
    Supports SQLite (dev) and PostgreSQL/TimescaleDB (prod)
    """
    
    def __init__(self, db_type="bars"):
        """
        Initialize database connection
        
        Args:
            db_type: "bars" for market data, "analysis" for analysis results
        """
        self.kind = "sqlite"
        self.db_type = db_type
        self.conn = None
        
        # Determine database mode
        if EMO_ENV == "prod":
            try:
                import psycopg2, psycopg2.extras  # noqa: F401
                self.kind = "timescale"
            except Exception:
                self.kind = "sqlite"
    
    def connect(self):
        """Establish database connection and create tables"""
        if self.kind == "sqlite":
            return self._connect_sqlite()
        else:
            return self._connect_postgres()
    
    def _connect_sqlite(self):
        """Connect to SQLite database"""
        if self.db_type == "bars":
            db_path = SQLITE_BARS_PATH
        else:
            db_path = SQLITE_ANALYSIS_PATH
            
        # Ensure data directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect and configure
        self.conn = sqlite3.connect(str(db_path))
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        
        # Create appropriate tables
        if self.db_type == "bars":
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS bars (
                symbol TEXT NOT NULL,
                ts TEXT NOT NULL,
                open REAL, high REAL, low REAL, close REAL,
                volume INTEGER,
                PRIMARY KEY(symbol, ts)
            )
            """)
        else:
            self.conn.executescript(ANALYSIS_SCHEMA)
            
        self.conn.commit()
        return self
    
    def _connect_postgres(self):
        """Connect to PostgreSQL/TimescaleDB"""
        import psycopg2
        dsn = os.getenv("EMO_PG_DSN")
        self.conn = psycopg2.connect(dsn)
        
        with self.conn.cursor() as cur:
            if self.db_type == "bars":
                cur.execute("""
                CREATE TABLE IF NOT EXISTS bars (
                    symbol TEXT NOT NULL,
                    ts TIMESTAMPTZ NOT NULL,
                    open DOUBLE PRECISION, high DOUBLE PRECISION, 
                    low DOUBLE PRECISION, close DOUBLE PRECISION,
                    volume BIGINT,
                    PRIMARY KEY(symbol, ts)
                );
                """)
            else:
                # Adapt analysis schema for PostgreSQL
                postgres_analysis_schema = ANALYSIS_SCHEMA.replace("AUTOINCREMENT", "SERIAL")
                cur.execute(postgres_analysis_schema)
                
        self.conn.commit()
        return self
    
    # Market bars methods
    def upsert_bars(self, rows):
        """
        Insert or update market bars
        
        Args:
            rows: list of dicts with keys: symbol, ts(ISO8601), open, high, low, close, volume
            
        Returns:
            Number of rows processed
        """
        if not rows:
            return 0
            
        if self.kind == "sqlite":
            with contextlib.closing(self.conn.cursor()) as cur:
                cur.executemany("""
                INSERT INTO bars(symbol, ts, open, high, low, close, volume)
                VALUES (:symbol, :ts, :open, :high, :low, :close, :volume)
                ON CONFLICT(symbol, ts) DO UPDATE SET
                  open=excluded.open, high=excluded.high, low=excluded.low,
                  close=excluded.close, volume=excluded.volume
                """, rows)
            self.conn.commit()
            return len(rows)
        else:
            import psycopg2.extras
            with self.conn.cursor() as cur:
                psycopg2.extras.execute_batch(cur, """
                INSERT INTO bars(symbol, ts, open, high, low, close, volume)
                VALUES (%(symbol)s, %(ts)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s)
                ON CONFLICT (symbol, ts) DO UPDATE SET
                  open=EXCLUDED.open, high=EXCLUDED.high, low=EXCLUDED.low,
                  close=EXCLUDED.close, volume=EXCLUDED.volume
                """, rows, page_size=100)
                self.conn.commit()
                return len(rows)
    
    # Analysis data methods
    def insert_run(self, ts_utc, regime, info_shock, z_perp, z_vix, z_sent):
        """Insert analysis run record"""
        with closing(self.conn.cursor()) as cur:
            cur.execute(
                "INSERT INTO runs(ts_utc, regime, info_shock, z_perp, z_vix, z_sent) VALUES (?,?,?,?,?,?)",
                (ts_utc, regime, info_shock, z_perp, z_vix, z_sent)
            )
            run_id = cur.lastrowid
        self.conn.commit()
        return run_id
    
    def insert_symbol_row(self, run_id, row):
        """Insert symbol analysis data"""
        cols = ("run_id","symbol","close","ret_5m","atrp","vol_z","ivr","skew_25d","term_slope","vix",
                "vix_change","avg_sentiment","sent_var","avg_perplexity","perp_z","topic_entropy")
        vals = (run_id, row["symbol"], row["close"], row["ret_5m"], row["atrp"], row["vol_z"], row["ivr"],
                row["skew_25d"], row["term_slope"], row["vix"], row["vix_change"], row["avg_sentiment"],
                row["sent_var"], row["avg_perplexity"], row["perp_z"], row["topic_entropy"])
        with closing(self.conn.cursor()) as cur:
            cur.execute(
            "INSERT INTO symbols(run_id, symbol, close, ret_5m, atrp, vol_z, ivr, skew_25d, "
            "term_slope, vix, vix_change, avg_sentiment, sent_var, avg_perplexity, perp_z, topic_entropy) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            vals
        )
        self.conn.commit()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None


# Legacy compatibility functions
def connect(db_path="data/describer.db"):
    """Legacy function for backward compatibility"""
    full_path = ROOT / db_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(full_path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def ensure_schema(conn):
    """Legacy function for backward compatibility"""
    with closing(conn.cursor()) as cur:
        cur.executescript(ANALYSIS_SCHEMA)
    conn.commit()

def insert_run(conn, ts_utc, regime, info_shock, z_perp, z_vix, z_sent):
    """Legacy function for backward compatibility"""
    with closing(conn.cursor()) as cur:
        cur.execute(
            "INSERT INTO runs(ts_utc, regime, info_shock, z_perp, z_vix, z_sent) VALUES (?,?,?,?,?,?)",
            (ts_utc, regime, info_shock, z_perp, z_vix, z_sent)
        )
        run_id = cur.lastrowid
    conn.commit()
    return run_id

def insert_symbol_row(conn, run_id, row):
    """Legacy function for backward compatibility"""
    cols = ("run_id","symbol","close","ret_5m","atrp","vol_z","ivr","skew_25d","term_slope","vix",
            "vix_change","avg_sentiment","sent_var","avg_perplexity","perp_z","topic_entropy")
    vals = (run_id, row["symbol"], row["close"], row["ret_5m"], row["atrp"], row["vol_z"], row["ivr"],
            row["skew_25d"], row["term_slope"], row["vix"], row["vix_change"], row["avg_sentiment"],
            row["sent_var"], row["avg_perplexity"], row["perp_z"], row["topic_entropy"])
    with closing(conn.cursor()) as cur:
        cur.execute(
            "INSERT INTO symbols(run_id, symbol, close, ret_5m, atrp, vol_z, ivr, skew_25d, "
            "term_slope, vix, vix_change, avg_sentiment, sent_var, avg_perplexity, perp_z, topic_entropy) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            vals
        )
    conn.commit()


def get_db_connection(db_type="bars"):
    """
    Get database connection for enhanced components.
    Returns a sqlite3 connection to the appropriate database.
    """
    if db_type == "bars":
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(SQLITE_BARS_PATH)
    elif db_type == "analysis":
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(SQLITE_ANALYSIS_PATH)
    else:
        raise ValueError(f"Unknown db_type: {db_type}")


def get_enhanced_db():
    """Get database instance for enhanced features."""
    return DB(db_type="bars")