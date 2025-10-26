"""
Lightweight SQLAlchemy session helper for the trading database.
Chooses DB URL from env or configuration with sane defaults.
"""
from __future__ import annotations
import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ENV controls:
#   EMO_DB_URL      - full DB url (e.g., sqlite:///data/emo.sqlite)
#   EMO_ENV         - 'dev'|'staging'|'prod' (optional, only used if router not present)
# Defaults to local SQLite in ./data/emo.sqlite

_DEFAULT_SQLITE = "sqlite:///data/emo.sqlite"

_ENGINE = None
_Session = None

def _db_url() -> str:
    # Highest priority: explicit URL
    url = os.getenv("EMO_DB_URL")
    if url:
        return url
    # Fallback: local SQLite (router may override elsewhere in your code)
    return _DEFAULT_SQLITE

def _init_engine(echo: bool = False):
    global _ENGINE, _Session
    if _ENGINE is None:
        _ENGINE = create_engine(_db_url(), echo=echo, future=True)
        _Session = sessionmaker(bind=_ENGINE, autoflush=False, autocommit=False, future=True)
    return _ENGINE, _Session

def get_engine(echo: bool = False):
    eng, _ = _init_engine(echo=echo)
    return eng

def get_session(echo: bool = False):
    _, Session = _init_engine(echo=echo)
    return Session()

@contextmanager
def session_scope(echo: bool = False) -> Generator:
    """
    Provide a transactional scope around a series of operations.
    Usage:
        with session_scope() as s:
            s.execute(...)
    """
    sess = get_session(echo=echo)
    try:
        yield sess
        sess.commit()
    except Exception:
        sess.rollback()
        raise
    finally:
        sess.close()

def quick_health_check() -> dict:
    "Minimal DB check for health server."
    try:
        with session_scope() as s:
            s.execute(text("SELECT 1"))
        return {"db": "ok", "url": _db_url()}
    except Exception as e:
        return {"db": "error", "error": str(e), "url": _db_url()}