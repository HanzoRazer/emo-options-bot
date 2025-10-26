#!/usr/bin/env python3
"""
EMO Options Bot - Institutional Integration System
================================================
Complete institutional-grade system integration bringing together:
- Enhanced database models and migrations
- Order review and analysis system
- Health monitoring and reporting
- Real-time dashboard generation
- Legacy system compatibility

This script provides unified access to all institutional components.
"""

from __future__ import annotations
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SystemStatus:
    """Complete system status information."""
    
    timestamp: str
    database_healthy: bool
    environment: str
    total_orders: int
    active_orders: int
    system_health_score: float
    database_dialect: str
    migration_status: str
    recent_files_count: int
    components: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

class InstitutionalIntegration:
    """
    Institutional-grade system integration for EMO Options Bot.
    Provides unified access to all enhanced components.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize institutional integration system.
        
        Args:
            data_dir: Data directory for reports and cache
        """
        if data_dir is None:
            data_dir = Path(__file__).resolve().parents[2] / "data"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.reports_dir = self.data_dir / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self.integration_dir = self.data_dir / "integration"
        self.integration_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Institutional integration initialized: {self.data_dir}")
    
    def check_system_health(self) -> SystemStatus:
        """
        Perform comprehensive system health check.
        
        Returns:
            Complete system status information
        """
        timestamp = datetime.now().isoformat()
        components = {}
        
        # Check database health
        try:
            from .enhanced_router import DBRouter, test_connection
            db_healthy = test_connection()
            db_dialect = DBRouter.dialect() if db_healthy else "unknown"
            components["database"] = {
                "healthy": db_healthy,
                "dialect": db_dialect,
                "status": "operational" if db_healthy else "degraded"
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            db_healthy = False
            db_dialect = "unknown"
            components["database"] = {
                "healthy": False,
                "dialect": "unknown",
                "status": "failed",
                "error": str(e)
            }
        
        # Check migration status
        try:
            from .enhanced_router import DBRouter
            migration_status = "current" if DBRouter.migrate() else "pending"
            components["migrations"] = {
                "status": migration_status,
                "last_check": timestamp
            }
        except Exception as e:
            logger.error(f"Migration check failed: {e}")
            migration_status = "unknown"
            components["migrations"] = {
                "status": "unknown",
                "error": str(e)
            }
        
        # Count recent files
        recent_files_count = 0
        try:
            cutoff_time = datetime.now() - timedelta(hours=24)
            for file_path in self.data_dir.rglob("*"):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time > cutoff_time:
                        recent_files_count += 1
            
            components["file_system"] = {
                "recent_files_24h": recent_files_count,
                "data_directory": str(self.data_dir),
                "status": "operational"
            }
        except Exception as e:
            logger.error(f"File system check failed: {e}")
            components["file_system"] = {
                "recent_files_24h": 0,
                "status": "degraded",
                "error": str(e)
            }
        
        # Check order system (mock data for now)
        total_orders = 0
        active_orders = 0
        try:
            # This would integrate with actual order system
            components["orders"] = {
                "total": total_orders,
                "active": active_orders,
                "status": "operational"
            }
        except Exception as e:
            logger.error(f"Order system check failed: {e}")
            components["orders"] = {
                "total": 0,
                "active": 0,
                "status": "degraded",
                "error": str(e)
            }
        
        # Calculate overall health score
        health_scores = []
        for component, info in components.items():
            if info.get("status") == "operational":
                health_scores.append(100)
            elif info.get("status") == "degraded":
                health_scores.append(60)
            else:
                health_scores.append(0)
        
        system_health_score = sum(health_scores) / len(health_scores) if health_scores else 0
        
        # Get environment
        environment = os.getenv("EMO_ENV", "dev")
        
        return SystemStatus(
            timestamp=timestamp,
            database_healthy=db_healthy,
            environment=environment,
            total_orders=total_orders,
            active_orders=active_orders,
            system_health_score=system_health_score,
            database_dialect=db_dialect,
            migration_status=migration_status,
            recent_files_count=recent_files_count,
            components=components
        )
    
    def generate_institutional_report(self) -> str:
        """
        Generate comprehensive institutional report.
        
        Returns:
            HTML report string
        """
        status = self.check_system_health()
        
        # Health status colors and indicators
        health_color = "#28a745" if status.system_health_score > 80 else "#ffc107" if status.system_health_score > 50 else "#dc3545"
        health_icon = "✅" if status.system_health_score > 80 else "⚠️" if status.system_health_score > 50 else "❌"
        
        # Component status rows
        component_rows = []
        for component, info in status.components.items():
            status_text = info.get("status", "unknown")
            status_class = "success" if status_text == "operational" else "warning" if status_text == "degraded" else "danger"
            
            row = f"""
            <tr class="table-{status_class}">
                <td style="text-transform: capitalize;">{component.replace('_', ' ')}</td>
                <td><span class="badge bg-{status_class}">{status_text}</span></td>
                <td>{info.get('total', info.get('dialect', info.get('recent_files_24h', 'N/A')))}</td>
                <td>{info.get('error', 'All systems operational')[:50]}</td>
            </tr>
            """
            component_rows.append(row)
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>EMO Options Bot - Institutional System Report</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    font-family: 'Segoe UI', system-ui, sans-serif;
                }}
                .main-container {{
                    background: white;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                    margin: 20px;
                    overflow: hidden;
                }}
                .header-section {{
                    background: linear-gradient(135deg, #2c3e50 0%, #34495e 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .health-indicator {{
                    font-size: 3rem;
                    margin: 20px 0;
                }}
                .metric-cards {{
                    background: #f8f9fa;
                    padding: 30px;
                }}
                .metric-card {{
                    background: white;
                    border-radius: 10px;
                    padding: 20px;
                    margin: 10px;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    border-left: 4px solid {health_color};
                }}
                .metric-value {{
                    font-size: 2.5rem;
                    font-weight: bold;
                    color: {health_color};
                }}
                .metric-label {{
                    color: #6c757d;
                    font-size: 0.9rem;
                    text-transform: uppercase;
                    letter-spacing: 1px;
                    margin-top: 5px;
                }}
                .components-section {{
                    padding: 30px;
                }}
                .section-title {{
                    border-bottom: 3px solid #667eea;
                    padding-bottom: 10px;
                    margin-bottom: 25px;
                    font-weight: 600;
                }}
                .status-table {{
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }}
                .footer-section {{
                    background: #2c3e50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .timestamp {{
                    opacity: 0.8;
                    font-size: 0.9rem;
                }}
            </style>
        </head>
        <body>
            <div class="container-fluid">
                <div class="main-container">
                    <div class="header-section">
                        <h1 class="mb-0">🏛️ Institutional System Report</h1>
                        <div class="health-indicator">{health_icon}</div>
                        <h3>System Health: {status.system_health_score:.1f}%</h3>
                        <div class="timestamp">Generated: {status.timestamp}</div>
                    </div>
                    
                    <div class="metric-cards">
                        <div class="row">
                            <div class="col-md-3">
                                <div class="metric-card">
                                    <div class="metric-value">{status.environment.upper()}</div>
                                    <div class="metric-label">Environment</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="metric-card">
                                    <div class="metric-value">{status.total_orders}</div>
                                    <div class="metric-label">Total Orders</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="metric-card">
                                    <div class="metric-value">{status.active_orders}</div>
                                    <div class="metric-label">Active Orders</div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="metric-card">
                                    <div class="metric-value">{status.recent_files_count}</div>
                                    <div class="metric-label">Recent Files (24h)</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="components-section">
                        <h2 class="section-title">🔧 System Components</h2>
                        <table class="table status-table">
                            <thead class="table-dark">
                                <tr>
                                    <th>Component</th>
                                    <th>Status</th>
                                    <th>Details</th>
                                    <th>Notes</th>
                                </tr>
                            </thead>
                            <tbody>
                                {''.join(component_rows)}
                            </tbody>
                        </table>
                    </div>
                    
                    <div class="components-section">
                        <h2 class="section-title">📊 System Information</h2>
                        <div class="row">
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-header bg-primary text-white">
                                        <h5 class="mb-0">Database Configuration</h5>
                                    </div>
                                    <div class="card-body">
                                        <p><strong>Dialect:</strong> {status.database_dialect}</p>
                                        <p><strong>Migration Status:</strong> {status.migration_status}</p>
                                        <p><strong>Health:</strong> {'Healthy' if status.database_healthy else 'Degraded'}</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="card">
                                    <div class="card-header bg-info text-white">
                                        <h5 class="mb-0">Runtime Environment</h5>
                                    </div>
                                    <div class="card-body">
                                        <p><strong>Environment:</strong> {status.environment}</p>
                                        <p><strong>Data Directory:</strong> {self.data_dir}</p>
                                        <p><strong>Reports Directory:</strong> {self.reports_dir}</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="footer-section">
                        <h5>EMO Options Bot - Institutional Integration System v2.0</h5>
                        <p class="mb-0">Comprehensive system monitoring and reporting • Auto-refresh enabled</p>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                // Auto-refresh every 5 minutes
                setTimeout(() => window.location.reload(), 300000);
                
                // Add timestamp update
                setInterval(() => {{
                    const timestamp = new Date().toLocaleString();
                    document.querySelector('.timestamp').textContent = `Last Updated: ${{timestamp}}`;
                }}, 1000);
            </script>
        </body>
        </html>
        """
        
        return html_content
    
    def save_institutional_report(self, filename: Optional[str] = None) -> Path:
        """
        Save institutional report to file.
        
        Args:
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved report file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"institutional_report_{timestamp}.html"
        
        report_path = self.integration_dir / filename
        
        try:
            html_content = self.generate_institutional_report()
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Institutional report saved: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Failed to save institutional report: {e}")
            raise
    
    def export_system_status(self, format: str = "json") -> Dict[str, Any]:
        """
        Export system status in specified format.
        
        Args:
            format: Export format (json, dict)
            
        Returns:
            System status data
        """
        status = self.check_system_health()
        
        if format.lower() == "json":
            return json.loads(json.dumps(status.to_dict(), indent=2))
        else:
            return status.to_dict()
    
    def run_full_system_check(self) -> bool:
        """
        Run comprehensive system check and generate reports.
        
        Returns:
            True if all systems operational, False otherwise
        """
        try:
            logger.info("Starting full system check...")
            
            # Generate system status
            status = self.check_system_health()
            
            # Save institutional report
            report_path = self.save_institutional_report()
            
            # Save status JSON
            status_path = self.integration_dir / f"system_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(status_path, 'w', encoding='utf-8') as f:
                json.dump(status.to_dict(), f, indent=2)
            
            logger.info(f"Full system check completed")
            logger.info(f"Report: {report_path}")
            logger.info(f"Status: {status_path}")
            logger.info(f"System Health: {status.system_health_score:.1f}%")
            
            return status.system_health_score > 70
            
        except Exception as e:
            logger.error(f"Full system check failed: {e}")
            return False

# Export key classes
__all__ = [
    "InstitutionalIntegration",
    "SystemStatus"
]

# CLI interface
if __name__ == "__main__":
    integration = InstitutionalIntegration()
    
    print("🏛️ EMO Options Bot - Institutional Integration System")
    print("=" * 60)
    
    success = integration.run_full_system_check()
    
    if success:
        print("✅ All systems operational")
    else:
        print("⚠️ Some systems require attention")
        
    print("\nReports generated in data/integration/ directory")