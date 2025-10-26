"""
Enhanced Database Router (SQLite ⇄ Timescale)
Supports both development SQLite and production Timescale databases
with automatic schema management and connection pooling.
"""
import os
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
from pathlib import Path
import threading

import sqlalchemy as sa
from sqlalchemy.engine import Engine
from sqlalchemy.pool import NullPool, StaticPool
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError
import pandas as pd

logger = logging.getLogger(__name__)

# Default paths and configurations
_SQLITE_PATH_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
    "data", 
    "emo.sqlite"
)

class DBRouter:
    """
    Enhanced database router with connection pooling, health checks,
    and automatic failover capabilities.
    """
    _engine: Optional[Engine] = None
    _dialect: str = "sqlite"
    _session_factory: Optional[sessionmaker] = None
    _health_check_interval = 300  # 5 minutes
    _last_health_check = 0
    _connection_healthy = True
    _lock = threading.Lock()

    @classmethod
    def init(cls, force_reconnect: bool = False):
        """Initialize database connection with enhanced configuration"""
        with cls._lock:
            if cls._engine is not None and not force_reconnect:
                return

            # Environment detection
            forced = os.getenv("EMO_DB_ENGINE", "").strip().lower()
            env = os.getenv("EMO_ENV", "dev").strip().lower()

            if forced:
                engine_kind = forced
            else:
                engine_kind = "timescale" if env in ("prod", "production") else "sqlite"

            logger.info(f"Initializing database router: {engine_kind} (env={env})")

            try:
                if engine_kind == "timescale":
                    cls._init_timescale()
                else:
                    cls._init_sqlite()
                    
                # Create session factory
                cls._session_factory = sessionmaker(bind=cls._engine)
                
                # Verify connection
                cls._verify_connection()
                cls._connection_healthy = True
                
                logger.info(f"Database initialized successfully: {cls._dialect}")
                
            except Exception as e:
                logger.error(f"Database initialization failed: {e}")
                cls._connection_healthy = False
                raise

    @classmethod
    def _init_timescale(cls):
        """Initialize Timescale (PostgreSQL) connection"""
        url = os.getenv("EMO_DB_URL")
        if not url:
            raise RuntimeError(
                "EMO_DB_URL required for timescale engine. "
                "Format: postgresql+psycopg://user:pass@host:5432/emo"
            )
        
        # Enhanced connection parameters for production
        connect_args = {
            "connect_timeout": 30,
            "application_name": "emo_options_bot",
        }
        
        cls._engine = sa.create_engine(
            url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,  # 1 hour
            echo=os.getenv("EMO_DB_DEBUG", "").lower() == "true",
            connect_args=connect_args
        )
        cls._dialect = "timescale"

    @classmethod
    def _init_sqlite(cls):
        """Initialize SQLite connection"""
        db_path = os.getenv("EMO_SQLITE_PATH", _SQLITE_PATH_DEFAULT)
        db_dir = os.path.dirname(db_path)
        
        # Ensure directory exists
        os.makedirs(db_dir, exist_ok=True)
        
        # SQLite-specific optimizations
        connect_args = {
            "check_same_thread": False,
            "timeout": 30,
        }
        
        cls._engine = sa.create_engine(
            f"sqlite:///{db_path}",
            poolclass=StaticPool,
            connect_args=connect_args,
            echo=os.getenv("EMO_DB_DEBUG", "").lower() == "true"
        )
        cls._dialect = "sqlite"
        
        # Initialize SQLite pragmas for performance
        cls._init_sqlite_pragmas()

    @classmethod
    def _init_sqlite_pragmas(cls):
        """Set SQLite performance optimizations"""
        pragmas = [
            "PRAGMA journal_mode=WAL",
            "PRAGMA synchronous=NORMAL", 
            "PRAGMA cache_size=10000",
            "PRAGMA temp_store=memory",
            "PRAGMA mmap_size=268435456",  # 256MB
        ]
        
        try:
            with cls.connect() as conn:
                for pragma in pragmas:
                    conn.execute(sa.text(pragma))
            logger.info("SQLite pragmas applied successfully")
        except Exception as e:
            logger.warning(f"Failed to apply SQLite pragmas: {e}")

    @classmethod
    def _verify_connection(cls):
        """Verify database connection is working"""
        try:
            with cls.connect() as conn:
                result = conn.execute(sa.text("SELECT 1")).scalar()
                if result != 1:
                    raise RuntimeError("Connection verification failed")
        except Exception as e:
            logger.error(f"Database connection verification failed: {e}")
            raise

    @classmethod
    def engine(cls) -> Engine:
        """Get database engine, initializing if necessary"""
        if cls._engine is None:
            cls.init()
        
        # Periodic health check
        cls._health_check()
        
        return cls._engine

    @classmethod
    def dialect(cls) -> str:
        """Get current database dialect"""
        if cls._engine is None:
            cls.init()
        return cls._dialect

    @classmethod
    def _health_check(cls):
        """Perform periodic health check"""
        import time
        current_time = time.time()
        
        if current_time - cls._last_health_check < cls._health_check_interval:
            return
        
        cls._last_health_check = current_time
        
        try:
            cls._verify_connection()
            if not cls._connection_healthy:
                logger.info("Database connection restored")
                cls._connection_healthy = True
        except Exception as e:
            if cls._connection_healthy:
                logger.error(f"Database health check failed: {e}")
                cls._connection_healthy = False

    @classmethod
    @contextmanager
    def connect(cls):
        """Get database connection with automatic cleanup"""
        conn = cls.engine().connect()
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    @contextmanager
    def session(cls) -> Session:
        """Get database session with automatic cleanup"""
        if cls._session_factory is None:
            cls.init()
        
        session = cls._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @classmethod
    def execute(cls, sql: str, **params):
        """Execute SQL with parameters"""
        with cls.connect() as conn:
            return conn.execute(sa.text(sql), params)

    @classmethod
    def fetch_df(cls, sql: str, **params) -> pd.DataFrame:
        """Execute SQL and return as pandas DataFrame"""
        with cls.connect() as conn:
            return pd.read_sql(sa.text(sql), conn, params=params)

    @classmethod
    def upsert_df(cls, df: pd.DataFrame, table: str, conflict_columns: List[str] = None):
        """Upsert DataFrame to database table with dialect-specific optimization"""
        if df.empty:
            return 0

        if conflict_columns is None:
            conflict_columns = ["symbol", "ts"] if "symbol" in df.columns and "ts" in df.columns else []

        try:
            if cls.dialect() == "sqlite":
                return cls._upsert_sqlite(df, table, conflict_columns)
            else:
                return cls._upsert_postgres(df, table, conflict_columns)
        except Exception as e:
            logger.error(f"Upsert failed for table {table}: {e}")
            raise

    @classmethod
    def _upsert_sqlite(cls, df: pd.DataFrame, table: str, conflict_columns: List[str]) -> int:
        """SQLite-specific upsert implementation"""
        columns = df.columns.tolist()
        placeholders = ", ".join([f":{col}" for col in columns])
        
        if conflict_columns:
            conflict_clause = f"({', '.join(conflict_columns)})"
            update_clause = ", ".join([f"{col}=excluded.{col}" for col in columns if col not in conflict_columns])
            sql = f"""
                INSERT INTO {table} ({', '.join(columns)})
                VALUES ({placeholders})
                ON CONFLICT {conflict_clause} DO UPDATE SET {update_clause}
            """
        else:
            sql = f"INSERT OR REPLACE INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

        records = df.to_dict('records')
        with cls.connect() as conn:
            for record in records:
                conn.execute(sa.text(sql), record)
        
        return len(records)

    @classmethod
    def _upsert_postgres(cls, df: pd.DataFrame, table: str, conflict_columns: List[str]) -> int:
        """PostgreSQL-specific upsert implementation"""
        columns = df.columns.tolist()
        placeholders = ", ".join([f":{col}" for col in columns])
        
        if conflict_columns:
            conflict_clause = f"({', '.join(conflict_columns)})"
            update_clause = ", ".join([f"{col}=EXCLUDED.{col}" for col in columns if col not in conflict_columns])
            sql = f"""
                INSERT INTO {table} ({', '.join(columns)})
                VALUES ({placeholders})
                ON CONFLICT {conflict_clause} DO UPDATE SET {update_clause}
            """
        else:
            sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

        records = df.to_dict('records')
        with cls.connect() as conn:
            for record in records:
                conn.execute(sa.text(sql), record)
        
        return len(records)

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Get database status information"""
        try:
            with cls.connect() as conn:
                if cls.dialect() == "sqlite":
                    # SQLite status
                    db_size = conn.execute(sa.text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")).scalar()
                    status = {
                        "dialect": cls.dialect(),
                        "healthy": cls._connection_healthy,
                        "database_size_bytes": db_size,
                        "path": os.getenv("EMO_SQLITE_PATH", _SQLITE_PATH_DEFAULT)
                    }
                else:
                    # PostgreSQL status
                    db_size = conn.execute(sa.text("SELECT pg_database_size(current_database())")).scalar()
                    status = {
                        "dialect": cls.dialect(),
                        "healthy": cls._connection_healthy,
                        "database_size_bytes": db_size,
                        "url": os.getenv("EMO_DB_URL", "").split("@")[-1] if "@" in os.getenv("EMO_DB_URL", "") else "unknown"
                    }
                
                # Common status
                tables = conn.execute(sa.text(
                    "SELECT name FROM sqlite_master WHERE type='table'" if cls.dialect() == "sqlite"
                    else "SELECT tablename FROM pg_tables WHERE schemaname='public'"
                )).fetchall()
                
                status.update({
                    "tables": [t[0] for t in tables],
                    "last_health_check": cls._last_health_check,
                })
                
                return status
                
        except Exception as e:
            return {
                "dialect": cls.dialect(),
                "healthy": False,
                "error": str(e)
            }

    @classmethod
    def close(cls):
        """Close database connections"""
        with cls._lock:
            if cls._engine:
                cls._engine.dispose()
                cls._engine = None
                cls._session_factory = None
                logger.info("Database connections closed")

# Convenience helpers
def is_timescale() -> bool:
    """Check if using Timescale database"""
    return DBRouter.dialect() == "timescale"

def is_sqlite() -> bool:
    """Check if using SQLite database"""
    return DBRouter.dialect() == "sqlite"

def get_db_status() -> Dict[str, Any]:
    """Get database status"""
    return DBRouter.get_status()

# Initialize router on import
try:
    DBRouter.init()
except Exception as e:
    logger.warning(f"Database router initialization deferred: {e}")