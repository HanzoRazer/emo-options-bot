import os, sqlite3, contextlib, datetime as dt
from pathlib import Path

EMO_ENV = os.getenv("EMO_ENV", "dev").lower()
ROOT = Path(__file__).resolve().parents[1]
SQLITE_PATH = ROOT / "ops" / "emo.sqlite"

class DB:
    def __init__(self):
        self.kind = "sqlite"
        self.conn = None
        if EMO_ENV == "prod":
            # Timescale/Postgres path (enable when you're ready)
            try:
                import psycopg2, psycopg2.extras  # noqa: F401
                self.kind = "timescale"
            except Exception:
                self.kind = "sqlite"

    def connect(self):
        if self.kind == "sqlite":
            SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(str(SQLITE_PATH))
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS bars (
                symbol TEXT NOT NULL,
                ts TEXT NOT NULL,
                open REAL, high REAL, low REAL, close REAL,
                volume INTEGER,
                PRIMARY KEY(symbol, ts)
            )
            """)
            self.conn.commit()
        else:
            # Example DSN: use EMO_PG_DSN env (e.g. postgresql://user:pass@host:5432/db)
            import psycopg2
            dsn = os.getenv("EMO_PG_DSN")
            self.conn = psycopg2.connect(dsn)
            with self.conn.cursor() as cur:
                cur.execute("""
                CREATE TABLE IF NOT EXISTS bars (
                    symbol TEXT NOT NULL,
                    ts TIMESTAMPTZ NOT NULL,
                    open DOUBLE PRECISION, high DOUBLE PRECISION, low DOUBLE PRECISION, close DOUBLE PRECISION,
                    volume BIGINT,
                    PRIMARY KEY(symbol, ts)
                );
                """)
                self.conn.commit()
        return self

    def upsert_bars(self, rows):
        """
        rows: list of dicts with keys: symbol, ts(ISO8601), open, high, low, close, volume
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