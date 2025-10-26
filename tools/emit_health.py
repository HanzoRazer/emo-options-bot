#!/usr/bin/env python3
"""
Enhanced Health Monitoring Server with Order Management
=======================================================
Provides comprehensive health endpoints and HTML order viewing for EMO Options Bot:
- /health: Basic health status
- /metrics: Detailed performance metrics with institutional integration
- /orders.html: Professional HTML order management interface
- /orders.json: Orders API endpoint
- /ready: Readiness probe for containers
- /config: Configuration health check

Features:
- Professional HTML interface with auto-refresh
- Integration with OPS database and institutional systems
- Real-time order monitoring with risk scoring
- Compliance checking and approval workflows
- Responsive design with professional styling
- JSON APIs for programmatic access
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading
import time
import os
import logging
import html
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import List, Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

try:
    from utils.enhanced_config import Config
except ImportError:
    # Fallback if enhanced_config not available
    class Config:
        def get(self, key: str, default: str = None) -> str:
            return os.getenv(key, default)
        def as_int(self, key: str, default: int = 0) -> int:
            try:
                return int(self.get(key, str(default)))
            except (ValueError, TypeError):
                return default

# Lightweight import for trading session helper
try:
    from src.database.trading_session import quick_health_check
    from src.database.read_paths import fetch_positions, fetch_recent_orders
    _TRADING_DB_READY = True
except Exception:
    _TRADING_DB_READY = False

# Setup robust logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Enhanced global state management with thread safety
_state_lock = threading.Lock()
_state = {
    "status": "initializing",
    "cycle": 0,
    "metrics": {},
    "start_time": time.time(),
    "last_update": None,
    "request_count": 0,
    "errors": []
}

def snapshot(perf, latest_files=None):
    """Update global state with performance metrics (thread-safe)."""
    try:
        with _state_lock:
            _state["status"] = "healthy"
            _state["cycle"] = len(perf.get("cycle_times", []))
            _state["metrics"] = perf.copy()
            _state["last_update"] = datetime.now().isoformat()
            if latest_files:
                _state["latest"] = latest_files
            # Attach quick DB health if available
            if _TRADING_DB_READY:
                _state["trading_db"] = quick_health_check()
            else:
                _state["trading_db"] = {"db": "unavailable"}
            logger.debug(f"State updated: cycle {_state['cycle']}")
    except Exception as e:
        logger.error(f"❌ Failed to update state: {e}")
        with _state_lock:
            _state["errors"].append({"timestamp": datetime.now().isoformat(), "error": str(e)})

def _query_recent_orders(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Enhanced DB query for recent staged orders with institutional integration.
    Returns list of order dictionaries with enhanced metadata.
    """
    try:
        from ops.db.session import get_session, init_db
        from ops.staging.models import StagedOrder
    except Exception as e:
        logger.debug(f"OPS database not available: {e}")
        return []
    
    try:
        init_db()
        with get_session() as session:
            rows = (
                session.query(StagedOrder)  # type: ignore
                .order_by(StagedOrder.created_at.desc())  # type: ignore
                .limit(limit)
                .all()
            )
            
            # Convert to enhanced dictionaries
            orders = []
            for row in rows:
                order_dict = row.as_dict()
                
                # Add computed fields for display
                order_dict["risk_level"] = _get_risk_level(order_dict.get("risk_score"))
                order_dict["compliance_status"] = "✅ Pass" if not order_dict.get("compliance_flags") else "⚠️ Issues"
                order_dict["approval_status"] = _get_approval_status(order_dict)
                order_dict["age_hours"] = _calculate_age_hours(order_dict.get("created_at"))
                
                orders.append(order_dict)
            
            logger.debug(f"Retrieved {len(orders)} orders from database")
            return orders
            
    except Exception as e:
        logger.error(f"Failed to query orders: {e}")
        return []

def _get_risk_level(risk_score: Optional[float]) -> str:
    """Get risk level display string."""
    if not risk_score:
        return "❓ Unknown"
    
    if risk_score >= 75:
        return "🔴 High"
    elif risk_score >= 50:
        return "🟡 Medium"
    elif risk_score >= 25:
        return "🟢 Low"
    else:
        return "🟢 Minimal"

def _get_approval_status(order: Dict[str, Any]) -> str:
    """Get approval status display string."""
    if order.get("approved_at"):
        return f"✅ Approved ({order.get('approved_by', 'Unknown')})"
    elif order.get("approval_required"):
        return "🔒 Pending Approval"
    else:
        return "🚀 Ready"

def _calculate_age_hours(created_at: Optional[str]) -> str:
    """Calculate and format order age."""
    if not created_at:
        return "Unknown"
    
    try:
        created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        age = datetime.now(timezone.utc) - created
        hours = age.total_seconds() / 3600
        
        if hours < 1:
            return f"{int(age.total_seconds() / 60)}m"
        elif hours < 24:
            return f"{hours:.1f}h"
        else:
            return f"{hours / 24:.1f}d"
    except Exception:
        return "Unknown"

def _get_institutional_status() -> Dict[str, Any]:
    """Get institutional system status for health monitoring."""
    try:
        from database.institutional_integration import InstitutionalIntegration
        integration = InstitutionalIntegration()
        status = integration.check_system_health()
        
        return {
            "available": True,
            "health_score": status.system_health_score,
            "database_healthy": status.database_healthy,
            "environment": status.environment,
            "total_orders": status.total_orders,
            "active_orders": status.active_orders,
            "migration_status": status.migration_status
        }
    except Exception as e:
        logger.debug(f"Institutional integration not available: {e}")
        return {"available": False, "error": str(e)}

def _render_orders_html(rows: List[Dict[str, Any]]) -> bytes:
    """
    Render enhanced orders HTML page with professional styling and institutional features.
    """
    def esc(x): 
        return html.escape(str(x) if x is not None else "")
    
    institutional_status = _get_institutional_status()
    
    # Enhanced CSS styling
    css = """
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        margin: 0;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    .container {
        max-width: 1400px;
        margin: 0 auto;
        background: white;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        overflow: hidden;
    }
    .header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px;
        text-align: center;
    }
    .header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 300;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .status-bar {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        padding: 20px 30px;
        background: #f8f9fa;
        border-bottom: 1px solid #dee2e6;
    }
    .status-item {
        text-align: center;
        padding: 10px;
    }
    .status-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #667eea;
    }
    .status-label {
        font-size: 0.9rem;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .table-container {
        padding: 30px;
        overflow-x: auto;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
        background: white;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    th {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px 12px;
        text-align: left;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.8rem;
    }
    td {
        padding: 12px;
        border-bottom: 1px solid #eee;
        vertical-align: middle;
    }
    tr:hover {
        background-color: #f8f9fa;
    }
    .risk-high { color: #dc3545; }
    .risk-medium { color: #ffc107; }
    .risk-low { color: #28a745; }
    .status-staged { background: #cce7ff; color: #004085; }
    .status-reviewed { background: #fff3cd; color: #856404; }
    .status-approved { background: #d4edda; color: #155724; }
    .status-rejected { background: #f8d7da; color: #721c24; }
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .footer {
        background: #f8f9fa;
        padding: 20px 30px;
        text-align: center;
        color: #6c757d;
        border-top: 1px solid #dee2e6;
    }
    .nav-links {
        margin-top: 10px;
    }
    .nav-links a {
        color: #667eea;
        text-decoration: none;
        margin: 0 10px;
        font-weight: 500;
    }
    .nav-links a:hover {
        text-decoration: underline;
    }
    .refresh-info {
        opacity: 0.8;
        font-size: 0.9rem;
        margin-top: 10px;
    }
    """
    
    out = []
    out.append("<!DOCTYPE html>")
    out.append("<html lang='en'>")
    out.append("<head>")
    out.append("<meta charset='utf-8'>")
    out.append("<meta name='viewport' content='width=device-width, initial-scale=1.0'>")
    out.append("<title>EMO Options Bot - Order Management</title>")
    out.append(f"<style>{css}</style>")
    out.append("<script>")
    out.append("setTimeout(() => window.location.reload(), 30000);")  # Auto-refresh every 30 seconds
    out.append("</script>")
    out.append("</head>")
    out.append("<body>")
    
    out.append("<div class='container'>")
    out.append("<div class='header'>")
    out.append("<h1>📊 EMO Options Bot</h1>")
    out.append("<p>Order Management & Health Monitoring</p>")
    out.append("</div>")
    
    # Status bar
    out.append("<div class='status-bar'>")
    
    out.append("<div class='status-item'>")
    out.append(f"<div class='status-value'>{len(rows)}</div>")
    out.append("<div class='status-label'>Total Orders</div>")
    out.append("</div>")
    
    pending_count = len([r for r in rows if r.get("approval_required")])
    out.append("<div class='status-item'>")
    out.append(f"<div class='status-value'>{pending_count}</div>")
    out.append("<div class='status-label'>Pending Approval</div>")
    out.append("</div>")
    
    if institutional_status.get("available"):
        out.append("<div class='status-item'>")
        out.append(f"<div class='status-value'>{institutional_status.get('health_score', 0):.0f}%</div>")
        out.append("<div class='status-label'>System Health</div>")
        out.append("</div>")
        
        out.append("<div class='status-item'>")
        out.append(f"<div class='status-value'>{esc(institutional_status.get('environment', 'Unknown'))}</div>")
        out.append("<div class='status-label'>Environment</div>")
        out.append("</div>")
    
    out.append("</div>")
    
    # Orders table
    out.append("<div class='table-container'>")
    out.append("<h2>📋 Recent Staged Orders</h2>")
    out.append(f"<p>Last updated: {esc(datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'))}</p>")
    
    if rows:
        out.append("<table>")
        out.append("<thead><tr>")
        
        columns = [
            ("ID", "id"),
            ("Symbol", "symbol"),
            ("Side", "side"),
            ("Qty", "qty"),
            ("Type", "order_type"),
            ("Strategy", "strategy"),
            ("Risk", "risk_level"),
            ("Compliance", "compliance_status"),
            ("Approval", "approval_status"),
            ("Age", "age_hours"),
            ("Status", "status"),
            ("User", "user")
        ]
        
        for col_name, _ in columns:
            out.append(f"<th>{esc(col_name)}</th>")
        
        out.append("</tr></thead>")
        out.append("<tbody>")
        
        for row in rows:
            status_class = f"status-{row.get('status', 'unknown').lower()}"
            out.append(f"<tr class='{status_class}'>")
            
            for _, col_key in columns:
                value = row.get(col_key, "")
                
                # Special formatting
                if col_key == "qty" and value:
                    value = f"{int(value):,}"
                elif col_key == "status":
                    value = f"<span class='badge status-{str(value).lower()}'>{esc(value)}</span>"
                elif col_key in ("risk_level", "compliance_status", "approval_status"):
                    value = str(value)  # These already have emojis
                else:
                    value = esc(value)
                
                out.append(f"<td>{value}</td>")
            
            out.append("</tr>")
        
        out.append("</tbody>")
        out.append("</table>")
    else:
        out.append("<p>No staged orders found.</p>")
    
    out.append("</div>")
    
    # Footer
    out.append("<div class='footer'>")
    out.append("<p><strong>EMO Options Bot</strong> - Enhanced Order Management System</p>")
    out.append("<div class='nav-links'>")
    out.append("<a href='/health'>🏥 Health Status</a>")
    out.append("<a href='/metrics'>📊 Metrics</a>")
    out.append("<a href='/orders.html'>📋 Orders</a>")
    if institutional_status.get("available"):
        out.append("<a href='http://localhost:8082/institutional'>🏛️ Institutional Dashboard</a>")
    out.append("</div>")
    out.append("<div class='refresh-info'>")
    out.append("🔄 Auto-refresh every 30 seconds")
    out.append("</div>")
    out.append("</div>")
    
    out.append("</div>")
    out.append("</body>")
    out.append("</html>")
    
    return "".join(out).encode()

def get_system_metrics():
    """Collect enhanced system metrics."""
    try:
        import psutil
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent,
            "process_count": len(psutil.pids())
        }
    except ImportError:
        logger.warning("psutil not available, system metrics disabled")
        return {"note": "psutil not installed"}
    except Exception as e:
        logger.error(f"❌ System metrics error: {e}")
        return {"error": str(e)}

class EnhancedHealthHandler(BaseHTTPRequestHandler):
    """Enhanced HTTP request handler with comprehensive health endpoints and order management."""
    
    def log_message(self, format, *args):
        """Override to use Python logging instead of stderr."""
        logger.info(f"{self.client_address[0]} - {format % args}")
    
    def _send_json(self, code: int, obj: dict):
        """Send JSON response with proper headers and error handling."""
        try:
            # Add common response headers
            obj["timestamp"] = datetime.now().isoformat()
            obj["server"] = "EMO Health Monitor"
            
            json_str = json.dumps(obj, default=str, indent=2)
            response_bytes = json_str.encode('utf-8')
            
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response_bytes)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(response_bytes)
            
            # Update request counter
            with _state_lock:
                _state["request_count"] += 1
                
        except Exception as e:
            logger.error(f"❌ Error sending JSON response: {e}")
            self.send_error(500, f"JSON encoding error: {e}")
    
    def _send_html(self, code: int, body_bytes: bytes):
        """Send HTML response."""
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body_bytes)
        
        # Update request counter
        with _state_lock:
            _state["request_count"] += 1
    
    def _get_health_data(self):
        """Get basic health status with institutional integration."""
        with _state_lock:
            uptime = time.time() - _state["start_time"]
            health_data = {
                "status": _state["status"],
                "uptime_seconds": round(uptime, 2),
                "cycle": _state["cycle"],
                "last_update": _state["last_update"],
                "request_count": _state["request_count"]
            }
        
        # Add institutional status if available
        inst_status = _get_institutional_status()
        if inst_status.get("available"):
            health_data["institutional"] = inst_status
        
        return health_data
    
    def _get_metrics_data(self):
        """Get comprehensive metrics including file-based metrics and institutional data."""
        try:
            metrics_file = Path("data/metrics.json")
            file_metrics = {}
            
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    file_metrics = json.load(f)
                    logger.debug(f"Loaded file metrics: {len(file_metrics)} entries")
            
            with _state_lock:
                combined_metrics = {
                    "system": get_system_metrics(),
                    "application": _state["metrics"].copy(),
                    "file_based": file_metrics,
                    "uptime_seconds": time.time() - _state["start_time"],
                    "error_count": len(_state["errors"]),
                    "recent_errors": _state["errors"][-5:] if _state["errors"] else []
                }
            
            # Add OPS database metrics
            try:
                from ops.db.session import get_database_info
                combined_metrics["ops_database"] = get_database_info()
            except Exception as e:
                combined_metrics["ops_database"] = {"error": str(e)}
            
            # Add institutional metrics
            inst_status = _get_institutional_status()
            combined_metrics["institutional"] = inst_status
            
            return combined_metrics
            
        except Exception as e:
            logger.error(f"❌ Error collecting metrics: {e}")
            return {"error": str(e), "basic_metrics": _state["metrics"]}
    
    def _get_readiness_data(self):
        """Get readiness probe data for container orchestration."""
        try:
            # Check if essential components are ready
            config = Config()
            
            ready = True
            checks = {}
            
            # Configuration check
            try:
                if hasattr(config, 'health_check'):
                    health = config.health_check()
                    checks["config"] = len(health.get("validation_errors", {})) == 0
                else:
                    checks["config"] = True
            except Exception as e:
                checks["config"] = False
                logger.warning(f"Config health check failed: {e}")
            
            # Database connectivity check (if database module available)
            try:
                sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
                from database.db_router import get_engine
                engine = get_engine(config)
                checks["database"] = engine is not None
            except Exception as e:
                checks["database"] = False
                logger.warning(f"Database check failed: {e}")
            
            # OPS database check
            try:
                from ops.db.session import test_connection
                checks["ops_database"] = test_connection()
            except Exception as e:
                checks["ops_database"] = False
                logger.warning(f"OPS database check failed: {e}")
            
            ready = all(checks.values())
            
            return {
                "ready": ready,
                "checks": checks,
                "status": "ready" if ready else "not_ready"
            }
            
        except Exception as e:
            logger.error(f"❌ Readiness check failed: {e}")
            return {"ready": False, "error": str(e)}
    
    def _get_config_data(self):
        """Get configuration health information."""
        try:
            config = Config()
            
            if hasattr(config, 'health_check'):
                return config.health_check()
            else:
                # Basic config info if health_check not available
                return {
                    "environment": config.get("EMO_ENV", "unknown"),
                    "note": "Basic config - health_check not available"
                }
        except Exception as e:
            logger.error(f"❌ Config health check failed: {e}")
            return {"error": str(e)}

    def do_GET(self):
        """Handle GET requests for various health endpoints and order management."""
        try:
            if self.path.startswith("/health"):
                self._send_json(200, self._get_health_data())
                
            elif self.path.startswith("/metrics"):
                self._send_json(200, self._get_metrics_data())
                
            elif self.path.startswith("/orders.html") or self.path == "/":
                # Enhanced orders HTML page
                orders = _query_recent_orders(limit=100)
                html_content = _render_orders_html(orders)
                self._send_html(200, html_content)
                
            elif self.path.startswith("/orders.json"):
                # Orders JSON API (enhanced with trading DB if available)
                if _TRADING_DB_READY:
                    trading_orders = fetch_recent_orders(limit=100)
                    ops_orders = _query_recent_orders(limit=100)
                    self._send_json(200, {
                        "trading_orders": trading_orders,
                        "ops_orders": ops_orders,
                        "trading_count": len(trading_orders),
                        "ops_count": len(ops_orders)
                    })
                else:
                    orders = _query_recent_orders(limit=100)
                    self._send_json(200, {"orders": orders, "count": len(orders)})
                
            elif self.path.startswith("/positions.json"):
                # New positions JSON endpoint
                if not _TRADING_DB_READY:
                    self._send_json(503, {"error": "Trading DB layer unavailable"})
                    return
                positions = fetch_positions(limit=200)
                self._send_json(200, {"positions": positions, "count": len(positions)})
                
            elif self.path.startswith("/orders"):
                # Simple HTML view for trading orders
                if not _TRADING_DB_READY:
                    html_content = b"""<!doctype html><html><head>
<meta charset="utf-8"><title>EMO Orders</title>
<style>body { font:14px system-ui,-apple-system,Segoe UI,Arial,sans-serif; margin:20px }</style>
</head><body><h1>EMO Orders</h1><p>Trading DB unavailable</p></body></html>"""
                    self._send_html(503, html_content)
                    return
                
                orders = fetch_recent_orders(limit=100)
                rows = []
                for r in orders:
                    rows.append(f"<tr><td>{r.get('id','')}</td><td>{r.get('symbol','')}</td>"
                                f"<td>{r.get('side','')}</td><td>{r.get('type','')}</td>"
                                f"<td>{r.get('qty','')}</td><td>{r.get('status','')}</td>"
                                f"<td>{r.get('ts','')}</td></tr>")
                
                html_content = f"""<!doctype html><html><head>
<meta charset="utf-8"><title>EMO Orders</title>
<style>
 body {{ font:14px system-ui,-apple-system,Segoe UI,Arial,sans-serif; margin:20px }}
 table {{ border-collapse:collapse; width:100% }}
 th,td {{ border:1px solid #dde; padding:6px 8px; text-align:left; font-variant-numeric:tabular-nums }}
 th {{ background:#f7f9fc }}
 .meta {{ color:#666; margin: 0 0 14px 0 }}
</style>
</head><body>
<h1>EMO Orders</h1>
<div class="meta">/orders (latest)</div>
<table><thead><tr><th>ID</th><th>Symbol</th><th>Side</th>
<th>Type</th><th>Qty</th><th>Status</th><th>Time</th></tr></thead><tbody>
{chr(10).join(rows)}
</tbody></table>
</body></html>""".encode('utf-8')
                self._send_html(200, html_content)
                
            elif self.path.startswith("/ready"):
                readiness = self._get_readiness_data()
                status_code = 200 if readiness.get("ready", False) else 503
                self._send_json(status_code, readiness)
                
            elif self.path.startswith("/config"):
                self._send_json(200, self._get_config_data())
                
            elif self.path.startswith("/performance"):
                # Performance monitoring endpoint
                try:
                    from src.monitoring.performance import get_performance_summary, get_performance_alerts
                    perf_data = {
                        "summary": get_performance_summary(),
                        "alerts": get_performance_alerts(),
                        "status": "monitoring"
                    }
                    self._send_json(200, perf_data)
                except ImportError:
                    self._send_json(503, {"error": "Performance monitoring not available"})
                except Exception as e:
                    self._send_json(500, {"error": f"Performance monitoring error: {e}"})
            
            elif self.path == "/analytics":
                # Analytics endpoint
                if not _TRADING_DB_READY:
                    self._send_json(503, {"error": "Trading database not available"})
                    return
                
                try:
                    from src.analytics.trading_analytics import get_analytics_engine
                    engine = get_analytics_engine()
                    
                    # Get comprehensive analytics
                    portfolio_metrics = engine.get_portfolio_analytics()
                    risk_metrics = engine.get_risk_assessment()
                    execution_analytics = engine.get_execution_analytics(days=7)
                    performance_attribution = engine.get_performance_attribution(days=30)
                    
                    analytics_data = {
                        "portfolio": {
                            "total_value": portfolio_metrics.total_value,
                            "total_pnl": portfolio_metrics.total_pnl,
                            "return_pct": portfolio_metrics.return_pct,
                            "positions_count": portfolio_metrics.positions_count,
                            "win_rate": portfolio_metrics.win_rate,
                            "profit_factor": portfolio_metrics.profit_factor,
                            "sharpe_ratio": portfolio_metrics.sharpe_ratio,
                            "max_drawdown": portfolio_metrics.max_drawdown,
                            "greek_exposure": {
                                "delta": portfolio_metrics.total_delta,
                                "gamma": portfolio_metrics.total_gamma,
                                "theta": portfolio_metrics.total_theta,
                                "vega": portfolio_metrics.total_vega
                            }
                        },
                        "risk": {
                            "risk_score": risk_metrics.risk_score,
                            "concentration_risk": risk_metrics.concentration_risk,
                            "market_exposure": risk_metrics.market_exposure,
                            "sector_exposure": risk_metrics.sector_exposure,
                            "warnings": risk_metrics.warnings
                        },
                        "execution": [
                            {
                                "symbol": trade.symbol,
                                "side": trade.side,
                                "quantity": trade.quantity,
                                "execution_quality": trade.execution_quality,
                                "slippage_bps": trade.slippage_bps,
                                "timing_score": trade.timing_score
                            }
                            for trade in execution_analytics[-20:]  # Last 20 trades
                        ],
                        "attribution": performance_attribution
                    }
                    
                    self._send_json(200, analytics_data)
                    
                except ImportError:
                    self._send_json(503, {"error": "Analytics module not available"})
                except Exception as e:
                    self._send_json(500, {"error": f"Analytics error: {e}"})
            
            elif self.path == "/risk":
                # Risk dashboard endpoint
                if not _TRADING_DB_READY:
                    self._send_json(503, {"error": "Trading database not available"})
                    return
                
                try:
                    from src.analytics.trading_analytics import get_risk_dashboard
                    risk_data = get_risk_dashboard()
                    self._send_json(200, risk_data)
                    
                except ImportError:
                    self._send_json(503, {"error": "Risk analytics module not available"})
                except Exception as e:
                    self._send_json(500, {"error": f"Risk analysis error: {e}"})
                
            else:
                # Default endpoint with available routes
                endpoints = ["/health", "/metrics", "/orders.html", "/orders.json", "/ready", "/config", "/performance"]
                if _TRADING_DB_READY:
                    endpoints.extend(["/positions.json", "/orders", "/analytics", "/risk"])
                
                # Add analytics data if available
                analytics_data = {}
                if _TRADING_DB_READY:
                    try:
                        from src.database.advanced_read_paths import get_query_performance_stats
                        from src.analytics.trading_analytics import get_portfolio_summary, get_risk_dashboard
                        
                        analytics_data['query_performance'] = get_query_performance_stats()
                        analytics_data['portfolio_summary'] = get_portfolio_summary()
                        analytics_data['risk_dashboard'] = get_risk_dashboard()
                        
                    except ImportError as e:
                        analytics_data['error'] = f"Analytics modules not available: {e}"
                
                self._send_json(200, {
                    "service": "EMO Health Monitor",
                    "endpoints": endpoints,
                    "trading_db_available": _TRADING_DB_READY,
                    "uptime_seconds": time.time() - _state["start_time"],
                    "analytics": analytics_data
                })
                
        except Exception as e:
            logger.error(f"❌ Request handling error: {e}")
            self._send_json(500, {"error": str(e)})

def serve_health_monitor(host="0.0.0.0", port=8082):
    """Start the enhanced health monitoring server with robust error handling."""
    try:
        logger.info(f"🏥 Starting Enhanced Health Monitor on {host}:{port}")
        
        server = HTTPServer((host, port), EnhancedHealthHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        # Update state to indicate server is running
        with _state_lock:
            _state["status"] = "running"
            _state["server_host"] = host
            _state["server_port"] = port
        
        logger.info(f"✅ Health Monitor started successfully")
        logger.info(f"   Health: http://{host}:{port}/health")
        logger.info(f"   Metrics: http://{host}:{port}/metrics")
        logger.info(f"   Orders: http://{host}:{port}/orders.html")
        logger.info(f"   Ready: http://{host}:{port}/ready")
        logger.info(f"   Config: http://{host}:{port}/config")
        
        return server_thread, server
        
    except Exception as e:
        logger.error(f"❌ Failed to start health monitor: {e}")
        with _state_lock:
            _state["status"] = "error"
            _state["errors"].append({
                "timestamp": datetime.now().isoformat(),
                "error": f"Server start failed: {e}"
            })
        raise

def serve(port=8082):
    """Legacy compatibility function."""
    thread, _ = serve_health_monitor(port=port)
    return thread

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="EMO Enhanced Health Monitor")
    parser.add_argument("--port", type=int, default=8082, help="Server port (default: 8082)")
    parser.add_argument("--host", default="0.0.0.0", help="Server host (default: 0.0.0.0)")
    parser.add_argument("--config-test", action="store_true", help="Test configuration and exit")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon (no keyboard interrupt handling)")
    
    args = parser.parse_args()
    
    # Configuration and port handling
    try:
        cfg = Config()
        
        # Allow config override of port
        config_port = cfg.as_int("HEALTH_SERVER_PORT", args.port)
        final_port = config_port if config_port > 0 else args.port
        
        if args.config_test:
            print("🔧 Testing configuration...")
            if hasattr(cfg, 'health_check'):
                health = cfg.health_check()
                print("Configuration Health:")
                print(json.dumps(health, indent=2))
                if health.get("validation_errors"):
                    print("❌ Configuration has validation errors")
                    exit(1)
                else:
                    print("✅ Configuration is healthy")
            else:
                print("ℹ️ Basic configuration test passed")
            exit(0)
        
        # Start the server
        logger.info(f"🚀 EMO Health Monitor starting...")
        thread, server = serve_health_monitor(host=args.host, port=final_port)
        
        if args.daemon:
            logger.info("🔄 Running in daemon mode")
            thread.join()
        else:
            try:
                logger.info("⌨️ Press Ctrl+C to stop the server")
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("\n🛑 Stopping Health Monitor...")
                server.shutdown()
                logger.info("✅ Health Monitor stopped")
                
    except Exception as e:
        logger.error(f"❌ Health Monitor failed: {e}")
        exit(1)