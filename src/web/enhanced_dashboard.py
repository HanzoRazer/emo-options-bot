#!/usr/bin/env python3
"""
Enhanced EMO Options Bot Dashboard with Risk Management Integration
Combines ML outlook, market data, strategy signals, and real-time risk monitoring.
"""

from __future__ import annotations
import json, os, sqlite3, csv
from pathlib import Path
from typing import Dict, Any, List, Optional
import datetime as dt
from dataclasses import asdict

# Import our risk management system
import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.logic.risk_manager import RiskManager, PortfolioSnapshot, Position
from src.database.models import get_db_connection

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OPS = ROOT / "ops"
ML_JSON = DATA / "ml_outlook.json"
SIGNALS_CSV = OPS / "signals.csv"
OUT_HTML = ROOT / "enhanced_dashboard.html"

class EnhancedDashboard:
    """Enhanced dashboard with risk management integration."""
    
    def __init__(self):
        self.risk_manager = RiskManager(
            portfolio_risk_cap=0.25,
            per_position_risk=0.05,
            max_positions=5,
            max_beta_exposure=1.5
        )
    
    def _read_json(self, p: Path) -> Any | None:
        """Safe JSON reader with error handling."""
        try:
            if p.exists():
                return json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[dashboard] JSON read error {p.name}: {e}")
        return None
    
    def _get_portfolio_snapshot(self) -> PortfolioSnapshot:
        """Get current portfolio snapshot from database."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get current equity (mock data for demo)
            equity = 50000.0
            cash = 15000.0
            
            # Get current positions from database
            cursor.execute("""
                SELECT symbol, AVG(c) as mark, COUNT(*) as qty 
                FROM bars 
                WHERE symbol IN ('SPY', 'QQQ', 'AAPL', 'MSFT') 
                GROUP BY symbol 
                ORDER BY symbol
            """)
            
            positions = []
            for row in cursor.fetchall():
                symbol, mark, qty = row
                # Mock position data - in real system this would come from broker
                qty = 100 if symbol in ['SPY', 'QQQ'] else 50
                value = qty * mark
                max_loss = value * 0.15  # Assume 15% max loss estimate
                beta = {'SPY': 1.0, 'QQQ': 1.2, 'AAPL': 1.3, 'MSFT': 1.1}.get(symbol, 1.0)
                
                positions.append(Position(
                    symbol=symbol,
                    qty=qty,
                    mark=mark,
                    value=value,
                    max_loss=max_loss,
                    beta=beta
                ))
            
            conn.close()
            return PortfolioSnapshot(equity=equity, cash=cash, positions=positions)
            
        except Exception as e:
            print(f"[dashboard] Portfolio snapshot error: {e}")
            return PortfolioSnapshot(equity=50000.0, cash=15000.0, positions=[])
    
    def _render_risk_management_card(self) -> str:
        """Render risk management status card."""
        portfolio = self._get_portfolio_snapshot()
        assessment = self.risk_manager.assess_portfolio(portfolio)
        
        # Calculate key metrics
        total_risk = sum(pos.max_loss for pos in portfolio.positions)
        risk_pct = (total_risk / portfolio.equity * 100) if portfolio.equity > 0 else 0
        beta_exposure = sum(pos.value * pos.beta for pos in portfolio.positions) / portfolio.equity
        
        # Status colors
        risk_color = "#4CAF50" if risk_pct < 15 else "#FF9800" if risk_pct < 20 else "#f44336"
        beta_color = "#4CAF50" if abs(beta_exposure) < 1.2 else "#FF9800" if abs(beta_exposure) < 1.4 else "#f44336"
        
        # Position rows
        position_rows = ""
        for pos in portfolio.positions:
            risk_per_pos = (pos.max_loss / portfolio.equity * 100) if portfolio.equity > 0 else 0
            pos_color = "#4CAF50" if risk_per_pos < 3 else "#FF9800" if risk_per_pos < 5 else "#f44336"
            
            position_rows += f"""
            <tr>
                <td><strong>{pos.symbol}</strong></td>
                <td>{pos.qty:,.0f}</td>
                <td>${pos.mark:.2f}</td>
                <td>${pos.value:,.0f}</td>
                <td style="color:{pos_color}; font-weight:bold">${pos.max_loss:,.0f}</td>
                <td>{pos.beta:.2f}</td>
            </tr>
            """
        
        # Assessment messages
        assessment_html = ""
        if assessment.get("violations"):
            assessment_html += '<div class="alert alert-danger"><h4>⚠️ Risk Violations:</h4><ul>'
            for violation in assessment["violations"]:
                assessment_html += f'<li>{violation}</li>'
            assessment_html += '</ul></div>'
        
        if assessment.get("warnings"):
            assessment_html += '<div class="alert alert-warning"><h4>⚡ Risk Warnings:</h4><ul>'
            for warning in assessment["warnings"]:
                assessment_html += f'<li>{warning}</li>'
            assessment_html += '</ul></div>'
        
        return f"""
        <div class="card">
            <h2>🛡️ Risk Management</h2>
            <div class="risk-summary">
                <div class="metric">
                    <span class="label">Portfolio Risk:</span>
                    <span class="value" style="color:{risk_color}; font-weight:bold">{risk_pct:.1f}%</span>
                </div>
                <div class="metric">
                    <span class="label">Beta Exposure:</span>
                    <span class="value" style="color:{beta_color}; font-weight:bold">{beta_exposure:.2f}</span>
                </div>
                <div class="metric">
                    <span class="label">Positions:</span>
                    <span class="value">{len(portfolio.positions)}/5</span>
                </div>
                <div class="metric">
                    <span class="label">Available Cash:</span>
                    <span class="value">${portfolio.cash:,.0f}</span>
                </div>
            </div>
            
            {assessment_html}
            
            <h3>Current Positions</h3>
            <table class="positions-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Qty</th>
                        <th>Mark</th>
                        <th>Value</th>
                        <th>Max Loss</th>
                        <th>Beta</th>
                    </tr>
                </thead>
                <tbody>
                    {position_rows}
                </tbody>
            </table>
        </div>
        """
    
    def _render_ml_outlook_card(self) -> str:
        """Enhanced ML outlook card with risk integration."""
        if not ML_JSON.exists():
            return '''<div class="card">
                <h2>🧠 ML Outlook</h2>
                <div class="muted">No ML outlook data yet. Run ML training pipeline to generate predictions.</div>
            </div>'''
        
        try:
            data = json.loads(ML_JSON.read_text(encoding="utf-8"))
            
            # Extract main prediction data
            prediction = data.get("prediction", "n/a")
            confidence = data.get("confidence", "n/a")
            timestamp = data.get("ts", data.get("timestamp", ""))
            models = data.get("models", [])
            notes = data.get("notes", "")
            
            # Format confidence
            if isinstance(confidence, (int, float)):
                confidence_str = f"{confidence:.1%}"
                confidence_color = "#4CAF50" if confidence > 0.7 else "#FF9800" if confidence > 0.5 else "#f44336"
            else:
                confidence_str = str(confidence)
                confidence_color = "#9fb0d4"
            
            # Format prediction with color
            prediction_color = {
                "bullish": "#4CAF50",
                "bearish": "#f44336", 
                "neutral": "#FF9800",
                "slightly_bullish": "#81C784",
                "slightly_bearish": "#E57373"
            }.get(str(prediction).lower(), "#9fb0d4")
            
            models_str = ", ".join(models) if models else "Unknown"
            
            return f'''<div class="card">
                <h2>🧠 ML Outlook</h2>
                <div class="ml-summary">
                    <div class="metric">
                        <span class="label">Prediction:</span>
                        <span class="value" style="color:{prediction_color}; font-weight:bold">{prediction}</span>
                    </div>
                    <div class="metric">
                        <span class="label">Confidence:</span>
                        <span class="value" style="color:{confidence_color}; font-weight:bold">{confidence_str}</span>
                    </div>
                    <div class="metric">
                        <span class="label">Models:</span>
                        <span class="value">{models_str}</span>
                    </div>
                </div>
                {f'<div class="notes"><strong>Notes:</strong> {notes}</div>' if notes else ''}
                <div class="timestamp">Updated: {timestamp}</div>
            </div>'''
            
        except Exception as e:
            return f'''<div class="card">
                <h2>🧠 ML Outlook</h2>
                <div class="error">Error reading ML data: {e}</div>
            </div>'''

    def _render_strategy_signals_card(self, max_rows: int = 20) -> str:
        """Render strategy signals from CSV file."""
        if not SIGNALS_CSV.exists():
            return '''<div class="card">
                <h2>🎯 Strategy Signals</h2>
                <div class="muted">No strategy signals yet. Enable signal-based strategies to see recommendations.</div>
            </div>'''
        
        try:
            # Read signals from CSV
            signals = []
            with open(SIGNALS_CSV, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                signals = list(reader)
            
            if not signals:
                return '''<div class="card">
                    <h2>🎯 Strategy Signals</h2>
                    <div class="muted">No signals generated yet.</div>
                </div>'''
            
            # Get most recent signals
            recent_signals = signals[-max_rows:]
            recent_signals.reverse()  # Most recent first
            
            # Count actions
            actions = [s.get("action", "") for s in signals]
            enter_count = actions.count("enter")
            exit_count = actions.count("exit")
            hold_count = actions.count("hold")
            
            # Generate signal rows
            signal_rows = ""
            for signal in recent_signals:
                ts = signal.get("ts", "")
                symbol = signal.get("symbol", "")
                strategy = signal.get("strategy", "")
                action = signal.get("action", "")
                confidence = signal.get("confidence", "0")
                notes = signal.get("notes", "")
                
                # Format timestamp
                try:
                    if ts:
                        dt_obj = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                        formatted_time = dt_obj.strftime("%m/%d %H:%M")
                    else:
                        formatted_time = "—"
                except:
                    formatted_time = ts[:16] if len(ts) > 16 else ts
                
                # Action colors
                action_color = {
                    "enter": "#4CAF50",
                    "exit": "#f44336",
                    "hold": "#FF9800"
                }.get(action.lower(), "#9fb0d4")
                
                # Confidence formatting
                try:
                    conf_float = float(confidence)
                    conf_str = f"{conf_float:.2f}"
                    conf_color = "#4CAF50" if conf_float > 0.7 else "#FF9800" if conf_float > 0.4 else "#f44336"
                except:
                    conf_str = confidence
                    conf_color = "#9fb0d4"
                
                # Truncate notes
                short_notes = notes[:50] + "..." if len(notes) > 50 else notes
                
                signal_rows += f'''
                <tr>
                    <td>{formatted_time}</td>
                    <td><strong>{symbol}</strong></td>
                    <td>{strategy}</td>
                    <td style="color:{action_color}; font-weight:bold">{action.upper()}</td>
                    <td style="color:{conf_color}">{conf_str}</td>
                    <td class="notes-cell" title="{notes}">{short_notes}</td>
                </tr>
                '''
            
            return f'''<div class="card">
                <h2>🎯 Strategy Signals</h2>
                <div class="signals-summary">
                    <div class="metric">
                        <span class="label">Total Signals:</span>
                        <span class="value">{len(signals)}</span>
                    </div>
                    <div class="metric">
                        <span class="label">Enter:</span>
                        <span class="value" style="color:#4CAF50">{enter_count}</span>
                    </div>
                    <div class="metric">
                        <span class="label">Exit:</span>
                        <span class="value" style="color:#f44336">{exit_count}</span>
                    </div>
                    <div class="metric">
                        <span class="label">Hold:</span>
                        <span class="value" style="color:#FF9800">{hold_count}</span>
                    </div>
                </div>
                
                <h3>Recent Signals</h3>
                <table class="signals-table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Symbol</th>
                            <th>Strategy</th>
                            <th>Action</th>
                            <th>Confidence</th>
                            <th>Notes</th>
                        </tr>
                    </thead>
                    <tbody>
                        {signal_rows}
                    </tbody>
                </table>
            </div>'''
            
        except Exception as e:
            return f'''<div class="card">
                <h2>🎯 Strategy Signals</h2>
                <div class="error">Error reading signals: {e}</div>
            </div>'''
            
            if symbol in current_symbols:
                risk_indicator = '<span class="risk-indicator current">HELD</span>'
            elif direction == 'up' and confidence > 0.7:
                risk_indicator = '<span class="risk-indicator buy-signal">BUY SIGNAL</span>'
            elif direction == 'down' and confidence > 0.7:
                risk_indicator = '<span class="risk-indicator sell-signal">SELL SIGNAL</span>'
            
            # Color coding
            direction_color = "#4CAF50" if direction == "up" else "#f44336" if direction == "down" else "#FF9800"
            confidence_color = "#4CAF50" if confidence > 0.7 else "#FF9800" if confidence > 0.5 else "#f44336"
            
            rows_html += f"""
            <tr>
                <td><strong>{symbol}</strong> {in_portfolio}</td>
                <td style="color:{direction_color}; font-weight:bold">{direction.upper()}</td>
                <td style="color:{confidence_color}; font-weight:bold">{confidence:.3f}</td>
                <td>{score:.3f}</td>
                <td>{risk_indicator}</td>
            </tr>
            """
        
        return f"""
        <div class="card">
            <h2>🧠 ML Outlook</h2>
            <div class="meta">Updated: {updated} • Models: <code>{models}</code></div>
            <table class="ml-table">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Direction</th>
                        <th>Confidence</th>
                        <th>Score</th>
                        <th>Risk Context</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        """
    
    def _render_market_data_card(self) -> str:
        """Render market data and trends card."""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Get latest market data
            cursor.execute("""
                SELECT symbol, MAX(t) as latest_time, c as close, v as volume
                FROM bars 
                WHERE tf = '1Min'
                GROUP BY symbol 
                ORDER BY symbol
            """)
            
            market_rows = ""
            for row in cursor.fetchall():
                symbol, latest_time, close, volume = row
                # Convert timestamp to readable format
                dt_obj = dt.datetime.fromtimestamp(latest_time / 1000)
                time_str = dt_obj.strftime("%H:%M:%S")
                
                market_rows += f"""
                <tr>
                    <td><strong>{symbol}</strong></td>
                    <td>${close:.2f}</td>
                    <td>{volume:,}</td>
                    <td>{time_str}</td>
                </tr>
                """
            
            conn.close()
            
            # Image tags for charts
            shock_img = self._img_tag_if_exists('data/shock_trend.png')
            volume_img = self._img_tag_if_exists('data/volume_trend.png')
            
            return f"""
            <div class="card">
                <h2>📈 Market Data</h2>
                <div class="market-grid">
                    <div class="chart-section">
                        <h3>Market Trends</h3>
                        <div class="charts">
                            {shock_img}
                            {volume_img}
                        </div>
                    </div>
                    <div class="data-section">
                        <h3>Latest Prices</h3>
                        <table class="market-table">
                            <thead>
                                <tr>
                                    <th>Symbol</th>
                                    <th>Price</th>
                                    <th>Volume</th>
                                    <th>Last Update</th>
                                </tr>
                            </thead>
                            <tbody>
                                {market_rows}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            """
            
        except Exception as e:
            return f"""
            <div class="card">
                <h2>📈 Market Data</h2>
                <div class="error">Error loading market data: {e}</div>
            </div>
            """
    
    def _img_tag_if_exists(self, rel_path: str) -> str:
        """Generate image tag if file exists."""
        p = ROOT / rel_path
        if p.exists():
            return f'<img src="{rel_path.replace("\\","/")}" alt="{os.path.basename(rel_path)}" class="chart-img" />'
        return f'<div class="muted">No {os.path.basename(rel_path)} yet.</div>'
    
    def generate_dashboard(self) -> str:
        """Generate the complete enhanced dashboard HTML."""
        now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>EMO — Enhanced Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <style>
        body {{
            font: 14px system-ui, -apple-system, Segoe UI, Arial, sans-serif;
            margin: 0;
            padding: 24px;
            background: #0b1220;
            color: #e8eefc;
            line-height: 1.5;
        }}
        
        h1, h2, h3 {{
            margin: 0 0 16px 0;
            font-weight: 700;
        }}
        
        h1 {{ font-size: 28px; }}
        h2 {{ font-size: 20px; color: #9dc1ff; }}
        h3 {{ font-size: 16px; color: #b8d4ff; }}
        
        .meta {{
            color: #9fb0d4;
            margin-bottom: 16px;
            font-size: 12px;
        }}
        
        .dashboard-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 24px;
        }}
        
        @media (min-width: 1200px) {{
            .dashboard-grid {{
                grid-template-columns: 2fr 1fr;
            }}
        }}
        
        .card {{
            border: 1px solid #243354;
            background: #0f1730;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        
        .risk-summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin: 16px 0;
            padding: 16px;
            background: #141f3a;
            border-radius: 8px;
        }}
        
        .metric {{
            text-align: center;
        }}
        
        .metric .label {{
            display: block;
            color: #9fb0d4;
            font-size: 12px;
            margin-bottom: 4px;
        }}
        
        .metric .value {{
            display: block;
            font-size: 18px;
            font-weight: bold;
        }}
        
        .alert {{
            padding: 12px;
            border-radius: 6px;
            margin: 12px 0;
        }}
        
        .alert-danger {{
            background: rgba(244, 67, 54, 0.1);
            border: 1px solid #f44336;
            color: #ffcdd2;
        }}
        
        .alert-warning {{
            background: rgba(255, 152, 0, 0.1);
            border: 1px solid #FF9800;
            color: #ffcc02;
        }}
        
        .alert h4 {{
            margin: 0 0 8px 0;
            font-size: 14px;
        }}
        
        .alert ul {{
            margin: 0;
            padding-left: 20px;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-top: 12px;
        }}
        
        th, td {{
            border: 1px solid #243354;
            padding: 8px 12px;
            text-align: left;
            font-variant-numeric: tabular-nums;
        }}
        
        th {{
            background: #141f3a;
            font-weight: 600;
            color: #b8d4ff;
        }}
        
        .risk-indicator {{
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
        }}
        
        .risk-indicator.current {{
            background: #4CAF50;
            color: white;
        }}
        
        .risk-indicator.buy-signal {{
            background: #2196F3;
            color: white;
        }}
        
        .risk-indicator.sell-signal {{
            background: #f44336;
            color: white;
        }}
        
        .market-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
        }}
        
        @media (min-width: 800px) {{
            .market-grid {{
                grid-template-columns: 1fr 1fr;
            }}
        }}
        
        .charts {{
            display: grid;
            gap: 12px;
        }}
        
        .chart-img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #243354;
            border-radius: 8px;
        }}
        
        .signals-summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }}
        
        .signals-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 12px;
        }}
        
        .signals-table th,
        .signals-table td {{
            padding: 8px 12px;
            text-align: left;
            border-bottom: 1px solid #2b3a52;
        }}
        
        .signals-table th {{
            background: #1b2332;
            font-weight: 600;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .signals-table tr:hover {{
            background: rgba(33, 150, 243, 0.1);
        }}
        
        .notes-cell {{
            max-width: 200px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-size: 12px;
            color: #9fb0d4;
        }}
        
        .ml-summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }}
        
        .notes {{
            background: rgba(33, 150, 243, 0.1);
            padding: 12px;
            border-radius: 6px;
            margin: 16px 0;
            font-size: 13px;
        }}
        
        .timestamp {{
            color: #9fb0d4;
            font-size: 12px;
            margin-top: 12px;
            font-style: italic;
        }}
        
        .error {{
            color: #f44336;
            background: rgba(244, 67, 54, 0.1);
            padding: 12px;
            border-radius: 6px;
        }}
        
        .refresh-btn {{
            background: #2196F3;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 12px;
        }}
        
        .refresh-btn:hover {{
            background: #1976D2;
        }}
    </style>
</head>
<body>
    <h1>🚀 EMO — Enhanced Trading Dashboard</h1>
    <div class="meta">
        Generated: {now} 
        <button class="refresh-btn" onclick="window.location.reload()">🔄 Refresh</button>
    </div>
    
    <div class="dashboard-grid">
        <div class="main-column">
            {self._render_risk_management_card()}
            {self._render_market_data_card()}
        </div>
        <div class="side-column">
            {self._render_ml_outlook_card()}
            {self._render_strategy_signals_card()}
        </div>
    </div>
    
    <script>
        // Auto-refresh every 60 seconds
        setTimeout(() => {{
            window.location.reload();
        }}, 60000);
    </script>
</body>
</html>"""
    
    def build_dashboard(self):
        """Build and save the enhanced dashboard."""
        html = self.generate_dashboard()
        OUT_HTML.write_text(html, encoding="utf-8")
        print(f"[enhanced_dashboard] Generated {OUT_HTML}")
        return OUT_HTML

def main():
    """Main entry point for enhanced dashboard generation."""
    dashboard = EnhancedDashboard()
    dashboard.build_dashboard()

if __name__ == "__main__":
    main()