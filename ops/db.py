
import os, sqlite3
from contextlib import closing

SCHEMA = """
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

def connect(db_path="ops/describer.db"):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn

def ensure_schema(conn):
    with closing(conn.cursor()) as cur:
        cur.executescript(SCHEMA)
    conn.commit()

def insert_run(conn, ts_utc, regime, info_shock, z_perp, z_vix, z_sent):
    with closing(conn.cursor()) as cur:
        cur.execute(
            "INSERT INTO runs(ts_utc, regime, info_shock, z_perp, z_vix, z_sent) VALUES (?,?,?,?,?,?)",
            (ts_utc, regime, info_shock, z_perp, z_vix, z_sent)
        )
        run_id = cur.lastrowid
    conn.commit()
    return run_id

def insert_symbol_row(conn, run_id, row):
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
