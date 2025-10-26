#!/usr/bin/env python3
"""
Enhanced Market Analysis Auto-Runner v2.0
==========================================
Robust orchestration system for EMO Options Bot with:
- Health monitoring integration
- Order staging and execution hooks
- Performance tracking and metrics
- Configuration hot-reloading
- Email notifications and backup management
- Integration with enhanced Phase 2 infrastructure

Features:
- Graceful dependency handling with fallbacks
- Multi-environment support (dev/staging/prod)
- Comprehensive error handling and logging
- Integration with enhanced config and health systems
"""

import time
import datetime as dt
import importlib
import json
import smtplib
import shutil
import os
import logging
from pathlib import Path
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List

# Setup robust logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

# Configuration
ENABLE_EMAIL_NOTIFICATIONS = os.getenv("EMO_EMAIL_NOTIFICATIONS", "0") == "1"
ENABLE_AUTO_BACKUP = os.getenv("EMO_AUTO_BACKUP", "1") == "1"
ENABLE_PERFORMANCE_MONITORING = os.getenv("EMO_PERFORMANCE_MONITORING", "1") == "1"
ENABLE_CONFIG_HOT_RELOAD = os.getenv("EMO_CONFIG_HOT_RELOAD", "1") == "1"
ENABLE_HEALTH_INTEGRATION = os.getenv("EMO_HEALTH_INTEGRATION", "1") == "1"

# Enhanced configuration
SLEEP_INTERVAL = int(os.getenv("EMO_SLEEP_INTERVAL", "300"))  # 5 minutes default
MAX_CYCLES = int(os.getenv("EMO_MAX_CYCLES", "0"))  # 0 = infinite
EMAIL_INTERVAL = int(os.getenv("EMO_EMAIL_INTERVAL", "3600"))  # 1 hour default
BACKUP_INTERVAL = int(os.getenv("EMO_BACKUP_INTERVAL", "86400"))  # 24 hours default

# File paths
DATA_DIR = ROOT / "data"
BACKUP_DIR = ROOT / "backups"
LOGS_DIR = ROOT / "logs"
CONFIG_FILE = ROOT / "config.json"   # Dynamic configuration file

# Ensure directories exist
for directory in [DATA_DIR, BACKUP_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Health server integration (optional)
_health = None
if ENABLE_HEALTH_INTEGRATION:
    try:
        _health = importlib.import_module("tools.emit_health")
        logger.info("✅ Health monitoring integration enabled")
    except Exception as e:
        logger.warning(f"⚠️ Health monitoring not available: {e}")
        _health = None

# Enhanced configuration system integration
_config = None
try:
    from utils.enhanced_config import Config
    _config = Config()
    logger.info("✅ Enhanced configuration system loaded")
except Exception as e:
    logger.warning(f"⚠️ Enhanced config not available, using fallback: {e}")
    class FallbackConfig:
        def get(self, key: str, default: str = None) -> str:
            return os.getenv(key, default)
        def as_bool(self, key: str, default: bool = False) -> bool:
            return os.getenv(key, "0").lower() in ("1", "true", "yes", "on")
    _config = FallbackConfig()

# Try to import original describer, graceful fallback if dependencies missing
try:
    from app_describer import run_once
    logger.info("✅ Main describer module loaded")
except ImportError as e:
    logger.error(f"❌ Could not import app_describer: {e}")
    logger.info("🔄 Creating fallback run_once function")
    def run_once():
        return {"status": "fallback", "message": "app_describer not available"}

# Performance metrics tracking
_performance_metrics = {
    "cycle_times": [],
    "error_count": 0,
    "last_successful_run": None,
    "last_error": None,
    "total_cycles": 0,
    "uptime_start": time.time(),
    "last_email": None,
    "last_backup": None
}

def _is_staging_enabled() -> bool:
    """Check if order staging is enabled (EMO_STAGE_ORDERS=1)."""
    return _config.get("EMO_STAGE_ORDERS", "0").strip() == "1"

def load_dynamic_config() -> Dict[str, Any]:
    """Load configuration from JSON file with hot-reload capability."""
    if not ENABLE_CONFIG_HOT_RELOAD or not CONFIG_FILE.exists():
        return {}
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        logger.debug(f"📋 Loaded dynamic config: {len(config)} entries")
        return config
    except Exception as e:
        logger.error(f"❌ Failed to load dynamic config: {e}")
        return {}

def save_dynamic_config(config: Dict[str, Any]):
    """Save configuration to JSON file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2, default=str)
        logger.debug("💾 Saved dynamic configuration")
    except Exception as e:
        logger.error(f"❌ Failed to save dynamic config: {e}")

def send_email(subject: str, body: str, to_email: str = None):
    """Send email notification with robust error handling."""
    if not ENABLE_EMAIL_NOTIFICATIONS:
        return
    
    try:
        smtp_server = _config.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(_config.get("SMTP_PORT", "587"))
        smtp_user = _config.get("SMTP_USER")
        smtp_pass = _config.get("SMTP_PASS")
        
        if not all([smtp_user, smtp_pass]):
            logger.warning("⚠️ Email credentials not configured")
            return
        
        to_email = to_email or _config.get("NOTIFY_EMAIL", smtp_user)
        
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = f"[EMO Bot] {subject}"
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        
        logger.info(f"📧 Email sent: {subject}")
        _performance_metrics["last_email"] = time.time()
        
    except Exception as e:
        logger.error(f"❌ Email sending failed: {e}")

def create_backup():
    """Create backup of critical files with rotation."""
    if not ENABLE_AUTO_BACKUP:
        return
    
    try:
        timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Backup critical directories
        critical_dirs = ["data", "ops", "logs"]
        backed_up = 0
        
        for dir_name in critical_dirs:
            source_dir = ROOT / dir_name
            if source_dir.exists():
                dest_dir = backup_path / dir_name
                shutil.copytree(source_dir, dest_dir, ignore_errors=True)
                backed_up += 1
        
        # Backup configuration files
        config_files = [".env", "config.json", "requirements.txt"]
        for config_file in config_files:
            source_file = ROOT / config_file
            if source_file.exists():
                shutil.copy2(source_file, backup_path)
                backed_up += 1
        
        # Cleanup old backups (keep last 10)
        backups = sorted(BACKUP_DIR.glob("backup_*"), key=lambda x: x.stat().st_mtime)
        while len(backups) > 10:
            old_backup = backups.pop(0)
            shutil.rmtree(old_backup, ignore_errors=True)
            logger.debug(f"🗑️ Removed old backup: {old_backup.name}")
        
        logger.info(f"💾 Backup created: {backup_path.name} ({backed_up} items)")
        _performance_metrics["last_backup"] = time.time()
        
    except Exception as e:
        logger.error(f"❌ Backup creation failed: {e}")

def log_performance_metrics():
    """Log current performance metrics."""
    try:
        uptime = time.time() - _performance_metrics["uptime_start"]
        avg_cycle_time = 0
        if _performance_metrics["cycle_times"]:
            avg_cycle_time = sum(_performance_metrics["cycle_times"]) / len(_performance_metrics["cycle_times"])
        
        metrics = {
            "uptime_hours": round(uptime / 3600, 2),
            "total_cycles": _performance_metrics["total_cycles"],
            "error_count": _performance_metrics["error_count"],
            "avg_cycle_time": round(avg_cycle_time, 2),
            "last_successful_run": _performance_metrics["last_successful_run"],
            "memory_cycles": len(_performance_metrics["cycle_times"])
        }
        
        logger.info(f"📊 Performance: {metrics}")
        return metrics
        
    except Exception as e:
        logger.error(f"❌ Performance logging failed: {e}")
        return {}

def _rebuild_pipeline():
    """Rebuild dashboard and pipeline components."""
    try:
        logger.info("🔧 Rebuilding analysis pipeline...")
        build = importlib.import_module("tools.build_dashboard")
        build.main()
        logger.info("✅ Pipeline rebuild complete")
    except Exception as e:
        logger.error(f"❌ Pipeline rebuild failed: {e}")

def _maybe_snapshot_health():
    """Push a snapshot into the health server if available."""
    if not _health:
        return
    try:
        _health.snapshot(_performance_metrics)
        logger.debug("📊 Health snapshot updated")
    except Exception as e:
        logger.debug(f"⚠️ Health snapshot failed: {e}")

def _maybe_execute_or_stage_orders(orders: Optional[List[Dict[str, Any]]] = None):
    """
    Hook to either stage orders or execute them based on configuration.
    - If EMO_STAGE_ORDERS=1, stage to files (no execution).
    - Else, attempt to execute via broker module if available.
    """
    if not orders:
        return
    
    try:
        if _is_staging_enabled():
            # Stage orders to files
            logger.info(f"🗂️ Staging {len(orders)} orders...")
            try:
                st = importlib.import_module("tools.stage_order_cli")
            except Exception:
                st = None
            
            if not st:
                logger.warning("🗂️ Staging requested but tools.stage_order_cli not found. Skipping.")
                return
            
            staged_count = 0
            for order in orders:
                try:
                    # Call staging function with order parameters
                    if hasattr(st, 'stage_order_cli_entry'):
                        st.stage_order_cli_entry(
                            symbol=order.get("symbol", ""),
                            side=order.get("side", "buy"),
                            qty=order.get("qty", 1),
                            strategy=order.get("strategy", "unknown"),
                            note=order.get("note", "runner")
                        )
                    else:
                        # Fallback to direct file creation
                        from tools.stage_order_cli import create_order_draft
                        create_order_draft(order)
                    
                    logger.info(f"🗂️ Staged order: {order}")
                    staged_count += 1
                except Exception as e:
                    logger.error(f"⚠️ Failed to stage {order}: {e}")
            
            logger.info(f"✅ Successfully staged {staged_count}/{len(orders)} orders")
            
        else:
            # Try to execute via live broker if available
            logger.info(f"🟢 Attempting live execution of {len(orders)} orders...")
            try:
                broker_mod = importlib.import_module("exec.alpaca_broker")
                broker = broker_mod.AlpacaBroker(paper=True)
                
                executed_count = 0
                for order in orders:
                    try:
                        broker.submit_order(
                            order["symbol"],
                            order.get("qty", 1),
                            order.get("side", "buy"),
                            order.get("type", "market")
                        )
                        logger.info(f"🟢 Executed order: {order}")
                        executed_count += 1
                    except Exception as e:
                        logger.error(f"⚠️ Failed to execute {order}: {e}")
                
                logger.info(f"✅ Successfully executed {executed_count}/{len(orders)} orders")
                
            except Exception as e:
                logger.warning(f"⚠️ Live execution not available: {e}")
                logger.info("💡 Consider setting EMO_STAGE_ORDERS=1 to stage orders instead")
                
    except Exception as e:
        logger.error(f"❌ Order processing error: {e}")

def main():
    """Main orchestration loop with enhanced error handling and monitoring."""
    print("🚀 Enhanced Market Analysis Auto-Runner v2.0")
    print("=" * 60)
    
    # Load initial configuration
    dynamic_config = load_dynamic_config()
    
    # Log startup information
    logger.info("🔧 Configuration:")
    logger.info(f"   Sleep Interval: {SLEEP_INTERVAL}s")
    logger.info(f"   Max Cycles: {MAX_CYCLES if MAX_CYCLES > 0 else 'Unlimited'}")
    logger.info(f"   Email Notifications: {'✅' if ENABLE_EMAIL_NOTIFICATIONS else '❌'}")
    logger.info(f"   Auto Backup: {'✅' if ENABLE_AUTO_BACKUP else '❌'}")
    logger.info(f"   Health Integration: {'✅' if _health else '❌'}")
    logger.info(f"   Order Staging: {'✅' if _is_staging_enabled() else '❌'}")
    
    # Initial health snapshot
    _maybe_snapshot_health()
    
    # Send startup notification
    if ENABLE_EMAIL_NOTIFICATIONS:
        send_email("Auto-Runner Started", f"Enhanced Auto-Runner v2.0 started at {dt.datetime.now()}")
    
    cycle_count = 0
    
    try:
        while MAX_CYCLES == 0 or cycle_count < MAX_CYCLES:
            cycle_count += 1
            cycle_start = time.time()
            
            logger.info(f"🔄 Starting cycle {cycle_count}")
            
            try:
                # Hot-reload dynamic configuration
                if ENABLE_CONFIG_HOT_RELOAD:
                    dynamic_config = load_dynamic_config()
                
                # Run main analysis
                result = run_once()
                
                # Process any generated orders
                if isinstance(result, dict) and "orders" in result:
                    _maybe_execute_or_stage_orders(result["orders"])
                
                # Update performance metrics
                cycle_time = time.time() - cycle_start
                _performance_metrics["cycle_times"].append(cycle_time)
                _performance_metrics["total_cycles"] = cycle_count
                _performance_metrics["last_successful_run"] = dt.datetime.now().isoformat()
                
                # Keep only last 100 cycle times to prevent memory growth
                if len(_performance_metrics["cycle_times"]) > 100:
                    _performance_metrics["cycle_times"] = _performance_metrics["cycle_times"][-100:]
                
                logger.info(f"⏱️ Cycle {cycle_count} completed in {cycle_time:.2f}s")
                
            except Exception as e:
                _performance_metrics["error_count"] += 1
                _performance_metrics["last_error"] = str(e)
                logger.error(f"❌ Cycle {cycle_count} failed: {e}")
                
                # Send error notification (rate limited)
                if (ENABLE_EMAIL_NOTIFICATIONS and 
                    (_performance_metrics["last_email"] is None or 
                     time.time() - _performance_metrics["last_email"] > EMAIL_INTERVAL)):
                    send_email(f"Cycle {cycle_count} Error", f"Error: {e}\n\nTime: {dt.datetime.now()}")
            
            # Update health snapshot
            _maybe_snapshot_health()
            
            # Performance summary every 10 cycles
            if ENABLE_PERFORMANCE_MONITORING and cycle_count % 10 == 0:
                metrics = log_performance_metrics()
                
                # Save metrics to dynamic config
                dynamic_config["performance_metrics"] = metrics
                save_dynamic_config(dynamic_config)
            
            # Periodic backup
            if (ENABLE_AUTO_BACKUP and 
                (_performance_metrics["last_backup"] is None or 
                 time.time() - _performance_metrics["last_backup"] > BACKUP_INTERVAL)):
                create_backup()
            
            # Rebuild pipeline periodically (every 50 cycles)
            if cycle_count % 50 == 0:
                _rebuild_pipeline()
            
            logger.info(f"😴 Sleeping for {SLEEP_INTERVAL}s until next cycle...")
            time.sleep(SLEEP_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("⏹️ Received interrupt signal, shutting down gracefully...")
        
    except Exception as e:
        logger.error(f"❌ Fatal error in main loop: {e}")
        if ENABLE_EMAIL_NOTIFICATIONS:
            send_email("Fatal Error", f"Auto-runner crashed: {e}\n\nTime: {dt.datetime.now()}")
        raise
        
    finally:
        # Final metrics and cleanup
        final_metrics = log_performance_metrics()
        logger.info("🏁 Auto-runner shutting down")
        logger.info(f"📊 Final stats: {final_metrics}")
        
        # Send shutdown notification
        if ENABLE_EMAIL_NOTIFICATIONS:
            send_email("Auto-Runner Stopped", f"Enhanced Auto-Runner stopped after {cycle_count} cycles\n\nFinal metrics: {final_metrics}")

if __name__ == "__main__":
    main()