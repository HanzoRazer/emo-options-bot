#!/usr/bin/env python3
"""
Enhanced Command-line interface for EMO Options Bot Order Staging System
========================================================================
Provides easy command-line access to order staging functionality with:
- Database integration for persistent order tracking
- Institutional-grade risk assessment and compliance checking
- Integration with enhanced monitoring and reporting
- Multi-format output (YAML, JSON, Database)
- Professional workflow management

Features:
- SQLAlchemy 2.0+ database integration
- Risk scoring and compliance validation
- Approval workflow management
- Integration with institutional monitoring
- Enhanced metadata tracking
- Audit trail capabilities
"""

import os
import sys
import json
import uuid
import time
import argparse
import datetime as dt
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from decimal import Decimal

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def _stage_to_disk(out_dir: Path, payload: dict) -> Path:
    """
    Stage order to disk as YAML file.
    
    Args:
        out_dir: Output directory for staged files
        payload: Order payload dictionary
        
    Returns:
        Path to created file
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    sym = payload.get("symbol", "UNK")
    side = payload.get("side", "na")
    uid = uuid.uuid4().hex[:8]
    out = out_dir / f"{ts}_{sym}_{side}_{uid}.yaml"
    
    try:
        import yaml  # type: ignore
    except Exception:
        raise SystemExit("PyYAML required: pip install PyYAML")
    
    with open(out, "w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False)
    
    logger.info(f"📄 Staged draft: {out}")
    return out

def _try_write_db_row(file_path: Path, payload: dict) -> Optional[int]:
    """
    Enhanced database write for staged orders with institutional features.
    Includes risk assessment, compliance checking, and approval workflow.
    
    Args:
        file_path: Path to staged file
        payload: Order payload dictionary
        
    Returns:
        Order ID if successful, None if failed
    """
    try:
        from ops.db.session import init_db, get_session
        from ops.staging.models import StagedOrder, Base  # noqa
    except Exception as e:
        logger.warning(f"⚠️  DB write skipped (SQLAlchemy missing or import error): {e}")
        return None
    
    try:
        # Initialize database
        init_db()
        
        with get_session() as session:
            # Create enhanced staged order
            row = StagedOrder(
                symbol=payload.get("symbol", "UNK").upper(),
                side=payload.get("side", "buy").lower(),
                qty=int(payload.get("qty", 0) or 0),
                order_type=payload.get("type", "market").lower(),
                limit_price=Decimal(str(payload.get("limit"))) if payload.get("limit") else None,
                stop_price=Decimal(str(payload.get("stop"))) if payload.get("stop") else None,
                time_in_force=payload.get("time_in_force", "DAY").upper(),
                strategy=payload.get("strategy"),
                note=payload.get("note"),
                user=payload.get("user") or os.getenv("USER") or os.getenv("USERNAME"),
                raw_file=str(file_path),
                meta=payload.get("meta") or {},
                status="staged",
            )
            
            # Calculate risk score
            risk_score = row.calculate_risk_score()
            
            # Validate compliance
            compliance_issues = row.validate_compliance()
            
            # Check if approval required
            approval_needed = row.requires_approval()
            
            # Add to session and commit
            session.add(row)
            session.commit()
            
            # Log results
            logger.info(f"✅ DB row created (staged_orders.id={row.id})")
            logger.info(f"   Risk Score: {risk_score}")
            
            if compliance_issues:
                logger.warning(f"   Compliance Issues: {', '.join(compliance_issues)}")
            else:
                logger.info("   Compliance: ✅ Passed")
            
            if approval_needed:
                logger.warning(f"   🔒 Manual approval required")
                row.update_status("reviewed", user=row.user, note="Awaiting approval due to risk/compliance factors")
                session.commit()
            else:
                logger.info("   ✅ Ready for automated processing")
            
            # Integrate with institutional monitoring
            try:
                from src.database.institutional_integration import InstitutionalIntegration
                integration = InstitutionalIntegration()
                integration.log_system_event("order_staged", {
                    "order_id": row.id,
                    "symbol": row.symbol,
                    "side": row.side,
                    "qty": row.qty,
                    "risk_score": float(risk_score),
                    "approval_required": approval_needed,
                    "compliance_issues": len(compliance_issues)
                })
            except Exception as e:
                logger.debug(f"Institutional integration not available: {e}")
            
            return row.id
            
    except Exception as e:
        logger.error(f"⚠️  Failed to write staged order to DB: {e}")
        return None

def _get_institutional_status() -> Dict[str, Any]:
    """
    Get institutional system status for reporting.
    
    Returns:
        Dictionary with system status information
    """
    try:
        from src.database.institutional_integration import InstitutionalIntegration
        integration = InstitutionalIntegration()
        status = integration.check_system_health()
        return {
            "available": True,
            "health_score": status.system_health_score,
            "database_healthy": status.database_healthy,
            "environment": status.environment
        }
    except Exception as e:
        logger.debug(f"Institutional integration not available: {e}")
        return {"available": False, "error": str(e)}

def create_parser() -> argparse.ArgumentParser:
    """Create enhanced argument parser with institutional features."""
    parser = argparse.ArgumentParser(
        description="Enhanced EMO Options Bot Order Staging CLI with Institutional Features",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Stage a basic market order
  {sys.argv[0]} -s SPY --side buy --qty 100

  # Stage a limit order with strategy
  {sys.argv[0]} -s AAPL --side sell --qty 50 --type limit --limit 150.00 --strategy momentum

  # Stage with enhanced features
  {sys.argv[0]} -s QQQ --side buy --qty 25 --type limit --limit 300.00 \\
    --strategy iron_condor --note "Q4 position" --time-in-force IOC

  # View pending orders
  {sys.argv[0]} --list-pending

  # Check system status
  {sys.argv[0]} --status

Environment Variables:
  EMO_DB_URL=sqlite:///data/orders.sqlite   Database URL for order storage
  USER=trader_name                          Default user for order tracking
        """
    )
    
    # Required arguments (only when not using special commands)
    parser.add_argument(
        "-s", "--symbol", 
        help="Trading symbol (e.g., SPY, AAPL, QQQ)"
    )
    parser.add_argument(
        "--side", 
        required=False,
        choices=["buy", "sell"],
        help="Order side: buy or sell"
    )
    
    parser.add_argument(
        "--qty", 
        required=False,
        type=int,
        help="Order quantity (number of shares/contracts)"
    )
    
    # Optional order parameters
    parser.add_argument(
        "--type", 
        default="market",
        choices=["market", "limit", "stop", "stop_limit"],
        help="Order type (default: market)"
    )
    
    parser.add_argument(
        "--limit", 
        type=float,
        help="Limit price for limit orders"
    )
    
    parser.add_argument(
        "--stop", 
        type=float,
        help="Stop price for stop orders"
    )
    
    parser.add_argument(
        "--time-in-force", 
        default="DAY",
        choices=["DAY", "GTC", "IOC", "FOK"],
        help="Time in force (default: DAY)"
    )
    
    # Strategy and metadata
    parser.add_argument(
        "--strategy", 
        help="Trading strategy identifier"
    )
    
    parser.add_argument(
        "--note", 
        help="Optional note about the order"
    )
    
    parser.add_argument(
        "--user", 
        help="User creating the order (defaults to system user)"
    )
    
    # Output options
    parser.add_argument(
        "--outdir", 
        default=str(Path("ops") / "staged_orders"),
        help="Output directory for staged files"
    )
    
    parser.add_argument(
        "--format",
        choices=["yaml", "json"],
        default="yaml",
        help="Output format for staged files"
    )
    
    # Special commands
    parser.add_argument(
        "--list-pending",
        action="store_true",
        help="List pending orders in database"
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show system status"
    )
    
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize database tables"
    )
    
    parser.add_argument(
        "--db-only",
        action="store_true",
        help="Only write to database, skip file creation"
    )
    
    parser.add_argument(
        "--file-only",
        action="store_true",
        help="Only create file, skip database write"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force order staging even if validation fails (not recommended)"
    )
    
    return parser

def _list_pending_orders() -> None:
    """List pending orders from database."""
    try:
        from ops.db.session import get_session
        from ops.staging.models import StagedOrder
    except Exception as e:
        logger.error(f"Database not available: {e}")
        return
    
    try:
        with get_session() as session:
            # Get pending orders
            pending = StagedOrder.get_pending_approval(session, limit=50)
            staged = StagedOrder.get_by_status(session, "staged", limit=50)
            
            print("\n📋 Pending Orders Report")
            print("=" * 50)
            
            if pending:
                print(f"\n🔒 Orders Awaiting Approval ({len(pending)}):")
                for order in pending:
                    print(f"  {order.id:>3} | {order.symbol:<8} | {order.side:<4} | {order.qty:>6} | Risk: {order.risk_score or 0:.1f}")
            
            if staged:
                print(f"\n📝 Staged Orders ({len(staged)}):")
                for order in staged:
                    print(f"  {order.id:>3} | {order.symbol:<8} | {order.side:<4} | {order.qty:>6} | {order.created_at.strftime('%H:%M:%S')}")
            
            if not pending and not staged:
                print("  No pending orders found")
                
    except Exception as e:
        logger.error(f"Failed to list pending orders: {e}")

def _show_system_status() -> None:
    """Show comprehensive system status."""
    print("\n🏛️ EMO Options Bot System Status")
    print("=" * 50)
    
    # Database status
    try:
        from ops.db.session import test_connection, get_database_info
        db_info = get_database_info()
        
        print(f"\n📊 OPS Database:")
        print(f"  URL: {db_info.get('url', 'Unknown')}")
        print(f"  Dialect: {db_info.get('dialect', 'Unknown')}")
        print(f"  Status: {'✅ Healthy' if db_info.get('healthy') else '❌ Unhealthy'}")
        
    except Exception as e:
        print(f"\n📊 OPS Database: ❌ Error - {e}")
    
    # Institutional status
    inst_status = _get_institutional_status()
    print(f"\n🏛️ Institutional Infrastructure:")
    if inst_status.get("available"):
        print(f"  Status: ✅ Available")
        print(f"  Health Score: {inst_status.get('health_score', 0):.1f}%")
        print(f"  Environment: {inst_status.get('environment', 'Unknown')}")
        print(f"  Database: {'✅ Healthy' if inst_status.get('database_healthy') else '❌ Unhealthy'}")
    else:
        print(f"  Status: ⚠️ Not Available - {inst_status.get('error', 'Unknown')}")
    
    # File system status
    staging_dir = Path("ops") / "staged_orders"
    print(f"\n📁 File System:")
    print(f"  Staging Dir: {staging_dir}")
    print(f"  Exists: {'✅ Yes' if staging_dir.exists() else '❌ No'}")
    if staging_dir.exists():
        files = list(staging_dir.glob("*.yaml")) + list(staging_dir.glob("*.json"))
        print(f"  Staged Files: {len(files)}")

def _init_database() -> None:
    """Initialize database tables."""
    try:
        from ops.db.session import init_db
        engine = init_db()
        logger.info(f"✅ Database initialized: {engine.url}")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")

def main():
    """Enhanced main function with institutional features."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Handle special commands
    if args.init_db:
        _init_database()
        return
    
    if args.status:
        _show_system_status()
        return
    
    if args.list_pending:
        _list_pending_orders()
        return
    
    # Validate required arguments for order staging
    if not args.symbol or not args.side or args.qty is None:
        parser.error("--symbol, --side, and --qty are required for order staging")
    
    # Validate order parameters
    if args.type in ("limit", "stop_limit") and not args.limit:
        parser.error(f"--limit is required for {args.type} orders")
    
    if args.type in ("stop", "stop_limit") and not args.stop:
        parser.error(f"--stop is required for {args.type} orders")
    
    # Create order payload
    draft = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "symbol": args.symbol.upper(),
        "side": args.side.lower(),
        "qty": int(args.qty),
        "type": args.type.lower(),
        "limit": args.limit,
        "stop": args.stop,
        "time_in_force": getattr(args, 'time_in_force', 'DAY').upper(),
        "strategy": args.strategy,
        "note": args.note,
        "user": args.user,
        "meta": {
            "source": "stage_order_cli",
            "version": "v4_institutional",
            "cli_args": vars(args)
        },
    }
    
    # Remove None values
    draft = {k: v for k, v in draft.items() if v is not None}
    
    # Enhanced order validation
    logger.info("🔍 Running enhanced order validation...")
    try:
        from src.validation.order_validator import get_validation_summary
        validation_result = get_validation_summary(draft)
        
        if not validation_result['valid']:
            logger.error("❌ Order validation failed:")
            for error in validation_result['errors']:
                logger.error(f"   • {error}")
            
            if not args.force:
                logger.error("Use --force to override validation (not recommended)")
                return
            else:
                logger.warning("⚠️ Proceeding with invalid order due to --force flag")
        else:
            logger.info("✅ Order validation passed")
            logger.info(f"   Risk Score: {validation_result['risk_score']:.1f}/100")
            logger.info(f"   Compliance: {validation_result['compliance_status']}")
        
        # Add validation results to metadata
        draft['meta']['validation'] = validation_result
        
    except ImportError:
        logger.warning("⚠️ Enhanced validation not available - using basic validation only")
    except Exception as e:
        logger.warning(f"⚠️ Validation check failed: {e}")
    
    order_id = None
    file_path = None
    
    # Stage to file (unless --db-only)
    if not args.db_only:
        try:
            file_path = _stage_to_disk(Path(args.outdir), draft)
        except Exception as e:
            logger.error(f"Failed to stage file: {e}")
            return
    
    # Stage to database (unless --file-only)
    if not args.file_only:
        try:
            order_id = _try_write_db_row(file_path or Path("memory"), draft)
        except Exception as e:
            logger.error(f"Failed to stage to database: {e}")
    
    # Summary
    print("\n✅ Order Staging Complete")
    print("=" * 30)
    print(f"Symbol: {draft['symbol']}")
    print(f"Side: {draft['side'].upper()}")
    print(f"Quantity: {draft['qty']:,}")
    print(f"Type: {draft['type'].upper()}")
    
    if draft.get('limit'):
        print(f"Limit Price: ${draft['limit']:.2f}")
    if draft.get('stop'):
        print(f"Stop Price: ${draft['stop']:.2f}")
    
    if file_path:
        print(f"File: {file_path}")
    if order_id:
        print(f"Database ID: {order_id}")
    
    if args.strategy:
        print(f"Strategy: {args.strategy}")

if __name__ == "__main__":
    main()