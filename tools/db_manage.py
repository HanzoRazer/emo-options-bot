#!/usr/bin/env python3
"""
Database Management Tool for EMO Options Bot
============================================
Comprehensive database management utility with institutional integration.

Features:
- Initialize and migrate databases (OPS and institutional)
- Import/export data with validation
- Database health monitoring and diagnostics
- Performance optimization and maintenance
- Backup and restore operations
- Data integrity checking and repair
- Integration with institutional systems

Usage:
    python db_manage.py init                    # Initialize databases
    python db_manage.py migrate                 # Run migrations
    python db_manage.py backup                  # Create backup
    python db_manage.py restore <file>          # Restore from backup
    python db_manage.py health                  # Check database health
    python db_manage.py optimize                # Optimize performance
    python db_manage.py import <file>           # Import data
    python db_manage.py export                  # Export data
    python db_manage.py repair                  # Repair data integrity
    python db_manage.py stats                   # Show statistics
"""

import argparse
import json
import logging
import os
import sys
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add project paths for imports
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

try:
    from ops.db.session import get_session, init_db, get_database_info, test_connection
    from ops.staging.models import StagedOrder
    OPS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"OPS database not available: {e}")
    OPS_AVAILABLE = False

try:
    from src.database.institutional_integration import InstitutionalIntegration
    from src.models.institutional_models import InstitutionalOrder
    INSTITUTIONAL_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Institutional database not available: {e}")
    INSTITUTIONAL_AVAILABLE = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Comprehensive database management with institutional integration."""
    
    def __init__(self):
        """Initialize database manager."""
        self.ops_available = OPS_AVAILABLE
        self.institutional_available = INSTITUTIONAL_AVAILABLE
        self.backup_dir = Path("backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        logger.info(f"Database Manager initialized")
        logger.info(f"  OPS Database: {'✅ Available' if self.ops_available else '❌ Not Available'}")
        logger.info(f"  Institutional: {'✅ Available' if self.institutional_available else '❌ Not Available'}")
    
    def initialize_databases(self) -> bool:
        """Initialize all available databases."""
        logger.info("🚀 Initializing databases...")
        success = True
        
        # Initialize OPS database
        if self.ops_available:
            try:
                logger.info("📦 Initializing OPS database...")
                init_db()
                
                # Test connection
                if test_connection():
                    logger.info("✅ OPS database initialized successfully")
                else:
                    logger.error("❌ OPS database initialization failed - connection test failed")
                    success = False
                    
            except Exception as e:
                logger.error(f"❌ OPS database initialization failed: {e}")
                success = False
        
        # Initialize institutional database
        if self.institutional_available:
            try:
                logger.info("🏛️ Initializing institutional database...")
                integration = InstitutionalIntegration()
                migration_status = integration.check_migration_status()
                
                if migration_status.needs_migration:
                    logger.info("🔄 Running institutional migrations...")
                    integration.run_migrations()
                
                logger.info("✅ Institutional database initialized successfully")
                
            except Exception as e:
                logger.error(f"❌ Institutional database initialization failed: {e}")
                success = False
        
        if success:
            logger.info("🎉 All databases initialized successfully")
        else:
            logger.error("💥 Database initialization had errors")
        
        return success
    
    def run_migrations(self) -> bool:
        """Run database migrations."""
        logger.info("🔄 Running database migrations...")
        success = True
        
        # OPS migrations
        if self.ops_available:
            try:
                logger.info("📦 Running OPS migrations...")
                init_db()  # This includes migration logic
                logger.info("✅ OPS migrations completed")
                
            except Exception as e:
                logger.error(f"❌ OPS migrations failed: {e}")
                success = False
        
        # Institutional migrations
        if self.institutional_available:
            try:
                logger.info("🏛️ Running institutional migrations...")
                integration = InstitutionalIntegration()
                integration.run_migrations()
                logger.info("✅ Institutional migrations completed")
                
            except Exception as e:
                logger.error(f"❌ Institutional migrations failed: {e}")
                success = False
        
        return success
    
    def create_backup(self, backup_name: Optional[str] = None) -> Path:
        """Create comprehensive database backup."""
        if not backup_name:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            backup_name = f"emo_backup_{timestamp}"
        
        backup_path = self.backup_dir / backup_name
        backup_path.mkdir(exist_ok=True)
        
        logger.info(f"📦 Creating backup: {backup_path}")
        
        # Backup OPS database
        if self.ops_available:
            try:
                ops_backup = backup_path / "ops_database.json"
                self._backup_ops_data(ops_backup)
                logger.info(f"✅ OPS data backed up to {ops_backup}")
                
            except Exception as e:
                logger.error(f"❌ OPS backup failed: {e}")
        
        # Backup institutional database
        if self.institutional_available:
            try:
                inst_backup = backup_path / "institutional_database.json"
                self._backup_institutional_data(inst_backup)
                logger.info(f"✅ Institutional data backed up to {inst_backup}")
                
            except Exception as e:
                logger.error(f"❌ Institutional backup failed: {e}")
        
        # Create backup metadata
        metadata = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "backup_name": backup_name,
            "ops_available": self.ops_available,
            "institutional_available": self.institutional_available,
            "version": "1.0"
        }
        
        metadata_file = backup_path / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"🎉 Backup completed: {backup_path}")
        return backup_path
    
    def restore_backup(self, backup_path: Path) -> bool:
        """Restore from backup."""
        if not backup_path.exists():
            logger.error(f"❌ Backup path does not exist: {backup_path}")
            return False
        
        logger.info(f"🔄 Restoring from backup: {backup_path}")
        
        # Load metadata
        metadata_file = backup_path / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            logger.info(f"📋 Backup metadata: {metadata}")
        
        success = True
        
        # Restore OPS data
        ops_backup = backup_path / "ops_database.json"
        if ops_backup.exists() and self.ops_available:
            try:
                self._restore_ops_data(ops_backup)
                logger.info("✅ OPS data restored")
            except Exception as e:
                logger.error(f"❌ OPS restore failed: {e}")
                success = False
        
        # Restore institutional data
        inst_backup = backup_path / "institutional_database.json"
        if inst_backup.exists() and self.institutional_available:
            try:
                self._restore_institutional_data(inst_backup)
                logger.info("✅ Institutional data restored")
            except Exception as e:
                logger.error(f"❌ Institutional restore failed: {e}")
                success = False
        
        return success
    
    def check_health(self) -> Dict[str, Any]:
        """Comprehensive database health check."""
        logger.info("🏥 Running database health check...")
        
        health = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_healthy": True,
            "ops_database": {},
            "institutional_database": {}
        }
        
        # OPS database health
        if self.ops_available:
            try:
                ops_health = self._check_ops_health()
                health["ops_database"] = ops_health
                if not ops_health.get("healthy", False):
                    health["overall_healthy"] = False
                    
            except Exception as e:
                logger.error(f"❌ OPS health check failed: {e}")
                health["ops_database"] = {"healthy": False, "error": str(e)}
                health["overall_healthy"] = False
        else:
            health["ops_database"] = {"available": False}
        
        # Institutional database health
        if self.institutional_available:
            try:
                inst_health = self._check_institutional_health()
                health["institutional_database"] = inst_health
                if not inst_health.get("healthy", False):
                    health["overall_healthy"] = False
                    
            except Exception as e:
                logger.error(f"❌ Institutional health check failed: {e}")
                health["institutional_database"] = {"healthy": False, "error": str(e)}
                health["overall_healthy"] = False
        else:
            health["institutional_database"] = {"available": False}
        
        status = "✅ Healthy" if health["overall_healthy"] else "❌ Issues Found"
        logger.info(f"🏥 Health check complete: {status}")
        
        return health
    
    def optimize_databases(self) -> bool:
        """Optimize database performance."""
        logger.info("⚡ Optimizing databases...")
        success = True
        
        # Optimize OPS database
        if self.ops_available:
            try:
                self._optimize_ops_database()
                logger.info("✅ OPS database optimized")
            except Exception as e:
                logger.error(f"❌ OPS optimization failed: {e}")
                success = False
        
        # Optimize institutional database
        if self.institutional_available:
            try:
                self._optimize_institutional_database()
                logger.info("✅ Institutional database optimized")
            except Exception as e:
                logger.error(f"❌ Institutional optimization failed: {e}")
                success = False
        
        return success
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        logger.info("📊 Collecting database statistics...")
        
        stats = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "ops_database": {},
            "institutional_database": {}
        }
        
        # OPS statistics
        if self.ops_available:
            try:
                stats["ops_database"] = self._get_ops_statistics()
            except Exception as e:
                logger.error(f"❌ OPS statistics failed: {e}")
                stats["ops_database"] = {"error": str(e)}
        else:
            stats["ops_database"] = {"available": False}
        
        # Institutional statistics
        if self.institutional_available:
            try:
                stats["institutional_database"] = self._get_institutional_statistics()
            except Exception as e:
                logger.error(f"❌ Institutional statistics failed: {e}")
                stats["institutional_database"] = {"error": str(e)}
        else:
            stats["institutional_database"] = {"available": False}
        
        return stats
    
    def repair_databases(self) -> bool:
        """Repair database integrity issues."""
        logger.info("🔧 Repairing databases...")
        success = True
        
        # Repair OPS database
        if self.ops_available:
            try:
                self._repair_ops_database()
                logger.info("✅ OPS database repaired")
            except Exception as e:
                logger.error(f"❌ OPS repair failed: {e}")
                success = False
        
        # Repair institutional database
        if self.institutional_available:
            try:
                self._repair_institutional_database()
                logger.info("✅ Institutional database repaired")
            except Exception as e:
                logger.error(f"❌ Institutional repair failed: {e}")
                success = False
        
        return success
    
    def import_data(self, import_file: Path) -> bool:
        """Import data from file."""
        if not import_file.exists():
            logger.error(f"❌ Import file does not exist: {import_file}")
            return False
        
        logger.info(f"📥 Importing data from: {import_file}")
        
        try:
            with open(import_file, 'r') as f:
                data = json.load(f)
            
            success = True
            
            # Import OPS data
            if "ops_orders" in data and self.ops_available:
                try:
                    self._import_ops_orders(data["ops_orders"])
                    logger.info("✅ OPS orders imported")
                except Exception as e:
                    logger.error(f"❌ OPS import failed: {e}")
                    success = False
            
            # Import institutional data
            if "institutional_orders" in data and self.institutional_available:
                try:
                    self._import_institutional_orders(data["institutional_orders"])
                    logger.info("✅ Institutional orders imported")
                except Exception as e:
                    logger.error(f"❌ Institutional import failed: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Import failed: {e}")
            return False
    
    def export_data(self, export_file: Optional[Path] = None) -> Path:
        """Export data to file."""
        if not export_file:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            export_file = Path(f"emo_export_{timestamp}.json")
        
        logger.info(f"📤 Exporting data to: {export_file}")
        
        export_data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "ops_orders": [],
            "institutional_orders": []
        }
        
        # Export OPS data
        if self.ops_available:
            try:
                export_data["ops_orders"] = self._export_ops_orders()
                logger.info(f"✅ Exported {len(export_data['ops_orders'])} OPS orders")
            except Exception as e:
                logger.error(f"❌ OPS export failed: {e}")
        
        # Export institutional data
        if self.institutional_available:
            try:
                export_data["institutional_orders"] = self._export_institutional_orders()
                logger.info(f"✅ Exported {len(export_data['institutional_orders'])} institutional orders")
            except Exception as e:
                logger.error(f"❌ Institutional export failed: {e}")
        
        with open(export_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"🎉 Export completed: {export_file}")
        return export_file
    
    # Private helper methods
    
    def _backup_ops_data(self, backup_file: Path):
        """Backup OPS database data."""
        with get_session() as session:
            orders = session.query(StagedOrder).all()  # type: ignore
            
            data = {
                "orders": [order.as_dict() for order in orders],
                "count": len(orders),
                "backed_up_at": datetime.now(timezone.utc).isoformat()
            }
            
            with open(backup_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
    
    def _backup_institutional_data(self, backup_file: Path):
        """Backup institutional database data."""
        integration = InstitutionalIntegration()
        
        # Get all institutional orders
        orders = integration.get_all_orders()
        
        data = {
            "orders": [order.to_dict() for order in orders],
            "count": len(orders),
            "backed_up_at": datetime.now(timezone.utc).isoformat()
        }
        
        with open(backup_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _restore_ops_data(self, backup_file: Path):
        """Restore OPS database data."""
        with open(backup_file, 'r') as f:
            data = json.load(f)
        
        with get_session() as session:
            # Clear existing data (careful!)
            session.query(StagedOrder).delete()  # type: ignore
            
            # Restore orders
            for order_data in data["orders"]:
                order = StagedOrder(**order_data)
                session.add(order)
            
            session.commit()
    
    def _restore_institutional_data(self, backup_file: Path):
        """Restore institutional database data."""
        with open(backup_file, 'r') as f:
            data = json.load(f)
        
        integration = InstitutionalIntegration()
        
        # Clear and restore data
        for order_data in data["orders"]:
            integration.create_order_from_dict(order_data)
    
    def _check_ops_health(self) -> Dict[str, Any]:
        """Check OPS database health."""
        info = get_database_info()
        connection_ok = test_connection()
        
        with get_session() as session:
            order_count = session.query(StagedOrder).count()  # type: ignore
        
        return {
            "healthy": connection_ok and order_count >= 0,
            "connection": connection_ok,
            "order_count": order_count,
            "database_info": info
        }
    
    def _check_institutional_health(self) -> Dict[str, Any]:
        """Check institutional database health."""
        integration = InstitutionalIntegration()
        status = integration.check_system_health()
        
        return {
            "healthy": status.database_healthy,
            "health_score": status.system_health_score,
            "environment": status.environment,
            "total_orders": status.total_orders,
            "migration_status": status.migration_status
        }
    
    def _optimize_ops_database(self):
        """Optimize OPS database performance."""
        # Run VACUUM and ANALYZE on SQLite
        db_info = get_database_info()
        db_path = db_info.get("database_path")
        
        if db_path and db_path.endswith('.db'):
            conn = sqlite3.connect(db_path)
            conn.execute("VACUUM")
            conn.execute("ANALYZE")
            conn.close()
    
    def _optimize_institutional_database(self):
        """Optimize institutional database performance."""
        integration = InstitutionalIntegration()
        integration.optimize_database()
    
    def _get_ops_statistics(self) -> Dict[str, Any]:
        """Get OPS database statistics."""
        with get_session() as session:
            total_orders = session.query(StagedOrder).count()  # type: ignore
            
            # Count by status
            status_counts = {}
            statuses = session.query(StagedOrder.status).distinct().all()  # type: ignore
            for (status,) in statuses:
                count = session.query(StagedOrder).filter(StagedOrder.status == status).count()  # type: ignore
                status_counts[status] = count
        
        return {
            "total_orders": total_orders,
            "status_distribution": status_counts,
            "database_info": get_database_info()
        }
    
    def _get_institutional_statistics(self) -> Dict[str, Any]:
        """Get institutional database statistics."""
        integration = InstitutionalIntegration()
        status = integration.check_system_health()
        
        return {
            "total_orders": status.total_orders,
            "active_orders": status.active_orders,
            "health_score": status.system_health_score,
            "environment": status.environment
        }
    
    def _repair_ops_database(self):
        """Repair OPS database integrity issues."""
        # Check for orphaned records, invalid data, etc.
        with get_session() as session:
            # Example: Remove orders with invalid symbols
            invalid_orders = session.query(StagedOrder).filter(
                (StagedOrder.symbol == None) | (StagedOrder.symbol == "")  # type: ignore
            ).all()
            
            for order in invalid_orders:
                logger.warning(f"Removing invalid order: {order.id}")
                session.delete(order)
            
            session.commit()
    
    def _repair_institutional_database(self):
        """Repair institutional database integrity issues."""
        integration = InstitutionalIntegration()
        integration.repair_data_integrity()
    
    def _import_ops_orders(self, orders_data: List[Dict[str, Any]]):
        """Import OPS orders from data."""
        with get_session() as session:
            for order_data in orders_data:
                order = StagedOrder(**order_data)
                session.add(order)
            session.commit()
    
    def _import_institutional_orders(self, orders_data: List[Dict[str, Any]]):
        """Import institutional orders from data."""
        integration = InstitutionalIntegration()
        for order_data in orders_data:
            integration.create_order_from_dict(order_data)
    
    def _export_ops_orders(self) -> List[Dict[str, Any]]:
        """Export OPS orders."""
        with get_session() as session:
            orders = session.query(StagedOrder).all()  # type: ignore
            return [order.as_dict() for order in orders]
    
    def _export_institutional_orders(self) -> List[Dict[str, Any]]:
        """Export institutional orders."""
        integration = InstitutionalIntegration()
        orders = integration.get_all_orders()
        return [order.to_dict() for order in orders]

def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(
        description="EMO Options Bot Database Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python db_manage.py init                    # Initialize databases
    python db_manage.py migrate                 # Run migrations
    python db_manage.py backup                  # Create backup
    python db_manage.py restore backups/backup1 # Restore from backup
    python db_manage.py health                  # Check database health
    python db_manage.py optimize                # Optimize performance
    python db_manage.py stats                   # Show statistics
        """
    )
    
    parser.add_argument(
        "command",
        choices=["init", "migrate", "backup", "restore", "health", "optimize", "import", "export", "repair", "stats"],
        help="Database management command"
    )
    
    parser.add_argument(
        "file",
        nargs="?",
        help="File path for restore/import/export operations"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize database manager
    db_manager = DatabaseManager()
    
    try:
        if args.command == "init":
            success = db_manager.initialize_databases()
            sys.exit(0 if success else 1)
            
        elif args.command == "migrate":
            success = db_manager.run_migrations()
            sys.exit(0 if success else 1)
            
        elif args.command == "backup":
            backup_path = db_manager.create_backup()
            print(f"Backup created: {backup_path}")
            
        elif args.command == "restore":
            if not args.file:
                print("Error: restore command requires a backup path")
                sys.exit(1)
            success = db_manager.restore_backup(Path(args.file))
            sys.exit(0 if success else 1)
            
        elif args.command == "health":
            health = db_manager.check_health()
            print(json.dumps(health, indent=2))
            sys.exit(0 if health["overall_healthy"] else 1)
            
        elif args.command == "optimize":
            success = db_manager.optimize_databases()
            sys.exit(0 if success else 1)
            
        elif args.command == "import":
            if not args.file:
                print("Error: import command requires a file path")
                sys.exit(1)
            success = db_manager.import_data(Path(args.file))
            sys.exit(0 if success else 1)
            
        elif args.command == "export":
            export_file = Path(args.file) if args.file else None
            result = db_manager.export_data(export_file)
            print(f"Data exported to: {result}")
            
        elif args.command == "repair":
            success = db_manager.repair_databases()
            sys.exit(0 if success else 1)
            
        elif args.command == "stats":
            stats = db_manager.get_statistics()
            print(json.dumps(stats, indent=2))
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Operation failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()