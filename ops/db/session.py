from __future__ import annotations
import os
import logging
from pathlib import Path
from typing import Optional

# Setup logging
logger = logging.getLogger(__name__)

_DB_URL_ENV = "EMO_DB_URL"
_DEFAULT_SQLITE = Path("data") / "orders.sqlite"

def _ensure_parent(p: Path):
    """Ensure parent directory exists."""
    p.parent.mkdir(parents=True, exist_ok=True)

def get_database_url() -> str:
    """
    Returns DB URL, preferring EMO_DB_URL if set, otherwise local SQLite file.
    
    Environment Variable Examples:
    - EMO_DB_URL=sqlite:///data/orders.sqlite
    - EMO_DB_URL=postgresql+psycopg2://user:pass@host:5432/emo
    
    Integration with Institutional Infrastructure:
    - Coordinates with src.database.router_v2 for enhanced features
    - Provides ops-specific database for order staging
    - Maintains compatibility with institutional monitoring
    
    Returns:
        Database URL string
    """
    url = os.getenv(_DB_URL_ENV)
    if url:
        logger.info(f"Using database URL from environment: {url[:50]}...")
        return url
    
    # Default to local SQLite for ops
    _ensure_parent(_DEFAULT_SQLITE)
    sqlite_url = f"sqlite:///{_DEFAULT_SQLITE.as_posix()}"
    logger.info(f"Using default SQLite for ops: {_DEFAULT_SQLITE}")
    return sqlite_url

def get_engine(echo: bool = False):
    """
    Create SQLAlchemy engine for ops database.
    
    Args:
        echo: Enable SQL query logging
        
    Returns:
        SQLAlchemy engine configured for ops database
        
    Raises:
        RuntimeError: If SQLAlchemy is not available
    """
    try:
        from sqlalchemy import create_engine
    except Exception as e:
        raise RuntimeError(
            "SQLAlchemy is required for DB features. Install with: pip install SQLAlchemy>=2.0"
        ) from e
    
    url = get_database_url()
    
    # Configure engine based on database type
    engine_kwargs = {
        "echo": echo,
        "future": True  # SQLAlchemy 2.0+ style
    }
    
    if url.startswith("sqlite"):
        # SQLite configuration for ops
        engine_kwargs.update({
            "connect_args": {
                "check_same_thread": False,
                "timeout": 30
            }
        })
    else:
        # PostgreSQL configuration for ops
        engine_kwargs.update({
            "pool_pre_ping": True,
            "pool_size": 5,
            "pool_recycle": 3600
        })
    
    engine = create_engine(url, **engine_kwargs)
    logger.info(f"OPS database engine created: {engine.url.database}")
    return engine

def get_session():
    """
    Create SQLAlchemy session for ops database with performance monitoring.
    
    Returns:
        SQLAlchemy session configured for ops database
        
    Raises:
        RuntimeError: If SQLAlchemy is not available
    """
    try:
        from sqlalchemy.orm import sessionmaker
        # Optional performance monitoring
        try:
            from src.monitoring.performance import record_metric
            record_metric("ops_session_created", 1, "count")
        except ImportError:
            pass  # Performance monitoring not available
    except Exception as e:
        raise RuntimeError(
            "SQLAlchemy is required for DB features. Install with: pip install SQLAlchemy>=2.0"
        ) from e
    
    engine = get_engine()
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    
    session = Session()
    logger.debug("OPS database session created")
    return session

def init_db():
    """
    Creates tables if they don't exist.
    Integrates with ops staging models.
    
    Returns:
        SQLAlchemy engine after table creation
        
    Raises:
        RuntimeError: If SQLAlchemy or models are not available
    """
    try:
        engine = get_engine()
        from ops.staging.models import Base  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "Unable to import SQLAlchemy model base. Ensure SQLAlchemy>=2.0 is installed "
            "and ops.staging.models is available."
        ) from e
    
    try:
        # Create all tables defined in Base
        Base.metadata.create_all(engine)
        logger.info("OPS database tables created/verified")
        
        # Integrate with institutional health monitoring
        try:
            from src.database.institutional_integration import InstitutionalIntegration
            integration = InstitutionalIntegration()
            integration.log_system_event("ops_db_init", {"status": "success", "url": str(engine.url)})
        except Exception as e:
            logger.debug(f"Institutional integration not available: {e}")
            
        return engine
        
    except Exception as e:
        logger.error(f"Failed to create OPS database tables: {e}")
        raise

def test_connection() -> bool:
    """
    Test ops database connectivity.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Use SQLAlchemy's text() for raw SQL
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
            test_value = result.scalar()
            
            if test_value == 1:
                logger.debug("OPS database connection test successful")
                return True
            else:
                logger.error("OPS database connection test failed: unexpected result")
                return False
                
    except Exception as e:
        logger.error(f"OPS database connection test failed: {e}")
        return False

def get_database_info() -> dict:
    """
    Get ops database information for monitoring.
    
    Returns:
        Dictionary with database information
    """
    try:
        engine = get_engine()
        return {
            "url": str(engine.url).replace(engine.url.password or "", "***") if engine.url.password else str(engine.url),
            "dialect": engine.dialect.name,
            "driver": engine.dialect.driver,
            "database": engine.url.database,
            "healthy": test_connection()
        }
    except Exception as e:
        return {
            "error": str(e),
            "healthy": False
        }

# Export key functions
__all__ = [
    "get_database_url",
    "get_engine",
    "get_session", 
    "init_db",
    "test_connection",
    "get_database_info"
]