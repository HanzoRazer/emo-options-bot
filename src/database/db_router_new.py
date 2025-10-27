from __future__ import annotations
import os
from typing import Optional
from pathlib import Path

try:
    from sqlalchemy import create_engine
except Exception:  # keep import light and optional
    create_engine = None  # type: ignore

# Route by environment with explicit override:
#   EMO_DB_ENGINE in {"sqlite","postgres","timescale"}
#   EMO_ENV in {"development","staging","production"} (fallback)
#   EMO_DB_URL wins if provided.
_DEFAULT_SQLITE = Path("data") / "emo.sqlite"

def _default_sqlite_url() -> str:
    _DEFAULT_SQLITE.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{_DEFAULT_SQLITE.as_posix()}"

def resolve_db_url() -> str:
    url = os.getenv("EMO_DB_URL")
    if url:
        return url

    forced = (os.getenv("EMO_DB_ENGINE") or "").lower().strip()
    env = (os.getenv("EMO_ENV") or "development").lower().strip()

    if forced in {"postgres", "timescale"} or env in {"staging","production"}:
        # Require explicit EMO_DB_URL for network DBs
        url = os.getenv("EMO_DB_URL")
        if not url:
            # fail closed to sqlite if not configured
            return _default_sqlite_url()
        return url

    # development default
    return _default_sqlite_url()

def get_engine(echo: bool=False):
    if create_engine is None:
        raise RuntimeError("SQLAlchemy not installed. `pip install SQLAlchemy` to use DB features.")
    return create_engine(resolve_db_url(), echo=echo, future=True)