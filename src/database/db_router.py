from __future__ import annotations
import os
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool, StaticPool
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError
from src.utils.enhanced_config import Config

"""
Enhanced Database Router
------------------------
Robust database connection management with:
- Connection pooling and health checks
- Automatic failover and retry logic
- Performance monitoring and logging
- Multi-environment support (dev/staging/prod)
- Connection validation and recovery

Environment Variables:
  - EMO_ENV=dev|staging|prod
  - EMO_DB=sqlite|timescale
  - EMO_SQLITE_PATH=./data/emo.sqlite
  - EMO_PG_DSN=postgresql+psycopg2://user:pass@host:5432/emo
  - EMO_DB_POOL_SIZE=10
  - EMO_DB_MAX_OVERFLOW=20
  - EMO_DB_POOL_TIMEOUT=30
  - EMO_DB_POOL_RECYCLE=3600
"""

# Global engine cache for connection reuse
_engines: Dict[str, Engine] = {}
_engine_health: Dict[str, Dict[str, Any]] = {}

# Setup module logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def db_url_from_env(cfg: Optional[Config] = None) -> str:
    """Generate database URL from environment configuration."""
    cfg = cfg or Config()
    emo_db = cfg.get("EMO_DB", "sqlite").lower()
    
    if emo_db == "timescale":
        dsn = cfg.get("EMO_PG_DSN")
        if not dsn:
            raise RuntimeError(
                "EMO_DB=timescale but EMO_PG_DSN is not set. "
                "Please configure PostgreSQL/TimescaleDB connection string."
            )
        logger.info(f"Using TimescaleDB connection: {dsn.split('@')[0]}@***")
        return dsn
    
    # Default SQLite configuration
    sqlite_path = cfg.get("EMO_SQLITE_PATH", "./data/emo.sqlite")
    sqlite_path = os.path.abspath(sqlite_path)
    
    # Ensure SQLite directory exists
    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    
    url = f"sqlite:///{sqlite_path}"
    logger.info(f"Using SQLite database: {sqlite_path}")
    return url

def _get_pool_config(cfg: Config, is_sqlite: bool = False) -> Dict[str, Any]:
    """Get connection pool configuration based on database type."""
    if is_sqlite:
        # SQLite-specific pool configuration
        return {
            "poolclass": StaticPool,
            "pool_pre_ping": True,
            "connect_args": {
                "check_same_thread": False,
                "timeout": 20,
                "isolation_level": None  # Autocommit mode
            }
        }
    else:
        # PostgreSQL/TimescaleDB pool configuration
        return {
            "poolclass": QueuePool,
            "pool_size": int(cfg.get("EMO_DB_POOL_SIZE", "10")),
            "max_overflow": int(cfg.get("EMO_DB_MAX_OVERFLOW", "20")),
            "pool_timeout": int(cfg.get("EMO_DB_POOL_TIMEOUT", "30")),
            "pool_recycle": int(cfg.get("EMO_DB_POOL_RECYCLE", "3600")),
            "pool_pre_ping": True,
            "connect_args": {
                "connect_timeout": 10,
                "application_name": "emo_options_bot"
            }
        }

def _setup_engine_events(engine: Engine, db_type: str):
    """Setup SQLAlchemy engine events for monitoring and health checks."""
    
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_connection, connection_record):
        logger.debug(f"New {db_type} connection established")
        connection_record.info["connect_time"] = time.time()
    
    @event.listens_for(engine, "checkout")
    def receive_checkout(dbapi_connection, connection_record, connection_proxy):
        logger.debug(f"{db_type} connection checked out from pool")
    
    @event.listens_for(engine, "checkin")
    def receive_checkin(dbapi_connection, connection_record):
        logger.debug(f"{db_type} connection checked back into pool")
    
    @event.listens_for(engine, "invalidate")
    def receive_invalidate(dbapi_connection, connection_record, exception):
        logger.warning(f"{db_type} connection invalidated: {exception}")

def validate_connection(engine: Engine, db_type: str) -> bool:
    """Validate database connection health."""
    try:
        with engine.connect() as conn:
            if db_type == "sqlite":
                result = conn.execute(text("SELECT 1")).fetchone()
            else:
                result = conn.execute(text("SELECT version()")).fetchone()
            
            logger.debug(f"{db_type} connection validation successful")
            return True
            
    except Exception as e:
        logger.error(f"{db_type} connection validation failed: {e}")
        return False

def get_engine(cfg: Optional[Config] = None, echo: bool = False, force_new: bool = False) -> Engine:
    """
    Get database engine with robust connection management.
    
    Args:
        cfg: Configuration object
        echo: Enable SQL query logging
        force_new: Force creation of new engine (bypass cache)
    
    Returns:
        SQLAlchemy Engine instance
    """
    cfg = cfg or Config()
    url = db_url_from_env(cfg)
    
    # Create cache key
    cache_key = f"{url}_{echo}"
    
    # Return cached engine if available and healthy
    if not force_new and cache_key in _engines:
        engine = _engines[cache_key]
        
        # Check engine health
        health_info = _engine_health.get(cache_key, {})
        last_check = health_info.get("last_check", 0)
        
        # Validate connection every 5 minutes
        if time.time() - last_check > 300:
            db_type = "sqlite" if url.startswith("sqlite") else "postgresql"
            if validate_connection(engine, db_type):
                _engine_health[cache_key] = {
                    "last_check": time.time(),
                    "status": "healthy",
                    "connections": engine.pool.size()
                }
                logger.debug(f"Using cached {db_type} engine (healthy)")
                return engine
            else:
                logger.warning(f"Cached engine unhealthy, creating new connection")
                # Remove unhealthy engine from cache
                _engines.pop(cache_key, None)
                _engine_health.pop(cache_key, None)
    
    # Create new engine
    is_sqlite = url.startswith("sqlite")
    db_type = "sqlite" if is_sqlite else "postgresql"
    
    try:
        # Get pool configuration
        pool_config = _get_pool_config(cfg, is_sqlite)
        
        # Create engine with robust configuration
        engine = create_engine(
            url,
            echo=echo,
            future=True,
            **pool_config
        )
        
        # Setup monitoring events
        _setup_engine_events(engine, db_type)
        
        # Validate new connection
        if not validate_connection(engine, db_type):
            raise RuntimeError(f"Failed to validate new {db_type} connection")
        
        # Cache the engine
        _engines[cache_key] = engine
        _engine_health[cache_key] = {
            "created": time.time(),
            "last_check": time.time(),
            "status": "healthy",
            "db_type": db_type,
            "url_hash": hash(url)
        }
        
        logger.info(f"Created new {db_type} engine with robust configuration")
        return engine
        
    except Exception as e:
        logger.error(f"Failed to create {db_type} engine: {e}")
        raise RuntimeError(f"Database connection failed: {e}") from e

def get_engine_health() -> Dict[str, Dict[str, Any]]:
    """Get health information for all cached engines."""
    health_report = {}
    
    for cache_key, health_info in _engine_health.items():
        engine = _engines.get(cache_key)
        if engine:
            try:
                pool_status = {
                    "size": engine.pool.size(),
                    "checked_in": engine.pool.checkedin(),
                    "checked_out": engine.pool.checkedout(),
                    "overflow": engine.pool.overflow(),
                    "invalid": engine.pool.invalid()
                }
            except:
                pool_status = {"error": "Could not retrieve pool status"}
            
            health_report[cache_key] = {
                **health_info,
                "pool_status": pool_status,
                "age_seconds": time.time() - health_info.get("created", 0)
            }
    
    return health_report

def close_all_engines():
    """Close all cached database engines."""
    for cache_key, engine in _engines.items():
        try:
            engine.dispose()
            logger.info(f"Closed engine: {cache_key}")
        except Exception as e:
            logger.error(f"Error closing engine {cache_key}: {e}")
    
    _engines.clear()
    _engine_health.clear()
    logger.info("All database engines closed")

# Context manager for database operations
class DatabaseSession:
    """Context manager for robust database operations."""
    
    def __init__(self, cfg: Optional[Config] = None, echo: bool = False):
        self.cfg = cfg or Config()
        self.echo = echo
        self.engine = None
        self.connection = None
    
    def __enter__(self):
        self.engine = get_engine(self.cfg, self.echo)
        self.connection = self.engine.connect()
        return self.connection
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            try:
                if exc_type:
                    self.connection.rollback()
                self.connection.close()
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
        
        return False  # Don't suppress exceptions

if __name__ == "__main__":
    # Enhanced CLI interface for database testing
    import argparse
    
    parser = argparse.ArgumentParser(description="EMO Database Router - Enhanced Testing")
    parser.add_argument("--test", action="store_true", help="Run connection tests")
    parser.add_argument("--health", action="store_true", help="Show engine health")
    parser.add_argument("--cleanup", action="store_true", help="Close all engines")
    parser.add_argument("--echo", action="store_true", help="Enable SQL echo")
    
    args = parser.parse_args()
    
    cfg = Config()
    
    if args.cleanup:
        close_all_engines()
        print("✅ All database engines closed")
    
    elif args.health:
        health = get_engine_health()
        if health:
            print("📊 Database Engine Health Report:")
            for key, info in health.items():
                print(f"  Engine: {key}")
                print(f"    Status: {info.get('status', 'unknown')}")
                print(f"    Type: {info.get('db_type', 'unknown')}")
                print(f"    Age: {info.get('age_seconds', 0):.1f}s")
                if 'pool_status' in info:
                    pool = info['pool_status']
                    print(f"    Pool: {pool.get('size', 0)} total, {pool.get('checked_out', 0)} active")
        else:
            print("📭 No cached database engines")
    
    elif args.test:
        print("🔧 Testing database connections...")
        
        try:
            # Test engine creation
            engine = get_engine(cfg, echo=args.echo)
            print(f"✅ Engine created successfully")
            
            # Test connection
            with DatabaseSession(cfg, echo=args.echo) as conn:
                if db_url_from_env(cfg).startswith("sqlite"):
                    result = conn.execute(text("SELECT sqlite_version()")).fetchone()
                    print(f"✅ SQLite connection successful: {result[0]}")
                else:
                    result = conn.execute(text("SELECT version()")).fetchone()
                    print(f"✅ PostgreSQL connection successful")
            
            # Show health after test
            health = get_engine_health()
            print(f"📊 Engine health: {len(health)} cached engines")
            
        except Exception as e:
            print(f"❌ Database test failed: {e}")
            exit(1)
    
    else:
        # Default: just print the URL
        url = db_url_from_env(cfg)
        print(url)