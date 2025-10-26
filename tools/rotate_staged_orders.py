#!/usr/bin/env python3
"""
Rotate/Archive Staged Order Drafts
==================================
Daily rotation and cleanup system for staged order files with:
- Cross-platform compatibility (cron/Task Scheduler)
- Configurable retention policies
- Safe archival with error handling
- Integration with enhanced logging

Features:
- Moves staged orders into date-named archive folders
- Configurable retention period (default: 14 days)
- Comprehensive error handling and logging
- Statistics and reporting
- Integration with enhanced configuration system

Usage:
  python tools/rotate_staged_orders.py [--dry-run] [--retention-days 7]
  
Environment Variables:
  EMO_STAGE_RETENTION_DAYS=14    # Days to keep archived orders
  EMO_STAGE_DIR=ops/orders/drafts # Override staging directory
  EMO_ARCHIVE_DIR=ops/orders/archive # Override archive directory
"""

import os
import shutil
import datetime as dt
import argparse
import logging
from pathlib import Path
import sys
from typing import Dict, List, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path for enhanced config
ROOT = Path(__file__).resolve().parents[1]
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
        def as_int(self, key: str, default: int = 0) -> int:
            try:
                return int(self.get(key, str(default)))
            except (ValueError, TypeError):
                return default
    config = FallbackConfig()

# Configuration with enhanced config integration
STAGED_DIR = Path(config.get("EMO_STAGE_DIR", "ops/orders/drafts"))
ARCHIVE_DIR = Path(config.get("EMO_ARCHIVE_DIR", "ops/orders/archive"))
RETENTION_DAYS = config.as_int("EMO_STAGE_RETENTION_DAYS", 14)

# Make paths absolute relative to ROOT
if not STAGED_DIR.is_absolute():
    STAGED_DIR = ROOT / STAGED_DIR
if not ARCHIVE_DIR.is_absolute():
    ARCHIVE_DIR = ROOT / ARCHIVE_DIR

def ensure_directories():
    """Create required directories if they don't exist."""
    try:
        STAGED_DIR.mkdir(parents=True, exist_ok=True)
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        logger.debug(f"📁 Directories ensured: {STAGED_DIR}, {ARCHIVE_DIR}")
    except Exception as e:
        logger.error(f"❌ Failed to create directories: {e}")
        raise

def get_rotation_stats() -> Dict[str, int]:
    """Get statistics about files to be rotated."""
    try:
        stats = {
            "yaml_files": len(list(STAGED_DIR.glob("*.yaml"))),
            "yml_files": len(list(STAGED_DIR.glob("*.yml"))),
            "json_files": len(list(STAGED_DIR.glob("*.json"))),
            "other_files": len([f for f in STAGED_DIR.glob("*") 
                              if f.is_file() and f.suffix not in [".yaml", ".yml", ".json"]])
        }
        stats["total_files"] = sum(stats.values())
        return stats
    except Exception as e:
        logger.error(f"❌ Failed to get rotation stats: {e}")
        return {"total_files": 0}

def rotate_today(dry_run: bool = False) -> Tuple[int, List[str]]:
    """
    Move today's staged drafts into a date-named folder.
    
    Args:
        dry_run: If True, only simulate the operation
        
    Returns:
        Tuple of (moved_count, error_list)
    """
    ensure_directories()
    
    today = dt.datetime.now().strftime("%Y-%m-%d")
    dest = ARCHIVE_DIR / today
    
    if not dry_run:
        dest.mkdir(parents=True, exist_ok=True)
    
    moved = 0
    errors = []
    
    # Get all order files (YAML, YML, JSON)
    order_patterns = ["*.yaml", "*.yml", "*.json"]
    order_files = []
    
    for pattern in order_patterns:
        order_files.extend(STAGED_DIR.glob(pattern))
    
    logger.info(f"📦 {'[DRY RUN] ' if dry_run else ''}Rotating {len(order_files)} files to {dest}")
    
    for file_path in order_files:
        try:
            dest_path = dest / file_path.name
            
            if dry_run:
                logger.info(f"  Would move: {file_path.name} -> {dest_path}")
                moved += 1
            else:
                # Check if destination file already exists
                if dest_path.exists():
                    # Add timestamp to make unique
                    timestamp = dt.datetime.now().strftime("%H%M%S")
                    stem = dest_path.stem
                    suffix = dest_path.suffix
                    dest_path = dest / f"{stem}_{timestamp}{suffix}"
                
                shutil.move(str(file_path), str(dest_path))
                logger.debug(f"  Moved: {file_path.name} -> {dest_path.name}")
                moved += 1
                
        except Exception as e:
            error_msg = f"Failed to move {file_path.name}: {e}"
            logger.error(f"⚠️ {error_msg}")
            errors.append(error_msg)
    
    if not dry_run and moved > 0:
        logger.info(f"✅ Rotated {moved} staged orders into {dest}")
    elif moved > 0:
        logger.info(f"✅ [DRY RUN] Would rotate {moved} staged orders into {dest}")
    else:
        logger.info("ℹ️ No staged orders found to rotate")
    
    return moved, errors

def get_archive_stats() -> Dict[str, any]:
    """Get statistics about archived folders."""
    try:
        archive_folders = [d for d in ARCHIVE_DIR.iterdir() if d.is_dir()]
        
        stats = {
            "total_folders": len(archive_folders),
            "folders_by_date": {},
            "total_archived_files": 0
        }
        
        for folder in archive_folders:
            try:
                # Count files in each archive folder
                files_count = len([f for f in folder.iterdir() if f.is_file()])
                stats["folders_by_date"][folder.name] = files_count
                stats["total_archived_files"] += files_count
            except Exception as e:
                logger.warning(f"⚠️ Error reading archive folder {folder.name}: {e}")
        
        return stats
    except Exception as e:
        logger.error(f"❌ Failed to get archive stats: {e}")
        return {"total_folders": 0, "total_archived_files": 0}

def prune_old_archives(retention_days: int, dry_run: bool = False) -> Tuple[int, List[str]]:
    """
    Remove archives older than retention_days.
    
    Args:
        retention_days: Number of days to keep archives
        dry_run: If True, only simulate the operation
        
    Returns:
        Tuple of (pruned_count, error_list)
    """
    cutoff = dt.datetime.now() - dt.timedelta(days=retention_days)
    pruned = 0
    errors = []
    
    logger.info(f"🧹 {'[DRY RUN] ' if dry_run else ''}Pruning archives older than {retention_days} days (before {cutoff.strftime('%Y-%m-%d')})")
    
    for folder in ARCHIVE_DIR.iterdir():
        if not folder.is_dir():
            continue
            
        try:
            # Parse folder name as date
            folder_date = dt.datetime.strptime(folder.name, "%Y-%m-%d")
        except ValueError:
            logger.warning(f"⚠️ Skipping non-date folder: {folder.name}")
            continue
        
        if folder_date < cutoff:
            try:
                if dry_run:
                    file_count = len([f for f in folder.iterdir() if f.is_file()])
                    logger.info(f"  Would remove: {folder.name} ({file_count} files)")
                    pruned += 1
                else:
                    file_count = len([f for f in folder.iterdir() if f.is_file()])
                    shutil.rmtree(folder)
                    logger.info(f"  Removed: {folder.name} ({file_count} files)")
                    pruned += 1
            except Exception as e:
                error_msg = f"Failed to remove {folder.name}: {e}"
                logger.error(f"⚠️ {error_msg}")
                errors.append(error_msg)
    
    if pruned > 0:
        if dry_run:
            logger.info(f"✅ [DRY RUN] Would prune {pruned} old archive folders")
        else:
            logger.info(f"✅ Pruned {pruned} old archive folders")
    else:
        logger.info("ℹ️ No old archives found to prune")
    
    return pruned, errors

def generate_report() -> Dict[str, any]:
    """Generate comprehensive rotation report."""
    try:
        rotation_stats = get_rotation_stats()
        archive_stats = get_archive_stats()
        
        report = {
            "timestamp": dt.datetime.now().isoformat(),
            "staging": {
                "directory": str(STAGED_DIR),
                "files_ready_for_rotation": rotation_stats["total_files"],
                "breakdown": rotation_stats
            },
            "archive": {
                "directory": str(ARCHIVE_DIR),
                "total_folders": archive_stats["total_folders"],
                "total_files": archive_stats["total_archived_files"],
                "folders_by_date": archive_stats.get("folders_by_date", {})
            },
            "configuration": {
                "retention_days": RETENTION_DAYS,
                "staged_dir": str(STAGED_DIR),
                "archive_dir": str(ARCHIVE_DIR)
            }
        }
        
        return report
    except Exception as e:
        logger.error(f"❌ Failed to generate report: {e}")
        return {"error": str(e)}

def main():
    """Main rotation and cleanup function with enhanced CLI."""
    parser = argparse.ArgumentParser(
        description="Rotate and archive staged order drafts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Normal rotation and cleanup
  python tools/rotate_staged_orders.py
  
  # Dry run to see what would happen
  python tools/rotate_staged_orders.py --dry-run
  
  # Custom retention period
  python tools/rotate_staged_orders.py --retention-days 7
  
  # Show statistics only
  python tools/rotate_staged_orders.py --report-only
        """
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Show what would be done without making changes"
    )
    parser.add_argument(
        "--retention-days", 
        type=int, 
        default=RETENTION_DAYS,
        help=f"Days to keep archived orders (default: {RETENTION_DAYS})"
    )
    parser.add_argument(
        "--report-only", 
        action="store_true", 
        help="Generate report without performing rotation/cleanup"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("🔄 EMO Order Rotation System")
    logger.info("=" * 40)
    
    try:
        # Generate initial report
        report = generate_report()
        
        if args.report_only:
            print("\n📊 Current Status Report:")
            print(f"Staging Directory: {report['staging']['directory']}")
            print(f"Files Ready for Rotation: {report['staging']['files_ready_for_rotation']}")
            print(f"Archive Directory: {report['archive']['directory']}")
            print(f"Total Archive Folders: {report['archive']['total_folders']}")
            print(f"Total Archived Files: {report['archive']['total_files']}")
            print(f"Retention Policy: {report['configuration']['retention_days']} days")
            
            if report['archive']['folders_by_date']:
                print("\nArchive Breakdown:")
                for date, count in sorted(report['archive']['folders_by_date'].items()):
                    print(f"  {date}: {count} files")
            
            return 0
        
        # Perform rotation
        rotated_count, rotation_errors = rotate_today(dry_run=args.dry_run)
        
        # Perform cleanup
        pruned_count, prune_errors = prune_old_archives(args.retention_days, dry_run=args.dry_run)
        
        # Summary
        total_errors = len(rotation_errors) + len(prune_errors)
        print(f"\n{'🔍 DRY RUN ' if args.dry_run else '✅ '}Summary:")
        print(f"  Rotated: {rotated_count} files")
        print(f"  Pruned: {pruned_count} old archives")
        print(f"  Errors: {total_errors}")
        
        if total_errors > 0:
            print("\n⚠️ Errors encountered:")
            for error in rotation_errors + prune_errors:
                print(f"  • {error}")
            return 1
        
        if args.dry_run:
            print("\n💡 Run without --dry-run to perform actual rotation/cleanup")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Fatal error in rotation system: {e}")
        return 2

if __name__ == "__main__":
    exit(main())