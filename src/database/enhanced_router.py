#!/usr/bin/env python3
"""
EMO Options Bot - Enhanced Database Router (Legacy Compatibility)
================================================================
Institutional-grade database routing system with legacy API support.
This module provides both new enhanced functionality and legacy compatibility.

Features:
- SQLite for development and testing
- PostgreSQL/TimescaleDB for production
- Automatic connection management
- Health monitoring and alerting
- Migration integration
- Performance optimization
- Legacy API compatibility
"""

from __future__ import annotations
import os
import logging
import threading
from pathlib import Path
from typing import Optional, Dict, Any, Union
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker

# Import new enhanced router
from .router_v2 import EnhancedDatabaseRouter, get_enhanced_router

# Setup logging
logger = logging.getLogger(__name__)

class DBRouter:
    """
    Legacy database router with enhanced functionality.
    This class provides backward compatibility while using the new enhanced router.
    """
    _engine: Optional[Engine] = None
    _dialect: str = "sqlite"
    _session_factory: Optional[sessionmaker] = None
    _health_check_interval = 300  # 5 minutes
    _last_health_check = 0
    _connection_healthy = True
    _lock = threading.Lock()
    _enhanced_router: Optional[EnhancedDatabaseRouter] = None

    @classmethod
    def init(cls, force_reconnect: bool = False):
        """Initialize database connection using enhanced router"""
        with cls._lock:
            if cls._engine is not None and not force_reconnect:
                return

            try:
                # Use enhanced router for initialization
                cls._enhanced_router = get_enhanced_router()
                cls._engine = cls._enhanced_router.get_engine(force_new=force_reconnect)
                
                # Detect dialect from engine URL
                url_str = str(cls._engine.url)
                if url_str.startswith("sqlite"):
                    cls._dialect = "sqlite"
                elif "postgresql" in url_str or "timescale" in url_str:
                    cls._dialect = "timescale"
                else:
                    cls._dialect = "unknown"
                    
                # Create session factory
                cls._session_factory = sessionmaker(bind=cls._engine)
                
                # Verify connection using enhanced router
                cls._connection_healthy = cls._enhanced_router.test_connection()
                
                logger.info(f"Database initialized via enhanced router: {cls._dialect}")
                
            except Exception as e:
                logger.error(f"Database initialization failed: {e}")
                cls._connection_healthy = False
                raise

    @classmethod
    def engine(cls) -> Engine:
        """Get database engine, initializing if necessary"""
        if cls._engine is None:
            cls.init()
        return cls._engine

    @classmethod
    def dialect(cls) -> str:
        """Get current database dialect"""
        if cls._engine is None:
            cls.init()
        return cls._dialect

    @classmethod
    def connect(cls):
        """Get database connection using enhanced router"""
        if cls._enhanced_router is None:
            cls.init()
        return cls._enhanced_router.get_connection()

    @classmethod
    def session(cls):
        """Get database session"""
        if cls._session_factory is None:
            cls.init()
        return cls._session_factory()

    @classmethod
    def test_connection(cls) -> bool:
        """Test database connection"""
        try:
            if cls._enhanced_router is None:
                cls.init()
            return cls._enhanced_router.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    @classmethod
    def close(cls):
        """Close database connections"""
        with cls._lock:
            if cls._enhanced_router:
                cls._enhanced_router.close()
            if cls._engine:
                cls._engine.dispose()
                cls._engine = None
            cls._session_factory = None
            cls._connection_healthy = False

    @classmethod
    def is_healthy(cls) -> bool:
        """Check if database connection is healthy"""
        return cls._connection_healthy

    @classmethod
    def migrate(cls) -> bool:
        """Run database migrations"""
        try:
            if cls._enhanced_router is None:
                cls.init()
            return cls._enhanced_router.migrate_schema()
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

# Legacy function exports for backward compatibility
def create_engine_from_env() -> Engine:
    """Create database engine from environment (legacy function)"""
    router = get_enhanced_router()
    return router.get_engine()

def get_database_url() -> str:
    """Get database URL from environment (legacy function)"""
    router = get_enhanced_router()
    return router.get_database_url()

def test_connection() -> bool:
    """Test database connection (legacy function)"""
    return DBRouter.test_connection()

# Export key classes and functions for compatibility
__all__ = [
    "DBRouter",
    "create_engine_from_env",
    "get_database_url", 
    "test_connection",
    "EnhancedDatabaseRouter",  # New enhanced router
    "get_enhanced_router"      # New enhanced router accessor
]

# Initialize router on import (optional)
try:
    DBRouter.init()
except Exception as e:
    logger.warning(f"Database router initialization deferred: {e}")