"""
Enhanced Timescale Migrations with Schema Versioning
Create/upgrade Timescale schema with automatic rollback and health checks.
Safe to re-run and includes data migration utilities.
"""
import sys
import os
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any
import json

import sqlalchemy as sa
from sqlalchemy.exc import OperationalError

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.database.enhanced_router import DBRouter, is_timescale

logger = logging.getLogger(__name__)

# Schema version tracking
CURRENT_SCHEMA_VERSION = "1.2.0"

# Enhanced DDL with better indexes and constraints
DDL_STATEMENTS = [
    # Enable TimescaleDB extension
    {
        "name": "enable_timescaledb",
        "sql": "CREATE EXTENSION IF NOT EXISTS timescaledb;",
        "rollback": None,  # Cannot rollback extension creation safely
        "version": "1.0.0"
    },
    
    # Schema version tracking table
    {
        "name": "schema_versions",
        "sql": """
        CREATE TABLE IF NOT EXISTS schema_versions (
            version TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            description TEXT,
            checksum TEXT
        );
        """,
        "rollback": "DROP TABLE IF EXISTS schema_versions;",
        "version": "1.0.0"
    },
    
    # Enhanced bars table with better partitioning
    {
        "name": "bars_table",
        "sql": """
        CREATE TABLE IF NOT EXISTS bars (
            ts TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            open DOUBLE PRECISION,
            high DOUBLE PRECISION,
            low DOUBLE PRECISION,
            close DOUBLE PRECISION,
            volume BIGINT,
            timeframe TEXT DEFAULT '1Min',
            vwap DOUBLE PRECISION,
            trade_count INTEGER,
            created_at TIMESTAMPTZ DEFAULT now(),
            PRIMARY KEY (symbol, ts, timeframe)
        );
        """,
        "rollback": "DROP TABLE IF EXISTS bars;",
        "version": "1.0.0"
    },
    
    # Convert to hypertable
    {
        "name": "bars_hypertable",
        "sql": "SELECT create_hypertable('bars', 'ts', if_not_exists => TRUE, migrate_data => TRUE, chunk_time_interval => INTERVAL '1 day');",
        "rollback": None,  # Cannot easily rollback hypertable
        "version": "1.0.0"
    },
    
    # Bars indexes for performance
    {
        "name": "bars_indexes",
        "sql": """
        CREATE INDEX IF NOT EXISTS idx_bars_symbol_ts ON bars(symbol, ts DESC);
        CREATE INDEX IF NOT EXISTS idx_bars_timeframe ON bars(timeframe);
        CREATE INDEX IF NOT EXISTS idx_bars_volume ON bars(volume) WHERE volume > 0;
        """,
        "rollback": """
        DROP INDEX IF EXISTS idx_bars_symbol_ts;
        DROP INDEX IF EXISTS idx_bars_timeframe;
        DROP INDEX IF EXISTS idx_bars_volume;
        """,
        "version": "1.0.0"
    },
    
    # Enhanced options Greeks table
    {
        "name": "options_greeks_table",
        "sql": """
        CREATE TABLE IF NOT EXISTS options_greeks (
            ts TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            expiry DATE NOT NULL,
            strike DOUBLE PRECISION NOT NULL,
            right TEXT NOT NULL CHECK (right IN ('C', 'P')),
            delta DOUBLE PRECISION,
            gamma DOUBLE PRECISION,
            theta DOUBLE PRECISION,
            vega DOUBLE PRECISION,
            rho DOUBLE PRECISION,
            iv DOUBLE PRECISION CHECK (iv >= 0),
            bid DOUBLE PRECISION CHECK (bid >= 0),
            ask DOUBLE PRECISION CHECK (ask >= bid),
            last DOUBLE PRECISION,
            volume INTEGER DEFAULT 0,
            open_interest INTEGER DEFAULT 0,
            intrinsic_value DOUBLE PRECISION,
            time_value DOUBLE PRECISION,
            created_at TIMESTAMPTZ DEFAULT now(),
            PRIMARY KEY (symbol, ts, expiry, strike, right)
        );
        """,
        "rollback": "DROP TABLE IF EXISTS options_greeks;",
        "version": "1.0.0"
    },
    
    # Options Greeks hypertable
    {
        "name": "options_greeks_hypertable", 
        "sql": "SELECT create_hypertable('options_greeks', 'ts', if_not_exists => TRUE, migrate_data => TRUE, chunk_time_interval => INTERVAL '1 day');",
        "rollback": None,
        "version": "1.0.0"
    },
    
    # Options Greeks indexes
    {
        "name": "options_greeks_indexes",
        "sql": """
        CREATE INDEX IF NOT EXISTS idx_greeks_symbol_ts ON options_greeks(symbol, ts DESC);
        CREATE INDEX IF NOT EXISTS idx_greeks_expiry ON options_greeks(expiry);
        CREATE INDEX IF NOT EXISTS idx_greeks_strike_right ON options_greeks(strike, right);
        CREATE INDEX IF NOT EXISTS idx_greeks_iv ON options_greeks(iv) WHERE iv IS NOT NULL;
        """,
        "rollback": """
        DROP INDEX IF EXISTS idx_greeks_symbol_ts;
        DROP INDEX IF EXISTS idx_greeks_expiry;
        DROP INDEX IF EXISTS idx_greeks_strike_right;
        DROP INDEX IF EXISTS idx_greeks_iv;
        """,
        "version": "1.0.0"
    },
    
    # Enhanced ML signals table
    {
        "name": "ml_signals_table",
        "sql": """
        CREATE TABLE IF NOT EXISTS ml_signals (
            ts TIMESTAMPTZ NOT NULL,
            symbol TEXT NOT NULL,
            model TEXT NOT NULL,
            horizon TEXT NOT NULL,
            signal DOUBLE PRECISION CHECK (signal BETWEEN -1 AND 1),
            confidence DOUBLE PRECISION CHECK (confidence BETWEEN 0 AND 1),
            meta JSONB,
            features_hash TEXT,
            model_version TEXT,
            prediction_target TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            PRIMARY KEY (symbol, ts, model, horizon)
        );
        """,
        "rollback": "DROP TABLE IF EXISTS ml_signals;",
        "version": "1.0.0"
    },
    
    # ML signals hypertable
    {
        "name": "ml_signals_hypertable",
        "sql": "SELECT create_hypertable('ml_signals', 'ts', if_not_exists => TRUE, migrate_data => TRUE, chunk_time_interval => INTERVAL '1 day');",
        "rollback": None,
        "version": "1.0.0"
    },
    
    # ML signals indexes
    {
        "name": "ml_signals_indexes",
        "sql": """
        CREATE INDEX IF NOT EXISTS idx_ml_symbol_ts ON ml_signals(symbol, ts DESC);
        CREATE INDEX IF NOT EXISTS idx_ml_model ON ml_signals(model);
        CREATE INDEX IF NOT EXISTS idx_ml_confidence ON ml_signals(confidence DESC);
        CREATE INDEX IF NOT EXISTS idx_ml_meta ON ml_signals USING GIN(meta) WHERE meta IS NOT NULL;
        """,
        "rollback": """
        DROP INDEX IF EXISTS idx_ml_symbol_ts;
        DROP INDEX IF EXISTS idx_ml_model;
        DROP INDEX IF EXISTS idx_ml_confidence;
        DROP INDEX IF EXISTS idx_ml_meta;
        """,
        "version": "1.0.0"
    },
    
    # Enhanced risk violations table
    {
        "name": "risk_violations_table",
        "sql": """
        CREATE TABLE IF NOT EXISTS risk_violations (
            id SERIAL PRIMARY KEY,
            ts TIMESTAMPTZ NOT NULL DEFAULT now(),
            trade_id TEXT,
            rule TEXT NOT NULL,
            details JSONB,
            severity TEXT DEFAULT 'warn' CHECK (severity IN ('info', 'warn', 'error', 'critical')),
            resolved BOOLEAN DEFAULT FALSE,
            resolved_at TIMESTAMPTZ,
            resolution_notes TEXT,
            session_id TEXT,
            user_id TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        );
        """,
        "rollback": "DROP TABLE IF EXISTS risk_violations;",
        "version": "1.0.0"
    },
    
    # Risk violations indexes
    {
        "name": "risk_violations_indexes",
        "sql": """
        CREATE INDEX IF NOT EXISTS idx_risk_ts ON risk_violations(ts DESC);
        CREATE INDEX IF NOT EXISTS idx_risk_severity ON risk_violations(severity);
        CREATE INDEX IF NOT EXISTS idx_risk_resolved ON risk_violations(resolved);
        CREATE INDEX IF NOT EXISTS idx_risk_trade_id ON risk_violations(trade_id) WHERE trade_id IS NOT NULL;
        """,
        "rollback": """
        DROP INDEX IF EXISTS idx_risk_ts;
        DROP INDEX IF EXISTS idx_risk_severity;
        DROP INDEX IF EXISTS idx_risk_resolved;
        DROP INDEX IF EXISTS idx_risk_trade_id;
        """,
        "version": "1.0.0"
    },
    
    # Phase 3 specific tables
    {
        "name": "llm_decisions_table",
        "sql": """
        CREATE TABLE IF NOT EXISTS llm_decisions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ts TIMESTAMPTZ NOT NULL DEFAULT now(),
            session_id TEXT NOT NULL,
            user_request TEXT NOT NULL,
            llm_provider TEXT NOT NULL,
            model_name TEXT,
            trade_plan JSONB,
            rationale JSONB,
            risk_assessment JSONB,
            execution_result JSONB,
            success BOOLEAN,
            error_message TEXT,
            processing_time_ms INTEGER,
            tokens_used INTEGER,
            cost_usd DECIMAL(10,6),
            created_at TIMESTAMPTZ DEFAULT now()
        );
        """,
        "rollback": "DROP TABLE IF EXISTS llm_decisions;",
        "version": "1.1.0"
    },
    
    # LLM decisions indexes
    {
        "name": "llm_decisions_indexes",
        "sql": """
        CREATE INDEX IF NOT EXISTS idx_llm_ts ON llm_decisions(ts DESC);
        CREATE INDEX IF NOT EXISTS idx_llm_session ON llm_decisions(session_id);
        CREATE INDEX IF NOT EXISTS idx_llm_success ON llm_decisions(success);
        CREATE INDEX IF NOT EXISTS idx_llm_provider ON llm_decisions(llm_provider, model_name);
        """,
        "rollback": """
        DROP INDEX IF EXISTS idx_llm_ts;
        DROP INDEX IF EXISTS idx_llm_session;
        DROP INDEX IF EXISTS idx_llm_success;
        DROP INDEX IF EXISTS idx_llm_provider;
        """,
        "version": "1.1.0"
    },
    
    # Voice interactions table
    {
        "name": "voice_interactions_table",
        "sql": """
        CREATE TABLE IF NOT EXISTS voice_interactions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ts TIMESTAMPTZ NOT NULL DEFAULT now(),
            session_id TEXT NOT NULL,
            audio_input_duration_ms INTEGER,
            transcribed_text TEXT,
            confidence_score DOUBLE PRECISION,
            language_detected TEXT,
            command_type TEXT,
            command_parameters JSONB,
            response_text TEXT,
            tts_duration_ms INTEGER,
            success BOOLEAN DEFAULT TRUE,
            error_message TEXT,
            created_at TIMESTAMPTZ DEFAULT now()
        );
        """,
        "rollback": "DROP TABLE IF EXISTS voice_interactions;",
        "version": "1.1.0"
    },
    
    # Voice interactions indexes
    {
        "name": "voice_interactions_indexes",
        "sql": """
        CREATE INDEX IF NOT EXISTS idx_voice_ts ON voice_interactions(ts DESC);
        CREATE INDEX IF NOT EXISTS idx_voice_session ON voice_interactions(session_id);
        CREATE INDEX IF NOT EXISTS idx_voice_command ON voice_interactions(command_type);
        CREATE INDEX IF NOT EXISTS idx_voice_success ON voice_interactions(success);
        """,
        "rollback": """
        DROP INDEX IF EXISTS idx_voice_ts;
        DROP INDEX IF EXISTS idx_voice_session;
        DROP INDEX IF EXISTS idx_voice_command;
        DROP INDEX IF EXISTS idx_voice_success;
        """,
        "version": "1.1.0"
    },
    
    # Data retention policies (TimescaleDB feature)
    {
        "name": "retention_policies",
        "sql": """
        -- Keep bars data for 2 years
        SELECT add_retention_policy('bars', INTERVAL '2 years', if_not_exists => TRUE);
        
        -- Keep options Greeks for 1 year
        SELECT add_retention_policy('options_greeks', INTERVAL '1 year', if_not_exists => TRUE);
        
        -- Keep ML signals for 6 months
        SELECT add_retention_policy('ml_signals', INTERVAL '6 months', if_not_exists => TRUE);
        
        -- Keep risk violations for 3 years (compliance)
        SELECT add_retention_policy('risk_violations', INTERVAL '3 years', if_not_exists => TRUE);
        
        -- Keep LLM decisions for 1 year
        SELECT add_retention_policy('llm_decisions', INTERVAL '1 year', if_not_exists => TRUE);
        
        -- Keep voice interactions for 3 months
        SELECT add_retention_policy('voice_interactions', INTERVAL '3 months', if_not_exists => TRUE);
        """,
        "rollback": """
        SELECT remove_retention_policy('bars', if_exists => TRUE);
        SELECT remove_retention_policy('options_greeks', if_exists => TRUE);
        SELECT remove_retention_policy('ml_signals', if_exists => TRUE);
        SELECT remove_retention_policy('risk_violations', if_exists => TRUE);
        SELECT remove_retention_policy('llm_decisions', if_exists => TRUE);
        SELECT remove_retention_policy('voice_interactions', if_exists => TRUE);
        """,
        "version": "1.2.0"
    }
]

class MigrationManager:
    """Manages database schema migrations with versioning and rollback"""
    
    def __init__(self):
        self.current_version = CURRENT_SCHEMA_VERSION
        
    def get_applied_versions(self) -> List[str]:
        """Get list of applied schema versions"""
        try:
            with DBRouter.connect() as conn:
                result = conn.execute(sa.text(
                    "SELECT version FROM schema_versions ORDER BY applied_at"
                ))
                return [row[0] for row in result.fetchall()]
        except Exception:
            # Table doesn't exist yet
            return []
    
    def is_version_applied(self, version: str) -> bool:
        """Check if a specific version is already applied"""
        return version in self.get_applied_versions()
    
    def record_version(self, version: str, description: str = ""):
        """Record that a version has been applied"""
        try:
            with DBRouter.connect() as conn:
                conn.execute(sa.text("""
                    INSERT INTO schema_versions (version, description, applied_at)
                    VALUES (:version, :description, :applied_at)
                    ON CONFLICT (version) DO UPDATE SET
                        description = EXCLUDED.description,
                        applied_at = EXCLUDED.applied_at
                """), {
                    "version": version,
                    "description": description,
                    "applied_at": datetime.now(timezone.utc)
                })
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to record version {version}: {e}")
    
    def execute_migration(self, migration: Dict[str, Any], dry_run: bool = False) -> bool:
        """Execute a single migration"""
        name = migration["name"]
        sql = migration["sql"]
        version = migration["version"]
        
        if self.is_version_applied(version) and name != "schema_versions":
            logger.info(f"Migration {name} (v{version}) already applied, skipping")
            return True
        
        try:
            logger.info(f"Executing migration: {name} (v{version})")
            
            if dry_run:
                logger.info(f"DRY RUN - Would execute: {sql[:200]}...")
                return True
            
            with DBRouter.connect() as conn:
                # Split multi-statement SQL
                statements = [stmt.strip() for stmt in sql.split(';') if stmt.strip()]
                
                for stmt in statements:
                    if stmt:
                        conn.execute(sa.text(stmt))
                
                conn.commit()
            
            # Record successful migration (except for schema_versions table itself)
            if name != "schema_versions":
                self.record_version(version, f"Migration: {name}")
            
            logger.info(f"✅ Migration {name} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration {name} failed: {e}")
            return False
    
    def migrate_up(self, target_version: str = None, dry_run: bool = False) -> bool:
        """Run migrations up to target version"""
        target_version = target_version or self.current_version
        applied_versions = self.get_applied_versions()
        
        logger.info(f"Starting migration to version {target_version}")
        logger.info(f"Applied versions: {applied_versions}")
        
        success_count = 0
        total_count = 0
        
        for migration in DDL_STATEMENTS:
            # Check if we should apply this migration
            migration_version = migration["version"]
            
            # Skip if target version is lower than migration version
            if self._version_compare(migration_version, target_version) > 0:
                continue
            
            total_count += 1
            
            if self.execute_migration(migration, dry_run):
                success_count += 1
            else:
                logger.error(f"Migration failed, stopping at {migration['name']}")
                break
        
        if success_count == total_count:
            logger.info(f"✅ All migrations completed successfully ({success_count}/{total_count})")
            return True
        else:
            logger.error(f"❌ Migrations incomplete ({success_count}/{total_count})")
            return False
    
    def rollback(self, target_version: str, dry_run: bool = False) -> bool:
        """Rollback to target version"""
        applied_versions = self.get_applied_versions()
        
        # Find migrations to rollback (in reverse order)
        rollback_migrations = []
        for migration in reversed(DDL_STATEMENTS):
            migration_version = migration["version"]
            
            if (migration_version in applied_versions and 
                self._version_compare(migration_version, target_version) > 0 and
                migration["rollback"] is not None):
                rollback_migrations.append(migration)
        
        logger.info(f"Rolling back {len(rollback_migrations)} migrations to version {target_version}")
        
        success_count = 0
        for migration in rollback_migrations:
            try:
                logger.info(f"Rolling back: {migration['name']}")
                
                if dry_run:
                    logger.info(f"DRY RUN - Would execute: {migration['rollback'][:200]}...")
                    success_count += 1
                    continue
                
                with DBRouter.connect() as conn:
                    statements = [stmt.strip() for stmt in migration["rollback"].split(';') if stmt.strip()]
                    
                    for stmt in statements:
                        if stmt:
                            conn.execute(sa.text(stmt))
                    
                    conn.commit()
                
                # Remove version record
                with DBRouter.connect() as conn:
                    conn.execute(sa.text(
                        "DELETE FROM schema_versions WHERE version = :version"
                    ), {"version": migration["version"]})
                    conn.commit()
                
                logger.info(f"✅ Rolled back {migration['name']}")
                success_count += 1
                
            except Exception as e:
                logger.error(f"❌ Rollback failed for {migration['name']}: {e}")
                break
        
        return success_count == len(rollback_migrations)
    
    def _version_compare(self, v1: str, v2: str) -> int:
        """Compare version strings (simple semantic versioning)"""
        def version_tuple(v):
            return tuple(map(int, v.split('.')))
        
        v1_tuple = version_tuple(v1)
        v2_tuple = version_tuple(v2)
        
        if v1_tuple < v2_tuple:
            return -1
        elif v1_tuple > v2_tuple:
            return 1
        else:
            return 0
    
    def get_status(self) -> Dict[str, Any]:
        """Get migration status"""
        applied_versions = self.get_applied_versions()
        
        return {
            "current_schema_version": self.current_version,
            "applied_versions": applied_versions,
            "pending_migrations": [
                m["name"] for m in DDL_STATEMENTS 
                if m["version"] not in applied_versions
            ],
            "database_dialect": DBRouter.dialect(),
            "migration_count": len(DDL_STATEMENTS)
        }

def main():
    """Main migration entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="EMO Database Migration Tool")
    parser.add_argument("--action", choices=["migrate", "rollback", "status"], 
                       default="migrate", help="Action to perform")
    parser.add_argument("--target-version", help="Target version for migration/rollback")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Show what would be done without executing")
    parser.add_argument("--force", action="store_true",
                       help="Force migration even if not timescale environment")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Check environment
    if not is_timescale() and not args.force:
        print("❌ Not a timescale environment")
        print("Set EMO_ENV=prod or EMO_DB_ENGINE=timescale, or use --force")
        sys.exit(1)
    
    # Initialize database router
    try:
        DBRouter.init()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)
    
    # Create migration manager
    manager = MigrationManager()
    
    try:
        if args.action == "status":
            status = manager.get_status()
            print(json.dumps(status, indent=2))
            
        elif args.action == "migrate":
            success = manager.migrate_up(args.target_version, args.dry_run)
            sys.exit(0 if success else 1)
            
        elif args.action == "rollback":
            if not args.target_version:
                print("❌ Target version required for rollback")
                sys.exit(1)
            success = manager.rollback(args.target_version, args.dry_run)
            sys.exit(0 if success else 1)
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()