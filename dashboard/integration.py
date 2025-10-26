"""
Dashboard Integration Script
Connects ML outlook system with dashboard display.
Provides automated data export and visualization hooks.
"""
import os
import sys
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.database.enhanced_router import DBRouter
from scripts.ml.enhanced_ml_outlook import MLOutlookEngine

logger = logging.getLogger(__name__)

class DashboardIntegrator:
    """Integrates ML system with dashboard display"""
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Output paths
        self.ml_outlook_path = self.data_dir / "ml_outlook.json"
        self.market_data_path = self.data_dir / "market_data.json"
        self.alerts_path = self.data_dir / "alerts.json"
        
        # Initialize ML engine
        try:
            self.ml_engine = MLOutlookEngine()
        except Exception as e:
            logger.warning(f"ML engine initialization failed: {e}")
            self.ml_engine = None
    
    def export_ml_outlook(self, symbol: str = "SPY") -> bool:
        """Export ML outlook to JSON for dashboard"""
        try:
            if not self.ml_engine:
                logger.error("ML engine not available")
                return False
            
            # Generate outlook
            outlook_data = self.ml_engine.generate_outlook(symbol)
            
            if outlook_data:
                # Add metadata
                export_data = {
                    **outlook_data,
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                    "dashboard_version": "1.0.0"
                }
                
                # Save to JSON
                with open(self.ml_outlook_path, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=2, default=str)
                
                logger.info(f"ML outlook exported to: {self.ml_outlook_path}")
                return True
            else:
                logger.warning("No outlook data generated")
                return False
                
        except Exception as e:
            logger.error(f"Failed to export ML outlook: {e}")
            return False
    
    def export_market_data(self, symbols: List[str] = None, hours: int = 24) -> bool:
        """Export recent market data for dashboard charts"""
        try:
            if symbols is None:
                symbols = ["SPY", "QQQ", "IWM"]
            
            market_data = {}
            
            for symbol in symbols:
                try:
                    # Get recent bars
                    start_time = datetime.now(timezone.utc) - timezone.timedelta(hours=hours)
                    
                    sql = """
                    SELECT ts, open, high, low, close, volume
                    FROM bars 
                    WHERE symbol = :symbol 
                        AND ts >= :start_time
                        AND timeframe = '1Min'
                    ORDER BY ts DESC
                    LIMIT 500
                    """
                    
                    df = DBRouter.fetch_df(sql, symbol=symbol, start_time=start_time)
                    
                    if not df.empty:
                        # Convert to chart-friendly format
                        chart_data = []
                        for _, row in df.iterrows():
                            chart_data.append({
                                "timestamp": row["ts"].isoformat() if hasattr(row["ts"], "isoformat") else str(row["ts"]),
                                "open": float(row["open"]),
                                "high": float(row["high"]),
                                "low": float(row["low"]),
                                "close": float(row["close"]),
                                "volume": int(row["volume"])
                            })
                        
                        market_data[symbol] = {
                            "data": chart_data,
                            "last_price": float(df.iloc[0]["close"]),
                            "change": float(df.iloc[0]["close"] - df.iloc[-1]["close"]) if len(df) > 1 else 0.0,
                            "change_percent": ((float(df.iloc[0]["close"]) / float(df.iloc[-1]["close"])) - 1) * 100 if len(df) > 1 else 0.0,
                            "last_updated": df.iloc[0]["ts"].isoformat() if hasattr(df.iloc[0]["ts"], "isoformat") else str(df.iloc[0]["ts"])
                        }
                        
                        logger.info(f"Exported {len(chart_data)} data points for {symbol}")
                    else:
                        logger.warning(f"No market data found for {symbol}")
                        market_data[symbol] = {
                            "data": [],
                            "last_price": 0.0,
                            "change": 0.0,
                            "change_percent": 0.0,
                            "last_updated": None
                        }
                        
                except Exception as e:
                    logger.error(f"Failed to export data for {symbol}: {e}")
                    continue
            
            # Add metadata
            export_data = {
                "symbols": market_data,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "hours_covered": hours,
                "dashboard_version": "1.0.0"
            }
            
            # Save to JSON
            with open(self.market_data_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, default=str)
            
            logger.info(f"Market data exported to: {self.market_data_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export market data: {e}")
            return False
    
    def check_and_create_alerts(self) -> bool:
        """Check system health and create alerts for dashboard"""
        try:
            alerts = []
            
            # Check database health
            try:
                db_status = DBRouter.get_status()
                if not db_status.get("healthy", False):
                    alerts.append({
                        "type": "error",
                        "title": "Database Health Issue",
                        "message": "Database connection or health check failed",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "details": db_status
                    })
            except Exception as e:
                alerts.append({
                    "type": "error",
                    "title": "Database Connection Failed",
                    "message": f"Cannot connect to database: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            # Check recent data freshness
            try:
                sql = "SELECT MAX(ts) as latest FROM bars WHERE ts >= :threshold"
                threshold = datetime.now(timezone.utc) - timezone.timedelta(hours=2)
                result = DBRouter.execute(sql, threshold=threshold).fetchone()
                
                if not result or not result[0]:
                    alerts.append({
                        "type": "warning",
                        "title": "Stale Market Data",
                        "message": "No recent market data found (>2 hours old)",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
            except Exception as e:
                alerts.append({
                    "type": "warning",
                    "title": "Data Check Failed",
                    "message": f"Cannot verify data freshness: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            # Check ML outlook freshness
            if self.ml_outlook_path.exists():
                try:
                    with open(self.ml_outlook_path, "r", encoding="utf-8") as f:
                        outlook = json.load(f)
                    
                    outlook_time = datetime.fromisoformat(outlook["ts"].replace('Z', '+00:00'))
                    age_hours = (datetime.now(timezone.utc) - outlook_time).total_seconds() / 3600
                    
                    if age_hours > 24:
                        alerts.append({
                            "type": "info",
                            "title": "ML Outlook Stale",
                            "message": f"ML outlook is {age_hours:.1f} hours old",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                except Exception as e:
                    alerts.append({
                        "type": "warning",
                        "title": "ML Outlook Check Failed",
                        "message": f"Cannot verify ML outlook: {str(e)}",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
            else:
                alerts.append({
                    "type": "info",
                    "title": "No ML Outlook",
                    "message": "ML outlook file not found. Run ML outlook generation.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            # Check for risk violations
            try:
                sql = """
                SELECT COUNT(*) as violation_count, 
                       COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_count
                FROM risk_violations 
                WHERE ts >= :threshold
                """
                threshold = datetime.now(timezone.utc) - timezone.timedelta(hours=24)
                result = DBRouter.execute(sql, threshold=threshold).fetchone()
                
                if result:
                    violation_count = result[0] or 0
                    critical_count = result[1] or 0
                    
                    if critical_count > 0:
                        alerts.append({
                            "type": "error",
                            "title": "Critical Risk Violations",
                            "message": f"{critical_count} critical risk violations in last 24 hours",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                    elif violation_count > 10:
                        alerts.append({
                            "type": "warning",
                            "title": "High Risk Violation Count",
                            "message": f"{violation_count} risk violations in last 24 hours",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
            except Exception:
                pass  # Risk violations table might not exist
            
            # Save alerts
            alert_data = {
                "alerts": alerts,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "alert_count": len(alerts),
                "dashboard_version": "1.0.0"
            }
            
            with open(self.alerts_path, "w", encoding="utf-8") as f:
                json.dump(alert_data, f, indent=2, default=str)
            
            logger.info(f"Generated {len(alerts)} alerts")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate alerts: {e}")
            return False
    
    def full_export(self, symbols: List[str] = None) -> Dict[str, bool]:
        """Perform full data export for dashboard"""
        results = {}
        
        logger.info("Starting full dashboard data export...")
        
        # Export ML outlook
        results["ml_outlook"] = self.export_ml_outlook()
        
        # Export market data
        results["market_data"] = self.export_market_data(symbols)
        
        # Generate alerts
        results["alerts"] = self.check_and_create_alerts()
        
        # Summary
        success_count = sum(results.values())
        logger.info(f"Export completed: {success_count}/{len(results)} successful")
        
        return results
    
    def cleanup_old_exports(self, days: int = 7) -> int:
        """Clean up old export files"""
        cleaned = 0
        cutoff = datetime.now() - timezone.timedelta(days=days)
        
        for file_path in self.data_dir.glob("*.json"):
            try:
                if file_path.stat().st_mtime < cutoff.timestamp():
                    # Don't delete current export files
                    if file_path.name not in ["ml_outlook.json", "market_data.json", "alerts.json"]:
                        file_path.unlink()
                        cleaned += 1
                        logger.info(f"Cleaned up old export: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up {file_path}: {e}")
        
        return cleaned

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Dashboard Integration")
    parser.add_argument("--export", choices=["ml", "market", "alerts", "all"], default="all",
                       help="What to export")
    parser.add_argument("--symbols", nargs="+", default=["SPY", "QQQ", "IWM"],
                       help="Symbols for market data export")
    parser.add_argument("--hours", type=int, default=24,
                       help="Hours of market data to export")
    parser.add_argument("--cleanup", action="store_true",
                       help="Clean up old export files")
    parser.add_argument("--data-dir", type=Path, default=Path("data"),
                       help="Data export directory")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize database
    try:
        DBRouter.init()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)
    
    # Initialize integrator
    integrator = DashboardIntegrator(args.data_dir)
    
    # Cleanup if requested
    if args.cleanup:
        cleaned = integrator.cleanup_old_exports()
        logger.info(f"Cleaned up {cleaned} old files")
    
    # Perform exports
    success = True
    
    if args.export in ["ml", "all"]:
        if not integrator.export_ml_outlook():
            success = False
    
    if args.export in ["market", "all"]:
        if not integrator.export_market_data(args.symbols, args.hours):
            success = False
    
    if args.export in ["alerts", "all"]:
        if not integrator.check_and_create_alerts():
            success = False
    
    if args.export == "all":
        results = integrator.full_export(args.symbols)
        success = all(results.values())
        
        print("\nExport Results:")
        for component, result in results.items():
            status = "✅" if result else "❌"
            print(f"  {status} {component}")
    
    if success:
        print(f"\n✅ Dashboard data exported to: {args.data_dir}")
        print("Dashboard files created:")
        for file_path in args.data_dir.glob("*.json"):
            print(f"  - {file_path.name}")
    else:
        print("\n❌ Some exports failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()