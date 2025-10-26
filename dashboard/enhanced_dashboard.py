"""
Enhanced Dashboard System
Integrates ML outlook, Phase 3 components, and real-time data.
Provides comprehensive monitoring and control interface.
"""
import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
import asyncio

# Web framework
try:
    from fastapi import FastAPI, Request, WebSocket, HTTPException
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from fastapi.responses import HTMLResponse, JSONResponse
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Add project root to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.database.enhanced_router import DBRouter, get_db_status
from phase3_integration import Phase3TradingSystem

logger = logging.getLogger(__name__)

class DashboardDataProvider:
    """Provides data for dashboard components"""
    
    def __init__(self):
        pass
    
    def load_ml_outlook(self) -> Optional[Dict]:
        """Load ML outlook from JSON file"""
        try:
            outlook_path = Path("data") / "ml_outlook.json"
            if outlook_path.exists():
                with open(outlook_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Failed to load ML outlook: {e}")
            return None
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary from database"""
        try:
            # Get recent staged orders
            sql_orders = """
            SELECT COUNT(*) as total_orders, 
                   COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_orders,
                   COUNT(CASE WHEN status = 'executed' THEN 1 END) as executed_orders
            FROM staged_orders 
            WHERE created_at >= :start_date
            """
            
            start_date = datetime.now(timezone.utc) - timedelta(days=7)
            orders_result = DBRouter.execute(sql_orders, start_date=start_date).fetchone()
            
            # Get recent risk violations
            sql_risk = """
            SELECT COUNT(*) as total_violations,
                   COUNT(CASE WHEN severity = 'critical' THEN 1 END) as critical_violations
            FROM risk_violations 
            WHERE ts >= :start_date
            """
            
            risk_result = DBRouter.execute(sql_risk, start_date=start_date).fetchone()
            
            # Get database status
            db_status = get_db_status()
            
            return {
                "orders": {
                    "total": orders_result[0] if orders_result else 0,
                    "pending": orders_result[1] if orders_result else 0,
                    "executed": orders_result[2] if orders_result else 0
                },
                "risk": {
                    "total_violations": risk_result[0] if risk_result else 0,
                    "critical_violations": risk_result[1] if risk_result else 0
                },
                "database": {
                    "status": "healthy" if db_status.get("healthy") else "error",
                    "size_mb": round(db_status.get("database_size_bytes", 0) / 1024 / 1024, 1),
                    "tables": len(db_status.get("tables", []))
                },
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get portfolio summary: {e}")
            return {
                "orders": {"total": 0, "pending": 0, "executed": 0},
                "risk": {"total_violations": 0, "critical_violations": 0},
                "database": {"status": "error", "size_mb": 0, "tables": 0},
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
    
    def get_recent_market_data(self, symbol: str = "SPY", hours: int = 24) -> List[Dict]:
        """Get recent market data for charts"""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(hours=hours)
            
            sql = """
            SELECT ts, open, high, low, close, volume
            FROM bars 
            WHERE symbol = :symbol 
                AND ts >= :start_date
                AND timeframe = '1Min'
            ORDER BY ts
            LIMIT 1000
            """
            
            df = DBRouter.fetch_df(sql, symbol=symbol, start_date=start_date)
            
            if not df.empty:
                # Sample data for performance (every 5 minutes)
                df_sampled = df.iloc[::5] if len(df) > 100 else df
                
                return [
                    {
                        "timestamp": row["ts"].isoformat() if hasattr(row["ts"], "isoformat") else str(row["ts"]),
                        "open": float(row["open"]),
                        "high": float(row["high"]), 
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                        "volume": int(row["volume"])
                    }
                    for _, row in df_sampled.iterrows()
                ]
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get market data for {symbol}: {e}")
            return []
    
    def get_ml_performance_metrics(self) -> Dict[str, Any]:
        """Get ML model performance metrics"""
        try:
            # Get recent predictions
            sql = """
            SELECT model, AVG(confidence) as avg_confidence, COUNT(*) as prediction_count
            FROM ml_signals 
            WHERE ts >= :start_date
            GROUP BY model
            ORDER BY prediction_count DESC
            """
            
            start_date = datetime.now(timezone.utc) - timedelta(days=7)
            result = DBRouter.execute(sql, start_date=start_date).fetchall()
            
            models = []
            for row in result:
                models.append({
                    "name": row[0],
                    "avg_confidence": round(float(row[1]), 3),
                    "prediction_count": int(row[2])
                })
            
            return {
                "models": models,
                "total_predictions": sum(m["prediction_count"] for m in models),
                "avg_confidence": round(sum(m["avg_confidence"] * m["prediction_count"] for m in models) / 
                                      max(sum(m["prediction_count"] for m in models), 1), 3)
            }
            
        except Exception as e:
            logger.error(f"Failed to get ML performance metrics: {e}")
            return {"models": [], "total_predictions": 0, "avg_confidence": 0.0}
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            # Check database
            db_status = get_db_status()
            db_healthy = db_status.get("healthy", False)
            
            # Check recent data ingestion
            sql = """
            SELECT MAX(ts) as latest_data, COUNT(*) as recent_count
            FROM bars 
            WHERE ts >= :start_date
            """
            
            start_date = datetime.now(timezone.utc) - timedelta(hours=2)
            data_result = DBRouter.execute(sql, start_date=start_date).fetchone()
            
            latest_data = data_result[0] if data_result and data_result[0] else None
            recent_data_count = data_result[1] if data_result else 0
            
            # Check if data is recent (within last hour)
            data_fresh = False
            if latest_data:
                if isinstance(latest_data, str):
                    latest_data = datetime.fromisoformat(latest_data.replace('Z', '+00:00'))
                data_age = (datetime.now(timezone.utc) - latest_data).total_seconds() / 3600
                data_fresh = data_age < 1.0  # Less than 1 hour old
            
            # Check ML outlook
            ml_outlook = self.load_ml_outlook()
            ml_fresh = False
            if ml_outlook:
                outlook_time = datetime.fromisoformat(ml_outlook["ts"].replace('Z', '+00:00'))
                ml_age = (datetime.now(timezone.utc) - outlook_time).total_seconds() / 3600
                ml_fresh = ml_age < 12.0  # Less than 12 hours old
            
            # Overall health score
            health_components = [db_healthy, data_fresh, ml_fresh]
            health_score = sum(health_components) / len(health_components)
            
            if health_score >= 0.8:
                health_status = "healthy"
            elif health_score >= 0.5:
                health_status = "warning"
            else:
                health_status = "error"
            
            return {
                "overall_status": health_status,
                "health_score": round(health_score, 2),
                "components": {
                    "database": {"status": "healthy" if db_healthy else "error", "details": db_status},
                    "data_ingestion": {
                        "status": "healthy" if data_fresh else "warning",
                        "latest_data": latest_data.isoformat() if latest_data else None,
                        "recent_count": recent_data_count
                    },
                    "ml_outlook": {
                        "status": "healthy" if ml_fresh else "warning",
                        "available": ml_outlook is not None,
                        "last_update": ml_outlook["ts"] if ml_outlook else None
                    }
                },
                "last_checked": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {
                "overall_status": "error",
                "health_score": 0.0,
                "error": str(e),
                "last_checked": datetime.now(timezone.utc).isoformat()
            }

# FastAPI app (if available)
if FASTAPI_AVAILABLE:
    app = FastAPI(title="EMO Options Bot Dashboard", version="1.0.0")
    
    # Mount static files
    dashboard_dir = Path(__file__).parent
    static_dir = dashboard_dir / "static"
    templates_dir = dashboard_dir / "templates"
    
    static_dir.mkdir(exist_ok=True)
    templates_dir.mkdir(exist_ok=True)
    
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    templates = Jinja2Templates(directory=templates_dir)
    
    # Data provider
    data_provider = DashboardDataProvider()
    
    @app.get("/", response_class=HTMLResponse)
    async def dashboard_home(request: Request):
        """Main dashboard page"""
        return templates.TemplateResponse("dashboard.html", {"request": request})
    
    @app.get("/api/ml-outlook")
    async def get_ml_outlook():
        """Get ML outlook data"""
        outlook = data_provider.load_ml_outlook()
        if outlook:
            return JSONResponse(outlook)
        else:
            raise HTTPException(status_code=404, detail="ML outlook not available")
    
    @app.get("/api/portfolio-summary")
    async def get_portfolio_summary():
        """Get portfolio summary"""
        summary = data_provider.get_portfolio_summary()
        return JSONResponse(summary)
    
    @app.get("/api/market-data/{symbol}")
    async def get_market_data(symbol: str, hours: int = 24):
        """Get market data for symbol"""
        data = data_provider.get_recent_market_data(symbol.upper(), hours)
        return JSONResponse(data)
    
    @app.get("/api/ml-performance")
    async def get_ml_performance():
        """Get ML performance metrics"""
        metrics = data_provider.get_ml_performance_metrics()
        return JSONResponse(metrics)
    
    @app.get("/api/system-health")
    async def get_system_health():
        """Get system health status"""
        health = data_provider.get_system_health()
        return JSONResponse(health)
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket for real-time updates"""
        await websocket.accept()
        try:
            while True:
                # Send periodic updates
                health_data = data_provider.get_system_health()
                await websocket.send_json({
                    "type": "health_update",
                    "data": health_data
                })
                
                await asyncio.sleep(30)  # Update every 30 seconds
                
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            await websocket.close()

class SimpleDashboardGenerator:
    """Generates static HTML dashboard when FastAPI not available"""
    
    def __init__(self):
        self.data_provider = DashboardDataProvider()
        self.template_dir = Path(__file__).parent / "templates"
        self.template_dir.mkdir(exist_ok=True)
    
    def generate_dashboard_html(self) -> str:
        """Generate complete dashboard HTML"""
        # Get all data
        ml_outlook = self.data_provider.load_ml_outlook()
        portfolio_summary = self.data_provider.get_portfolio_summary()
        system_health = self.data_provider.get_system_health()
        ml_performance = self.data_provider.get_ml_performance_metrics()
        
        # Generate HTML
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EMO Options Bot Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .card h3 {{ margin-top: 0; color: #2c3e50; }}
        .status-healthy {{ color: #27ae60; }}
        .status-warning {{ color: #f39c12; }}
        .status-error {{ color: #e74c3c; }}
        .metric {{ display: flex; justify-content: space-between; margin: 10px 0; }}
        .metric-value {{ font-weight: bold; }}
        .timestamp {{ font-size: 0.9em; color: #7f8c8d; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #f8f9fa; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 EMO Options Bot Dashboard</h1>
            <p>Real-time monitoring and control for Phase 3 trading system</p>
            <p class="timestamp">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
        </div>
        
        <div class="grid">
            {self._render_system_health_card(system_health)}
            {self._render_ml_outlook_card(ml_outlook)}
            {self._render_portfolio_card(portfolio_summary)}
            {self._render_ml_performance_card(ml_performance)}
        </div>
    </div>
    
    <script>
        // Auto-refresh every 5 minutes
        setTimeout(() => location.reload(), 300000);
    </script>
</body>
</html>
        """
        
        return html
    
    def _render_system_health_card(self, health: Dict) -> str:
        """Render system health card"""
        status = health.get("overall_status", "unknown")
        status_class = f"status-{status}"
        
        components_html = ""
        for comp_name, comp_data in health.get("components", {}).items():
            comp_status = comp_data.get("status", "unknown")
            comp_class = f"status-{comp_status}"
            components_html += f"""
            <div class="metric">
                <span>{comp_name.replace('_', ' ').title()}:</span>
                <span class="{comp_class}">{comp_status.upper()}</span>
            </div>
            """
        
        return f"""
        <div class="card">
            <h3>🔧 System Health</h3>
            <div class="metric">
                <span>Overall Status:</span>
                <span class="{status_class}">{status.upper()}</span>
            </div>
            <div class="metric">
                <span>Health Score:</span>
                <span class="metric-value">{health.get('health_score', 0):.1%}</span>
            </div>
            {components_html}
        </div>
        """
    
    def _render_ml_outlook_card(self, outlook: Optional[Dict]) -> str:
        """Render ML outlook card"""
        if not outlook:
            return """
            <div class="card">
                <h3>🧠 ML Outlook</h3>
                <p class="status-warning">No ML outlook available</p>
                <p>Run: <code>python scripts/ml/enhanced_ml_outlook.py --export</code></p>
            </div>
            """
        
        models_html = ""
        for model in outlook.get("models", []):
            models_html += f"""
            <tr>
                <td>{model.get('name', 'Unknown')}</td>
                <td>{model.get('signal', 0):.3f}</td>
                <td>{model.get('conf', 0):.3f}</td>
            </tr>
            """
        
        ensemble = outlook.get("ensemble", {})
        signal = ensemble.get("signal", 0)
        signal_class = "status-healthy" if abs(signal) > 0.1 else "status-warning"
        
        return f"""
        <div class="card">
            <h3>🧠 ML Outlook</h3>
            <div class="metric">
                <span>Symbol:</span>
                <span class="metric-value">{outlook.get('symbol', 'N/A')}</span>
            </div>
            <div class="metric">
                <span>Ensemble Signal:</span>
                <span class="{signal_class} metric-value">{signal:.3f}</span>
            </div>
            <div class="metric">
                <span>Confidence:</span>
                <span class="metric-value">{ensemble.get('confidence', 0):.3f}</span>
            </div>
            <p><strong>Summary:</strong> {outlook.get('summary', 'No summary available')}</p>
            
            <h4>Model Details</h4>
            <table>
                <tr><th>Model</th><th>Signal</th><th>Confidence</th></tr>
                {models_html}
            </table>
            
            <p class="timestamp">Updated: {outlook.get('ts', 'Unknown')}</p>
        </div>
        """
    
    def _render_portfolio_card(self, portfolio: Dict) -> str:
        """Render portfolio summary card"""
        orders = portfolio.get("orders", {})
        risk = portfolio.get("risk", {})
        db = portfolio.get("database", {})
        
        return f"""
        <div class="card">
            <h3>💼 Portfolio Summary</h3>
            
            <h4>Orders (Last 7 days)</h4>
            <div class="metric">
                <span>Total Orders:</span>
                <span class="metric-value">{orders.get('total', 0)}</span>
            </div>
            <div class="metric">
                <span>Pending:</span>
                <span class="metric-value">{orders.get('pending', 0)}</span>
            </div>
            <div class="metric">
                <span>Executed:</span>
                <span class="metric-value">{orders.get('executed', 0)}</span>
            </div>
            
            <h4>Risk Management</h4>
            <div class="metric">
                <span>Violations:</span>
                <span class="metric-value">{risk.get('total_violations', 0)}</span>
            </div>
            <div class="metric">
                <span>Critical:</span>
                <span class="status-error metric-value">{risk.get('critical_violations', 0)}</span>
            </div>
            
            <h4>Database</h4>
            <div class="metric">
                <span>Status:</span>
                <span class="status-{db.get('status', 'error')}">{db.get('status', 'unknown').upper()}</span>
            </div>
            <div class="metric">
                <span>Size:</span>
                <span class="metric-value">{db.get('size_mb', 0):.1f} MB</span>
            </div>
            
            <p class="timestamp">Updated: {portfolio.get('last_updated', 'Unknown')}</p>
        </div>
        """
    
    def _render_ml_performance_card(self, performance: Dict) -> str:
        """Render ML performance card"""
        models_html = ""
        for model in performance.get("models", []):
            models_html += f"""
            <tr>
                <td>{model.get('name', 'Unknown')}</td>
                <td>{model.get('avg_confidence', 0):.3f}</td>
                <td>{model.get('prediction_count', 0)}</td>
            </tr>
            """
        
        return f"""
        <div class="card">
            <h3>📈 ML Performance</h3>
            <div class="metric">
                <span>Total Predictions:</span>
                <span class="metric-value">{performance.get('total_predictions', 0)}</span>
            </div>
            <div class="metric">
                <span>Average Confidence:</span>
                <span class="metric-value">{performance.get('avg_confidence', 0):.3f}</span>
            </div>
            
            <h4>Model Breakdown</h4>
            <table>
                <tr><th>Model</th><th>Avg Confidence</th><th>Predictions</th></tr>
                {models_html}
            </table>
        </div>
        """
    
    def save_dashboard(self, output_path: Optional[Path] = None) -> Path:
        """Save dashboard HTML to file"""
        if output_path is None:
            output_path = Path("dashboard.html")
        
        html = self.generate_dashboard_html()
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        
        logger.info(f"Dashboard saved to: {output_path}")
        return output_path

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="EMO Dashboard")
    parser.add_argument("--mode", choices=["serve", "generate"], default="serve",
                       help="Mode: serve (FastAPI) or generate (static HTML)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--output", help="Output file for static generation")
    
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
        logger.warning(f"Database initialization failed: {e}")
    
    if args.mode == "serve" and FASTAPI_AVAILABLE:
        logger.info(f"Starting dashboard server on http://{args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
        
    elif args.mode == "generate" or not FASTAPI_AVAILABLE:
        if not FASTAPI_AVAILABLE:
            logger.info("FastAPI not available, generating static dashboard")
        
        generator = SimpleDashboardGenerator()
        output_path = Path(args.output) if args.output else Path("dashboard.html")
        saved_path = generator.save_dashboard(output_path)
        
        print(f"Dashboard generated: {saved_path}")
        print(f"Open in browser: file://{saved_path.absolute()}")
        
    else:
        logger.error("Invalid mode or missing dependencies")
        sys.exit(1)

if __name__ == "__main__":
    main()