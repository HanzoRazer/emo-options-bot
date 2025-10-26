#!/usr/bin/env python3
"""
EMO Options Bot - Dashboard Launcher
Quick launcher for the web dashboard
"""

import sys
from pathlib import Path

# Add src to Python path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from src.web.dashboard import main as dashboard_main

if __name__ == "__main__":
    print("🚀 EMO Options Bot Dashboard")
    print("Starting web interface...")
    dashboard_main()
        '<th>Symbol</th><th>Trend</th><th>Confidence</th><th>Exp. Return</th><th>Notes</th>'
        '</tr></thead><tbody>'
        + "".join(rows) +
        '</tbody></table>'
        f'<div class="meta" style="margin-top:8px;color:#666">Updated: {data.get("generated_at","")}</div>'
        '</div>'
    )
    return html

def _get_database_status():
    """Get status information from the database."""
    db_path = ROOT / "ops" / "describer.db"
    if not db_path.exists():
        return {"status": "No database found", "runs": 0, "symbols": 0}
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get run count
        cursor.execute("SELECT COUNT(*) FROM runs")
        run_count = cursor.fetchone()[0]
        
        # Get latest run info
        cursor.execute("SELECT ts_utc, regime, info_shock FROM runs ORDER BY ts_utc DESC LIMIT 1")
        latest_run = cursor.fetchone()
        
        # Get symbol count
        cursor.execute("SELECT COUNT(DISTINCT symbol) FROM symbols")
        symbol_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "status": "Connected",
            "runs": run_count,
            "symbols": symbol_count,
            "latest_run": latest_run[0] if latest_run else "None",
            "latest_regime": latest_run[1] if latest_run else "Unknown",
            "latest_shock": latest_run[2] if latest_run else 0
        }
    except Exception as e:
        return {"status": f"Error: {e}", "runs": 0, "symbols": 0}

def _render_status_card():
    """Render system status card."""
    db_status = _get_database_status()
    
    status_color = "#4CAF50" if db_status["status"] == "Connected" else "#f44336"
    
    html = f'''
    <div class="card">
        <h2>📊 System Status</h2>
        <div class="status-grid">
            <div class="status-item">
                <strong>Database:</strong> 
                <span style="color:{status_color}">{db_status["status"]}</span>
            </div>
            <div class="status-item">
                <strong>Total Runs:</strong> {db_status["runs"]}
            </div>
            <div class="status-item">
                <strong>Symbols Tracked:</strong> {db_status["symbols"]}
            </div>
            <div class="status-item">
                <strong>Latest Run:</strong> {db_status.get("latest_run", "None")}
            </div>
            <div class="status-item">
                <strong>Current Regime:</strong> {db_status.get("latest_regime", "Unknown")}
            </div>
            <div class="status-item">
                <strong>Info Shock:</strong> {db_status.get("latest_shock", 0):.3f}
            </div>
        </div>
    </div>
    '''
    return html

def _render_actions_card():
    """Render quick actions card."""
    html = '''
    <div class="card">
        <h2>🚀 Quick Actions</h2>
        <div class="actions">
            <button onclick="generateMLOutlook()" class="action-btn">🧠 Generate ML Outlook</button>
            <button onclick="runDescriber()" class="action-btn">📈 Run Describer</button>
            <button onclick="refreshPage()" class="action-btn">🔄 Refresh Dashboard</button>
        </div>
        <div class="command-help">
            <h3>Command Line:</h3>
            <code>python tools/ml_outlook_bridge.py</code><br>
            <code>python app_describer.py</code><br>
            <code>python predict_ml.py --action health</code>
        </div>
    </div>
    '''
    return html

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Generate dashboard HTML
            ml_card = _render_ml_card()
            status_card = _render_status_card()
            actions_card = _render_actions_card()
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>EMO Options Bot Dashboard</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: #f5f5f5;
                        color: #333;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                        padding: 20px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        border-radius: 10px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    }}
                    .dashboard-grid {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                        gap: 20px;
                        max-width: 1200px;
                        margin: 0 auto;
                    }}
                    .card {{
                        background: white;
                        border-radius: 10px;
                        padding: 20px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        transition: transform 0.2s ease;
                    }}
                    .card:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
                    }}
                    .card h2 {{
                        margin-top: 0;
                        color: #333;
                        border-bottom: 2px solid #eee;
                        padding-bottom: 10px;
                    }}
                    .ml-table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 10px;
                    }}
                    .ml-table th, .ml-table td {{
                        padding: 8px 12px;
                        text-align: left;
                        border-bottom: 1px solid #eee;
                    }}
                    .ml-table th {{
                        background-color: #f8f9fa;
                        font-weight: bold;
                        color: #555;
                    }}
                    .status-grid {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 15px;
                    }}
                    .status-item {{
                        padding: 10px;
                        background-color: #f8f9fa;
                        border-radius: 5px;
                        border-left: 4px solid #667eea;
                    }}
                    .actions {{
                        display: flex;
                        flex-wrap: wrap;
                        gap: 10px;
                        margin-bottom: 20px;
                    }}
                    .action-btn {{
                        padding: 10px 20px;
                        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                        font-size: 14px;
                        transition: background 0.3s ease;
                    }}
                    .action-btn:hover {{
                        background: linear-gradient(135deg, #45a049 0%, #4CAF50 100%);
                        transform: translateY(-1px);
                    }}
                    .command-help {{
                        background-color: #f8f9fa;
                        padding: 15px;
                        border-radius: 5px;
                        border-left: 4px solid #FF9800;
                    }}
                    .command-help code {{
                        background-color: #333;
                        color: #f8f8f2;
                        padding: 4px 8px;
                        border-radius: 3px;
                        display: block;
                        margin: 5px 0;
                        font-family: 'Courier New', monospace;
                    }}
                    .meta {{
                        font-size: 12px;
                        color: #666;
                        margin-top: 10px;
                        font-style: italic;
                    }}
                    .footer {{
                        text-align: center;
                        margin-top: 30px;
                        padding: 20px;
                        color: #666;
                        font-size: 14px;
                    }}
                </style>
                <script>
                    function generateMLOutlook() {{
                        alert('Run: python tools/ml_outlook_bridge.py\\nThen refresh this page.');
                    }}
                    function runDescriber() {{
                        alert('Run: python app_describer.py\\nThen refresh this page.');
                    }}
                    function refreshPage() {{
                        location.reload();
                    }}
                    // Auto-refresh every 30 seconds
                    setTimeout(function() {{
                        location.reload();
                    }}, 30000);
                </script>
            </head>
            <body>
                <div class="header">
                    <h1>🤖 EMO Options Bot Dashboard</h1>
                    <p>Machine Learning Enhanced Options Trading Platform</p>
                    <p style="margin:0;opacity:0.8">Generated: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="dashboard-grid">
                    {ml_card}
                    {status_card}
                    {actions_card}
                </div>
                
                <div class="footer">
                    <p>🔄 Auto-refresh: 30 seconds | 🚀 EMO Options Bot v2.0 with ML Integration</p>
                </div>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode())
        
        elif self.path == '/api/status':
            # API endpoint for status
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            status = {
                "timestamp": dt.datetime.now().isoformat(),
                "database": _get_database_status(),
                "ml_outlook": _read_ml_outlook()
            }
            
            self.wfile.write(json.dumps(status, indent=2).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

def serve_dashboard(host='localhost', port=8083):
    """Start the dashboard web server."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, DashboardHandler)
    
    print(f"🚀 EMO Options Bot Dashboard")
    print(f"📊 Starting server at http://{host}:{port}/")
    print(f"🔄 Auto-refresh enabled (30 seconds)")
    print(f"🧠 ML Outlook integration active")
    print(f"💾 Database: {ROOT}/ops/describer.db")
    print(f"📈 ML Data: {ROOT}/ops/ml_outlook.json")
    print()
    print("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Dashboard server stopped")
        httpd.server_close()

def main():
    """Main function."""
    serve_dashboard()

if __name__ == "__main__":
    main()