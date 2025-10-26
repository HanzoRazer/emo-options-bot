from __future__ import annotations
import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from utils.enhanced_config import Config

"""
Database Router
---------------
Chooses SQLite (dev/staging) vs Timescale (prod) based on env vars:
  - EMO_ENV=dev|staging|prod
  - EMO_DB=sqlite|timescale
  - EMO_SQLITE_PATH=./data/emo.sqlite
  - EMO_PG_DSN=postgresql+psycopg2://user:pass@host:5432/emo
"""

def db_url_from_env(cfg: Optional[Config] = None) -> str:
    cfg = cfg or Config()
    emo_db = cfg.get("EMO_DB", "sqlite").lower()
    if emo_db == "timescale":
        dsn = cfg.get("EMO_PG_DSN")
        if not dsn:
            raise RuntimeError("EMO_DB=timescale but EMO_PG_DSN is not set")
        return dsn
    # default sqlite
    sqlite_path = cfg.get("EMO_SQLITE_PATH", "./data/emo.sqlite")
    sqlite_path = os.path.abspath(sqlite_path)
    return f"sqlite:///{sqlite_path}"

def get_engine(cfg: Optional[Config] = None, echo: bool = False) -> Engine:
    url = db_url_from_env(cfg)
    if url.startswith("sqlite:///"):
        # pragmatic defaults for SQLite
        eng = create_engine(url, echo=echo, future=True)
    else:
        # Timescale/Postgres
        eng = create_engine(url, pool_pre_ping=True, pool_size=5, max_overflow=5, future=True)
    return eng

if __name__ == "__main__":
    c = Config()
    print(db_url_from_env(c))