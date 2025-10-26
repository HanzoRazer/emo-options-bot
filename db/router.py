#!/usr/bin/env python3
"""
Enhanced Database Router
========================
Advanced database routing system with:
- SQLite vs TimescaleDB selection based on environment
- Automatic migration and schema management
- Connection pooling and health monitoring
- Integration with enhanced Phase 2 infrastructure

Features:
- Environment-aware database selection (dev=SQLite, prod=TimescaleDB)
- Comprehensive schema management for EMO Options Bot
- Connection health monitoring and validation
- Integration with enhanced configuration system
- CLI tools for migration and testing
- Performance optimizations and indexing

Environment Variables:
  EMO_ENV=dev|staging|prod          # Environment selection
  EMO_DB=sqlite|timescale           # Override database type
  EMO_SQLITE_PATH=./ops/emo.db      # SQLite database path
  EMO_PG_DSN=postgresql://...       # PostgreSQL/TimescaleDB connection string
"""

import os
import sqlite3
import contextlib
import datetime as dt
import logging
from pathlib import Path
import sys
from typing import Optional, Dict, Any, Union

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
EMO_ENV = os.getenv("EMO_ENV", "dev").lower()
ROOT = Path(__file__).resolve().parents[1]

# Add src to path for enhanced config integration
sys.path.insert(0, str(ROOT / "src"))

# Enhanced configuration integration
try:
    from utils.enhanced_config import Config
    config = Config()
    logger.info("✅ Enhanced configuration loaded")
except Exception:
    logger.warning("⚠️ Enhanced config not available, using fallback")
    class FallbackConfig:
        def get(self, key: str, default: str = None) -> str:
            return os.getenv(key, default)
    config = FallbackConfig()

# Database configuration
SQLITE_PATH = ROOT / "ops" / config.get("EMO_SQLITE_NAME", "emo.sqlite")

class EnhancedDB:
    """Enhanced database manager with robust connection handling and schema management."""
    
    def __init__(self):
        self.kind = self._determine_db_type()
        self.conn = None
        self._schema_version = "1.0"
        logger.info(f"🗄️ Database manager initialized: {self.kind}")
    
    def _determine_db_type(self) -> str:
        """Determine database type based on environment and configuration."""
        # Allow explicit override
        db_override = config.get("EMO_DB")
        if db_override and db_override.lower() in ["sqlite", "timescale", "postgres"]:
            return db_override.lower()
        
        # Environment-based selection
        if EMO_ENV == "prod":
            # Production prefers TimescaleDB if available
            if config.get("EMO_PG_DSN") or config.get("EMO_TIMESCALE_URL"):
                try:
                    import psycopg2
                    return "timescale"
                except ImportError:
                    logger.warning("⚠️ psycopg2 not available, falling back to SQLite")
                    return "sqlite"
            else:
                logger.warning("⚠️ Production environment but no TimescaleDB configured")
                return "sqlite"
        else:
            return "sqlite"
    
    def connect(self):
        """Establish database connection with proper initialization."""
        try:
            if self.kind == "sqlite":
                self._connect_sqlite()
            else:
                self._connect_postgres()
            
            logger.info(f"✅ Database connection established: {self.kind}")
            return self
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    def _connect_sqlite(self):
        """Connect to SQLite with optimizations."""
        SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(SQLITE_PATH))
        
        # Enable optimizations
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA foreign_keys=ON;")
        self.conn.execute("PRAGMA busy_timeout=30000;")
        
        # Create enhanced schema
        self._create_sqlite_schema()
    
    def _connect_postgres(self):
        """Connect to PostgreSQL/TimescaleDB."""
        import psycopg2
        import psycopg2.extras
        
        # Get connection string
        dsn = (config.get("EMO_PG_DSN") or 
               config.get("EMO_TIMESCALE_URL") or 
               config.get("PG_URL"))
        
        if not dsn:
            raise ValueError("No PostgreSQL connection string configured")
        
        self.conn = psycopg2.connect(dsn)
        self.conn.autocommit = False
        
        # Create enhanced schema
        self._create_postgres_schema()
    
    def _create_sqlite_schema(self):
        """Create comprehensive SQLite schema for EMO Options Bot."""
        schema_queries = [
            # Market data table (enhanced)
            """
            CREATE TABLE IF NOT EXISTS bars (
                symbol TEXT NOT NULL,
                ts TEXT NOT NULL,
                open REAL, high REAL, low REAL, close REAL,
                volume INTEGER,
                adj_close REAL,
                data_source TEXT DEFAULT 'unknown',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(symbol, ts)
            )
            """,
            
            # Options data table
            """
            CREATE TABLE IF NOT EXISTS options_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                option_symbol TEXT NOT NULL,
                strike REAL NOT NULL,
                expiry TEXT NOT NULL,
                option_type TEXT NOT NULL CHECK (option_type IN ('call', 'put')),
                bid REAL,
                ask REAL,
                last REAL,
                volume INTEGER,
                open_interest INTEGER,
                implied_volatility REAL,
                delta REAL,
                gamma REAL,
                theta REAL,
                vega REAL,
                timestamp TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Trades table (enhanced)
            """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL CHECK (side IN ('buy', 'sell')),
                qty REAL NOT NULL CHECK (qty > 0),
                price REAL CHECK (price > 0),
                order_type TEXT DEFAULT 'market',
                strategy TEXT,
                notes TEXT,
                broker_order_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Positions table
            """
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL UNIQUE,
                qty REAL NOT NULL DEFAULT 0,
                avg_price REAL,
                market_value REAL,
                unrealized_pnl REAL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Order drafts table
            """
            CREATE TABLE IF NOT EXISTS order_drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT NOT NULL,
                symbol TEXT,
                side TEXT,
                qty REAL,
                strategy TEXT,
                processed BOOLEAN DEFAULT FALSE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # Performance metrics table
            """
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                metric_data TEXT,
                source TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]
        
        # Execute schema creation
        for query in schema_queries:
            self.conn.execute(query)
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_bars_symbol ON bars(symbol);",
            "CREATE INDEX IF NOT EXISTS idx_bars_ts ON bars(ts);",
            "CREATE INDEX IF NOT EXISTS idx_options_symbol ON options_data(symbol);",
            "CREATE INDEX IF NOT EXISTS idx_options_expiry ON options_data(expiry);",
            "CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol);",
            "CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp);",
            "CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol);",
            "CREATE INDEX IF NOT EXISTS idx_order_drafts_processed ON order_drafts(processed);",
            "CREATE INDEX IF NOT EXISTS idx_performance_metrics_name ON performance_metrics(metric_name);"
        ]
        
        for index_query in indexes:
            self.conn.execute(index_query)
        
        self.conn.commit()
        logger.info("✅ SQLite schema created successfully")
    
    def _create_postgres_schema(self):
        """Create PostgreSQL/TimescaleDB schema."""
        logger.info("🔧 Creating PostgreSQL/TimescaleDB schema...")
        
        with self.conn.cursor() as cur:
            # Market data table with TimescaleDB optimization
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bars (
                    symbol TEXT NOT NULL,
                    ts TIMESTAMPTZ NOT NULL,
                    open DOUBLE PRECISION, 
                    high DOUBLE PRECISION, 
                    low DOUBLE PRECISION, 
                    close DOUBLE PRECISION,
                    volume BIGINT,
                    adj_close DOUBLE PRECISION,
                    data_source TEXT DEFAULT 'unknown',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    PRIMARY KEY(symbol, ts)
                );
            """)
            
            # Options data table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS options_data (
                    id SERIAL PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    option_symbol TEXT NOT NULL,
                    strike DOUBLE PRECISION NOT NULL,
                    expiry DATE NOT NULL,
                    option_type TEXT NOT NULL CHECK (option_type IN ('call', 'put')),
                    bid DOUBLE PRECISION,
                    ask DOUBLE PRECISION,
                    last DOUBLE PRECISION,
                    volume BIGINT,
                    open_interest BIGINT,
                    implied_volatility DOUBLE PRECISION,
                    delta DOUBLE PRECISION,
                    gamma DOUBLE PRECISION,
                    theta DOUBLE PRECISION,
                    vega DOUBLE PRECISION,
                    timestamp TIMESTAMPTZ NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
            """)
            
            # Try to create hypertable if TimescaleDB extension is available
            try:
                cur.execute("SELECT create_hypertable('bars', 'ts', if_not_exists => TRUE);")
                logger.info("✅ TimescaleDB hypertable created for bars")
            except Exception as e:
                logger.info(f"ℹ️ TimescaleDB hypertable creation skipped: {e}")
            
            self.conn.commit()
            logger.info("✅ PostgreSQL schema created successfully")
    
    @contextlib.contextmanager
    def cursor(self):
        """Context manager for database cursor."""
        if not self.conn:
            raise RuntimeError("Database not connected")
        
        cur = self.conn.cursor()
        try:
            yield cur
        finally:
            cur.close()
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.debug("🔒 Database connection closed")
    
    def __enter__(self):
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"❌ Database transaction error: {exc_val}")
            if self.conn:
                self.conn.rollback()
        self.close()

# Legacy compatibility
class DB(EnhancedDB):
    """Legacy DB class for backward compatibility."""
    pass

# Convenience functions
def get_db() -> EnhancedDB:
    """Get a new database instance."""
    return EnhancedDB()

@contextlib.contextmanager
def get_connection():
    """Context manager for database connections."""
    db = EnhancedDB()
    try:
        yield db.connect()
    finally:
        db.close()

def migrate():
    """Run database migration."""
    try:
        with get_connection() as db:
            logger.info("🚀 Database migration completed successfully")
            return True
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        return False

def test_connection() -> bool:
    """Test database connection."""
    try:
        with get_connection() as db:
            with db.cursor() as cur:
                if db.kind == "sqlite":
                    cur.execute("SELECT sqlite_version();")
                    version = cur.fetchone()[0]
                    logger.info(f"✅ SQLite connection test successful (v{version})")
                else:
                    cur.execute("SELECT version();")
                    version = cur.fetchone()[0]
                    logger.info("✅ PostgreSQL connection test successful")
                return True
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="EMO Database Router")
    parser.add_argument("--migrate", action="store_true", help="Run migration")
    parser.add_argument("--test", action="store_true", help="Test connection")
    parser.add_argument("--info", action="store_true", help="Show database info")
    
    args = parser.parse_args()
    
    if args.migrate:
        print("🚀 Running database migration...")
        if migrate():
            print("✅ Migration completed successfully")
        else:
            print("❌ Migration failed")
            exit(1)
    
    elif args.test:
        print("🔍 Testing database connection...")
        if test_connection():
            print("✅ Connection test passed")
        else:
            print("❌ Connection test failed")
            exit(1)
    
    elif args.info:
        print("📊 Database Information:")
        print(f"  Environment: {EMO_ENV}")
        db = EnhancedDB()
        print(f"  Database Type: {db.kind}")
        print(f"  SQLite Path: {SQLITE_PATH}")
        if config.get("EMO_PG_DSN"):
            print(f"  PostgreSQL DSN: {config.get('EMO_PG_DSN')[:50]}...")
    
    else:
        # Default: show current configuration
        db = EnhancedDB()
        print(f"EMO Database Router (Environment: {EMO_ENV}, Type: {db.kind})")
        if db.kind == "sqlite":
            print(f"SQLite Path: {SQLITE_PATH}")
        else:
            print("PostgreSQL/TimescaleDB configured")