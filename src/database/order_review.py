#!/usr/bin/env python3
"""
EMO Options Bot - Enhanced Order Review System
==============================================
Institutional-grade order review and analysis system supporting:
- Comprehensive order analysis and validation
- HTML report generation with detailed metrics
- Risk assessment and compliance checking
- Performance analysis and optimization suggestions
- Integration with enhanced database models
- Real-time monitoring and alerting

Features:
- Order validation and risk analysis
- HTML dashboard generation
- Performance metrics calculation
- Compliance checking
- Integration with database models
- Real-time updates and monitoring
"""

from __future__ import annotations
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from decimal import Decimal

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class OrderReviewMetrics:
    """Comprehensive order review metrics."""
    
    total_orders: int = 0
    active_orders: int = 0
    pending_orders: int = 0
    executed_orders: int = 0
    cancelled_orders: int = 0
    
    total_value: Decimal = Decimal('0')
    average_order_value: Decimal = Decimal('0')
    largest_order_value: Decimal = Decimal('0')
    
    risk_score: float = 0.0
    compliance_score: float = 0.0
    performance_score: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_orders": self.total_orders,
            "active_orders": self.active_orders,
            "pending_orders": self.pending_orders,
            "executed_orders": self.executed_orders,
            "cancelled_orders": self.cancelled_orders,
            "total_value": float(self.total_value),
            "average_order_value": float(self.average_order_value),
            "largest_order_value": float(self.largest_order_value),
            "risk_score": self.risk_score,
            "compliance_score": self.compliance_score,
            "performance_score": self.performance_score
        }

class EnhancedOrderReview:
    """
    Enhanced order review system for comprehensive analysis.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize order review system.
        
        Args:
            data_dir: Data directory for reports and cache
        """
        if data_dir is None:
            data_dir = Path(__file__).resolve().parents[2] / "data"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.reports_dir = self.data_dir / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Enhanced order review initialized: {self.data_dir}")
    
    def analyze_orders(self, orders: List[Dict[str, Any]]) -> OrderReviewMetrics:
        """
        Analyze orders and calculate comprehensive metrics.
        
        Args:
            orders: List of order dictionaries
            
        Returns:
            Calculated order metrics
        """
        metrics = OrderReviewMetrics()
        
        if not orders:
            return metrics
        
        # Basic counts
        metrics.total_orders = len(orders)
        
        values = []
        for order in orders:
            status = order.get('status', '').lower()
            
            # Count by status
            if status == 'active':
                metrics.active_orders += 1
            elif status == 'pending':
                metrics.pending_orders += 1
            elif status == 'executed':
                metrics.executed_orders += 1
            elif status == 'cancelled':
                metrics.cancelled_orders += 1
            
            # Calculate values
            order_value = Decimal(str(order.get('value', 0)))
            values.append(order_value)
            metrics.total_value += order_value
        
        # Value metrics
        if values:
            metrics.average_order_value = metrics.total_value / len(values)
            metrics.largest_order_value = max(values)
        
        # Calculate scores
        metrics.risk_score = self._calculate_risk_score(orders)
        metrics.compliance_score = self._calculate_compliance_score(orders)
        metrics.performance_score = self._calculate_performance_score(orders)
        
        logger.info(f"Order analysis complete: {metrics.total_orders} orders processed")
        return metrics
    
    def _calculate_risk_score(self, orders: List[Dict[str, Any]]) -> float:
        """
        Calculate risk score based on order characteristics.
        
        Args:
            orders: List of order dictionaries
            
        Returns:
            Risk score (0-100, lower is better)
        """
        if not orders:
            return 0.0
        
        risk_factors = []
        
        for order in orders:
            order_risk = 0.0
            
            # Volume risk
            value = float(order.get('value', 0))
            if value > 10000:
                order_risk += 20
            elif value > 5000:
                order_risk += 10
            
            # Type risk
            order_type = order.get('type', '').lower()
            if 'market' in order_type:
                order_risk += 15
            elif 'stop' in order_type:
                order_risk += 10
            
            # Expiration risk
            expires_at = order.get('expires_at')
            if expires_at:
                try:
                    exp_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    days_to_exp = (exp_date - datetime.now()).days
                    if days_to_exp < 1:
                        order_risk += 25
                    elif days_to_exp < 7:
                        order_risk += 15
                except (ValueError, TypeError):
                    order_risk += 5
            
            risk_factors.append(min(order_risk, 100))
        
        return sum(risk_factors) / len(risk_factors) if risk_factors else 0.0
    
    def _calculate_compliance_score(self, orders: List[Dict[str, Any]]) -> float:
        """
        Calculate compliance score based on regulatory requirements.
        
        Args:
            orders: List of order dictionaries
            
        Returns:
            Compliance score (0-100, higher is better)
        """
        if not orders:
            return 100.0
        
        compliance_issues = 0
        total_checks = 0
        
        for order in orders:
            # Check for required fields
            required_fields = ['symbol', 'quantity', 'type', 'created_at']
            for field in required_fields:
                total_checks += 1
                if not order.get(field):
                    compliance_issues += 1
            
            # Check value limits
            total_checks += 1
            value = float(order.get('value', 0))
            if value > 50000:  # Assume $50k limit
                compliance_issues += 1
            
            # Check symbol format
            total_checks += 1
            symbol = order.get('symbol', '')
            if not symbol or len(symbol) < 3:
                compliance_issues += 1
        
        if total_checks == 0:
            return 100.0
        
        compliance_rate = 1 - (compliance_issues / total_checks)
        return max(0.0, compliance_rate * 100)
    
    def _calculate_performance_score(self, orders: List[Dict[str, Any]]) -> float:
        """
        Calculate performance score based on execution efficiency.
        
        Args:
            orders: List of order dictionaries
            
        Returns:
            Performance score (0-100, higher is better)
        """
        if not orders:
            return 0.0
        
        executed_orders = [o for o in orders if o.get('status') == 'executed']
        if not executed_orders:
            return 50.0  # Neutral score if no executed orders
        
        performance_factors = []
        
        for order in executed_orders:
            order_score = 70.0  # Base score
            
            # Execution speed bonus
            created_at = order.get('created_at')
            executed_at = order.get('executed_at')
            
            if created_at and executed_at:
                try:
                    created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    executed = datetime.fromisoformat(executed_at.replace('Z', '+00:00'))
                    execution_time = (executed - created).total_seconds()
                    
                    if execution_time < 60:  # Under 1 minute
                        order_score += 20
                    elif execution_time < 300:  # Under 5 minutes
                        order_score += 10
                    elif execution_time > 3600:  # Over 1 hour
                        order_score -= 20
                        
                except (ValueError, TypeError):
                    pass
            
            # Fill quality bonus
            requested_qty = float(order.get('quantity', 0))
            filled_qty = float(order.get('filled_quantity', 0))
            
            if requested_qty > 0:
                fill_rate = filled_qty / requested_qty
                if fill_rate >= 1.0:
                    order_score += 10
                elif fill_rate < 0.9:
                    order_score -= 15
            
            performance_factors.append(min(100.0, max(0.0, order_score)))
        
        return sum(performance_factors) / len(performance_factors)
    
    def generate_html_report(self, orders: List[Dict[str, Any]], 
                           metrics: Optional[OrderReviewMetrics] = None) -> str:
        """
        Generate comprehensive HTML report for order review.
        
        Args:
            orders: List of order dictionaries
            metrics: Pre-calculated metrics (optional)
            
        Returns:
            HTML report string
        """
        if metrics is None:
            metrics = self.analyze_orders(orders)
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Generate order table rows
        order_rows = []
        for i, order in enumerate(orders[:50], 1):  # Limit to 50 for display
            status_class = self._get_status_class(order.get('status', ''))
            
            row = f"""
            <tr class="{status_class}">
                <td>{i}</td>
                <td>{order.get('symbol', 'N/A')}</td>
                <td>{order.get('type', 'N/A')}</td>
                <td>{order.get('quantity', 0)}</td>
                <td>${order.get('value', 0):,.2f}</td>
                <td><span class="status status-{order.get('status', 'unknown').lower()}">{order.get('status', 'Unknown')}</span></td>
                <td>{order.get('created_at', 'N/A')[:19] if order.get('created_at') else 'N/A'}</td>
            </tr>
            """
            order_rows.append(row)
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>EMO Options Bot - Order Review Report</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background-color: #f5f7fa;
                    color: #333;
                }}
                .container {{
                    max-width: 1400px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 12px;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 2.5rem;
                    font-weight: 300;
                }}
                .timestamp {{
                    opacity: 0.9;
                    margin-top: 10px;
                    font-size: 1.1rem;
                }}
                .metrics-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    padding: 30px;
                    background: #f8f9fa;
                }}
                .metric-card {{
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                    text-align: center;
                    border-left: 4px solid #667eea;
                }}
                .metric-value {{
                    font-size: 2rem;
                    font-weight: bold;
                    color: #667eea;
                    margin: 10px 0;
                }}
                .metric-label {{
                    color: #6c757d;
                    font-size: 0.9rem;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .score-card {{
                    border-left-color: #28a745;
                }}
                .score-card .metric-value {{
                    color: #28a745;
                }}
                .risk-card {{
                    border-left-color: #dc3545;
                }}
                .risk-card .metric-value {{
                    color: #dc3545;
                }}
                .orders-section {{
                    padding: 30px;
                }}
                .section-title {{
                    font-size: 1.8rem;
                    margin-bottom: 20px;
                    color: #333;
                    border-bottom: 2px solid #667eea;
                    padding-bottom: 10px;
                }}
                .orders-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                    font-size: 0.9rem;
                }}
                .orders-table th {{
                    background: #667eea;
                    color: white;
                    padding: 15px 10px;
                    text-align: left;
                    font-weight: 600;
                }}
                .orders-table td {{
                    padding: 12px 10px;
                    border-bottom: 1px solid #eee;
                }}
                .orders-table tr:hover {{
                    background-color: #f8f9fa;
                }}
                .status {{
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 0.8rem;
                    font-weight: bold;
                    text-transform: uppercase;
                }}
                .status-active {{
                    background: #d4edda;
                    color: #155724;
                }}
                .status-pending {{
                    background: #fff3cd;
                    color: #856404;
                }}
                .status-executed {{
                    background: #cce7ff;
                    color: #004085;
                }}
                .status-cancelled {{
                    background: #f8d7da;
                    color: #721c24;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #6c757d;
                    border-top: 1px solid #dee2e6;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Order Review Report</h1>
                    <div class="timestamp">Generated: {timestamp}</div>
                </div>
                
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">{metrics.total_orders}</div>
                        <div class="metric-label">Total Orders</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{metrics.active_orders}</div>
                        <div class="metric-label">Active Orders</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">{metrics.executed_orders}</div>
                        <div class="metric-label">Executed Orders</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${metrics.total_value:,.0f}</div>
                        <div class="metric-label">Total Value</div>
                    </div>
                    <div class="metric-card score-card">
                        <div class="metric-value">{metrics.performance_score:.1f}%</div>
                        <div class="metric-label">Performance Score</div>
                    </div>
                    <div class="metric-card score-card">
                        <div class="metric-value">{metrics.compliance_score:.1f}%</div>
                        <div class="metric-label">Compliance Score</div>
                    </div>
                    <div class="metric-card risk-card">
                        <div class="metric-value">{metrics.risk_score:.1f}</div>
                        <div class="metric-label">Risk Score</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${metrics.average_order_value:,.0f}</div>
                        <div class="metric-label">Average Order Value</div>
                    </div>
                </div>
                
                <div class="orders-section">
                    <h2 class="section-title">📋 Recent Orders</h2>
                    <table class="orders-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Symbol</th>
                                <th>Type</th>
                                <th>Quantity</th>
                                <th>Value</th>
                                <th>Status</th>
                                <th>Created</th>
                            </tr>
                        </thead>
                        <tbody>
                            {''.join(order_rows)}
                        </tbody>
                    </table>
                </div>
                
                <div class="footer">
                    <p>EMO Options Bot - Enhanced Order Review System v2.0</p>
                    <p>Report generated automatically • Refresh for latest data</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _get_status_class(self, status: str) -> str:
        """Get CSS class for order status."""
        status_lower = status.lower()
        if status_lower == 'executed':
            return 'table-success'
        elif status_lower == 'cancelled':
            return 'table-danger'
        elif status_lower == 'pending':
            return 'table-warning'
        elif status_lower == 'active':
            return 'table-info'
        else:
            return ''
    
    def save_report(self, orders: List[Dict[str, Any]], 
                   filename: Optional[str] = None) -> Path:
        """
        Save order review report to file.
        
        Args:
            orders: List of order dictionaries
            filename: Output filename (auto-generated if None)
            
        Returns:
            Path to saved report file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"order_review_{timestamp}.html"
        
        report_path = self.reports_dir / filename
        
        try:
            html_content = self.generate_html_report(orders)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"Order review report saved: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Failed to save order review report: {e}")
            raise
    
    def get_recent_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get list of recent report files.
        
        Args:
            limit: Maximum number of reports to return
            
        Returns:
            List of report file information
        """
        try:
            report_files = list(self.reports_dir.glob("order_review_*.html"))
            report_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            reports = []
            for report_file in report_files[:limit]:
                stat = report_file.stat()
                reports.append({
                    "filename": report_file.name,
                    "path": str(report_file),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "url": f"file://{report_file.as_posix()}"
                })
            
            return reports
            
        except Exception as e:
            logger.error(f"Failed to get recent reports: {e}")
            return []

# Export key classes
__all__ = [
    "EnhancedOrderReview",
    "OrderReviewMetrics"
]