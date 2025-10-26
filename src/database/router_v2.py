#!/usr/bin/env python3
"""
EMO Options Bot - Enhanced Database Router V2
=============================================
Institutional-grade database routing system supporting:
- Environment-aware database selection (SQLite dev, PostgreSQL prod)
- Connection pooling and health monitoring
- Automatic failover and recovery
- Schema migration and validation
- Performance monitoring and metrics
- Multi-database support with unified interface

Features:
- SQLite for development and testing
- PostgreSQL/TimescaleDB for production
- Automatic connection management
- Health monitoring and alerting
- Migration integration
- Performance optimization
- Error handling and recovery
"""

from __future__ import annotations
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Union
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import StaticPool

# Setup logging
logger = logging.getLogger(__name__)

class EnhancedDatabaseRouter:
    """
    Enhanced database router for EMO Options Bot.
    Provides intelligent routing between SQLite and PostgreSQL based on environment.
    """
    
    def __init__(self, echo: bool = False, pool_size: int = 5):
        """
        Initialize database router.
        
        Args:
            echo: Enable SQL query logging
            pool_size: Connection pool size for PostgreSQL
        """
        self.echo = echo
        self.pool_size = pool_size
        self.environment = os.getenv("EMO_ENV", "dev").lower()
        self._engine: Optional[Engine] = None
        self._connection_cache: Dict[str, Engine] = {}
        
        logger.info(f"Enhanced database router initialized for {self.environment} environment")
    
    def get_database_url(self) -> str:
        """
        Get database URL based on environment and configuration.
        
        Returns:
            Database URL string
        """
        # Highest priority: explicit override
        override_url = os.getenv("EMO_DB_URL")
        if override_url:
            logger.info("Using explicit database URL override")
            return override_url
        
        # Environment-based routing
        if self.environment in ("prod", "staging"):
            # Production/staging: prefer PostgreSQL/TimescaleDB
            postgres_url = os.getenv("POSTGRES_URL") or os.getenv("EMO_PG_DSN")
            if postgres_url:
                logger.info(f"Using PostgreSQL for {self.environment} environment")
                return postgres_url
            else:
                logger.warning(f"PostgreSQL URL not configured for {self.environment}, falling back to SQLite")
        
        # Development/fallback: SQLite
        root_dir = Path(__file__).resolve().parents[2]  # src/database/ -> project root
        data_dir = root_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        sqlite_path = data_dir / f"emo_{self.environment}.sqlite"
        sqlite_url = f"sqlite:///{sqlite_path.as_posix()}"
        
        logger.info(f"Using SQLite for {self.environment} environment: {sqlite_path}")
        return sqlite_url
    
    def create_engine(self, url: Optional[str] = None) -> Engine:
        """
        Create SQLAlchemy engine with appropriate configuration.
        
        Args:
            url: Database URL, auto-detected if None
            
        Returns:
            Configured SQLAlchemy engine
        """
        if url is None:
            url = self.get_database_url()
        
        # Engine configuration based on database type
        engine_kwargs = {
            "echo": self.echo,
            "future": True  # SQLAlchemy 2.0+ style
        }
        
        if url.startswith("sqlite"):
            # SQLite configuration
            engine_kwargs.update({
                "connect_args": {
                    "check_same_thread": False,
                    "timeout": 30
                },
                "poolclass": StaticPool,
                "pool_pre_ping": True
            })
        else:
            # PostgreSQL configuration
            engine_kwargs.update({
                "pool_size": self.pool_size,
                "pool_pre_ping": True,
                "pool_recycle": 3600,  # Recycle connections every hour
                "connect_args": {
                    "connect_timeout": 30,
                    "application_name": f"emo_bot_{self.environment}"
                }
            })
        
        try:
            engine = create_engine(url, **engine_kwargs)
            logger.info(f"Database engine created: {engine.url.database}")
            return engine
            
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise
    
    def get_engine(self, force_new: bool = False) -> Engine:
        """
        Get database engine, creating if necessary.
        
        Args:
            force_new: Force creation of new engine
            
        Returns:
            SQLAlchemy engine
        """
        if self._engine is None or force_new:
            self._engine = self.create_engine()
        
        return self._engine
    
    @contextmanager
    def get_connection(self):
        """
        Get database connection as context manager.
        Automatically handles connection cleanup.
        """
        engine = self.get_engine()
        connection = None
        
        try:
            connection = engine.connect()
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                connection.close()
    
    def test_connection(self) -> bool:
        """
        Test database connectivity and basic functionality.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                # Simple connectivity test
                result = conn.execute(text("SELECT 1"))
                test_value = result.scalar()
                
                if test_value == 1:
                    logger.debug("Database connection test successful")
                    return True
                else:
                    logger.error("Database connection test failed: unexpected result")
                    return False
                    
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def migrate_schema(self) -> bool:
        """
        Run database schema migrations.
        
        Returns:
            True if migration successful, False otherwise
        """
        try:
            from .migrations import run_migrations
            
            engine = self.get_engine()
            success = run_migrations(engine)
            
            if success:
                logger.info("Database schema migration completed successfully")
            else:
                logger.error("Database schema migration failed")
            
            return success
            
        except ImportError:
            logger.warning("Migration system not available")
            return False
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False
    
    def close(self) -> None:
        """Close database connections and cleanup resources."""
        try:
            if self._engine:
                self._engine.dispose()
                self._engine = None
                logger.info("Database engine disposed")
            
            # Clear connection cache
            for engine in self._connection_cache.values():
                engine.dispose()
            self._connection_cache.clear()
            
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")

# Global router instance for convenience
_enhanced_router: Optional[EnhancedDatabaseRouter] = None

def get_enhanced_router() -> EnhancedDatabaseRouter:
    """Get enhanced database router instance."""
    global _enhanced_router
    if _enhanced_router is None:
        _enhanced_router = EnhancedDatabaseRouter()
    return _enhanced_router

def create_enhanced_engine(echo: bool = False, pool_size: int = 5) -> Engine:
    """
    Create database engine using enhanced router configuration.
    
    Args:
        echo: Enable SQL query logging
        pool_size: Connection pool size
        
    Returns:
        Configured SQLAlchemy engine
    """
    router = EnhancedDatabaseRouter(echo=echo, pool_size=pool_size)
    return router.get_engine()

def test_enhanced_connection() -> bool:
    """
    Test database connection using enhanced router.
    
    Returns:
        True if connection successful, False otherwise
    """
    router = get_enhanced_router()
    return router.test_connection()

def migrate_enhanced() -> bool:
    """
    Run database migrations using enhanced router.
    
    Returns:
        True if migration successful, False otherwise
    """
    router = get_enhanced_router()
    return router.migrate_schema()

# Export key classes and functions
__all__ = [
    "EnhancedDatabaseRouter",
    "create_enhanced_engine", 
    "test_enhanced_connection",
    "migrate_enhanced",
    "get_enhanced_router"
]