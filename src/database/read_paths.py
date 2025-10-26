"""
Read paths for health server: fetch current positions and recent orders.
This version is schema-tolerant:
  - Tries 'positions' and 'orders' tables if present
  - Works with SQLite defaults; can be extended for Timescale/Postgres
"""
from __future__ import annotations
from typing import List, Dict, Any
from sqlalchemy import inspect, text

from .trading_session import session_scope

def _has_table(session, name: str) -> bool:
    insp = inspect(session.bind)
    return insp.has_table(name)

def fetch_positions(limit: int = 100) -> List[Dict[str, Any]]:
    with session_scope() as s:
        rows: List[Dict[str, Any]] = []
        # Try a few common table names/shapes
        if _has_table(s, "positions"):
            q = text("""
                SELECT
                    COALESCE(symbol, underlying, '') AS symbol,
                    COALESCE(quantity, qty, 0)      AS quantity,
                    COALESCE(avg_price, 0)          AS avg_price,
                    COALESCE(pnl, 0)                AS pnl,
                    COALESCE(updated_at, created_at) AS ts
                FROM positions
                ORDER BY ts DESC
                LIMIT :lim
            """)
            for r in s.execute(q, {"lim": limit}).mappings():
                rows.append(dict(r))
        return rows

def fetch_recent_orders(limit: int = 100) -> List[Dict[str, Any]]:
    with session_scope() as s:
        rows: List[Dict[str, Any]] = []
        if _has_table(s, "orders"):
            q = text("""
                SELECT
                    COALESCE(id, order_id, '')       AS id,
                    COALESCE(symbol, '')             AS symbol,
                    COALESCE(side, '')               AS side,
                    COALESCE(type, order_type, '')   AS type,
                    COALESCE(qty, quantity, 0)       AS qty,
                    COALESCE(status, '')             AS status,
                    COALESCE(created_at, ts)         AS ts
                FROM orders
                ORDER BY COALESCE(created_at, ts) DESC
                LIMIT :lim
            """)
            for r in s.execute(q, {"lim": limit}).mappings():
                rows.append(dict(r))
        return rows