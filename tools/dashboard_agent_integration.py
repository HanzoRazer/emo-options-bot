# tools/dashboard_agent_integration.py
"""
Dashboard integration for AI agent state.
Adds agent cards to the existing dashboard.
"""

import json
import urllib.request
from datetime import datetime
from pathlib import Path

def fetch_agent_last(timeout: float = 1.0):
    """Fetch the last agent state from the API."""
    try:
        with urllib.request.urlopen("http://localhost:8085/last", timeout=timeout) as response:
            return json.loads(response.read().decode())
    except Exception:
        return None

def fetch_agent_status(timeout: float = 1.0):
    """Fetch the agent system status from the API.""" 
    try:
        with urllib.request.urlopen("http://localhost:8085/status", timeout=timeout) as response:
            return json.loads(response.read().decode())
    except Exception:
        return None

def generate_agent_dashboard_cards():
    """Generate HTML cards for agent status and last processing."""
    
    agent_state = fetch_agent_last()
    agent_status = fetch_agent_status()
    
    cards_html = ""
    
    # Agent Status Card
    if agent_status:
        api_status = agent_status.get("api", {}).get("status", "unknown")
        voice_status = agent_status.get("voice", {}).get("available", False)
        tts_status = agent_status.get("tts", {}).get("available", False)
        last_processing = agent_status.get("last_processing")
        
        status_color = "success" if api_status == "running" else "warning"
        
        cards_html += f"""
        <div class="card mb-3">
            <div class="card-header bg-{status_color} text-white">
                <h5 class="mb-0">🤖 AI Agent Status</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <p><strong>API Status:</strong> <span class="badge badge-{status_color}">{api_status.upper()}</span></p>
                        <p><strong>Voice Recognition:</strong> {"✅ Available" if voice_status else "❌ Stub Mode"}</p>
                        <p><strong>Text-to-Speech:</strong> {"✅ Available" if tts_status else "❌ Stub Mode"}</p>
                    </div>
                    <div class="col-md-6">
                        <p><strong>Last Processing:</strong><br>
                           <small>{last_processing if last_processing else "None"}</small></p>
                        <p><strong>Session ID:</strong><br>
                           <small>{agent_status.get('session_id', 'N/A')}</small></p>
                    </div>
                </div>
            </div>
        </div>
        """
    
    # Last Agent Processing Card
    if agent_state and agent_state.get("intent"):
        intent = agent_state.get("intent", {})
        plan = agent_state.get("plan", {})
        validation = agent_state.get("validation", {})
        timestamp = agent_state.get("timestamp", "")
        
        # Determine card color based on validation
        if validation and validation.get("ok"):
            card_color = "success"
            status_text = "✅ VALIDATED"
        elif validation and not validation.get("ok"):
            card_color = "danger"  
            status_text = "❌ VALIDATION FAILED"
        else:
            card_color = "info"
            status_text = "ℹ️ PROCESSED"
        
        cards_html += f"""
        <div class="card mb-3">
            <div class="card-header bg-{card_color} text-white">
                <h5 class="mb-0">📊 Last AI Processing - {status_text}</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-4">
                        <h6>Intent</h6>
                        <p><strong>Kind:</strong> {intent.get('kind', 'N/A')}</p>
                        <p><strong>Symbol:</strong> {intent.get('symbol', 'N/A')}</p>
                        <p><strong>Strategy:</strong> {intent.get('strategy', 'N/A')}</p>
                    </div>
                    <div class="col-md-4">
                        <h6>Plan Details</h6>
                        <p><strong>Strategy:</strong> {plan.get('strategy', 'N/A').replace('_', ' ').title()}</p>
                        <p><strong>DTE:</strong> {plan.get('dte', 'N/A')}</p>
                        <p><strong>Risk Level:</strong> {plan.get('risk_level', 'N/A').title()}</p>
                        <p><strong>Legs:</strong> {len(plan.get('legs', []))}</p>
                    </div>
                    <div class="col-md-4">
                        <h6>Validation</h6>
                        <p><strong>Status:</strong> {"✅ Passed" if validation.get('ok') else "❌ Failed"}</p>
                        <p><strong>Risk Score:</strong> {validation.get('risk_score', 'N/A'):.1f}/10</p>
                        <p><strong>Warnings:</strong> {len(validation.get('warnings', []))}</p>
                        <p><strong>Errors:</strong> {len(validation.get('errors', []))}</p>
                    </div>
                </div>
                
                {"" if not plan.get('legs') else f'''
                <hr>
                <h6>Option Legs</h6>
                <div class="table-responsive">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>Action</th>
                                <th>Strike</th>
                                <th>Quantity</th>
                                <th>Expiry</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join([f'''
                            <tr>
                                <td>{leg.get('kind', 'N/A').replace('_', ' ').title()}</td>
                                <td>${leg.get('strike', 0):.2f}</td>
                                <td>{leg.get('qty', 0)}</td>
                                <td>{leg.get('expiry', 'N/A')}</td>
                            </tr>
                            ''' for leg in plan.get('legs', [])])}
                        </tbody>
                    </table>
                </div>
                '''}
                
                {"" if not validation.get('warnings') and not validation.get('errors') else f'''
                <hr>
                <h6>Validation Details</h6>
                {"".join([f'<div class="alert alert-warning py-2"><small>⚠️ {warning}</small></div>' for warning in validation.get('warnings', [])])}
                {"".join([f'<div class="alert alert-danger py-2"><small>❌ {error}</small></div>' for error in validation.get('errors', [])])}
                '''}
                
                <hr>
                <small class="text-muted">
                    Processed: {timestamp}<br>
                    <a href="http://localhost:8085/last" target="_blank">View Raw JSON</a> | 
                    <a href="http://localhost:8085/status" target="_blank">System Status</a>
                </small>
            </div>
        </div>
        """
    else:
        # No recent processing
        cards_html += f"""
        <div class="card mb-3">
            <div class="card-header bg-secondary text-white">
                <h5 class="mb-0">📊 AI Agent Processing</h5>
            </div>
            <div class="card-body">
                <p class="text-muted">No recent agent processing detected.</p>
                <p>Start the agent with: <code>python tools/agent_happy_path.py</code></p>
                <small><a href="http://localhost:8085/health" target="_blank">Check API Health</a></small>
            </div>
        </div>
        """
    
    return cards_html

def generate_agent_quick_actions():
    """Generate quick action buttons for agent control."""
    
    return """
    <div class="card mb-3">
        <div class="card-header bg-primary text-white">
            <h5 class="mb-0">🎮 AI Agent Quick Actions</h5>
        </div>
        <div class="card-body">
            <div class="btn-group" role="group">
                <button type="button" class="btn btn-success btn-sm" onclick="testAgentCommand('Build an iron condor on SPY')">
                    Iron Condor SPY
                </button>
                <button type="button" class="btn btn-info btn-sm" onclick="testAgentCommand('Create a put credit spread on QQQ with low risk')">
                    Put Credit QQQ
                </button>
                <button type="button" class="btn btn-warning btn-sm" onclick="testAgentCommand('Status')">
                    System Status
                </button>
                <button type="button" class="btn btn-secondary btn-sm" onclick="window.open('http://localhost:8085/last', '_blank')">
                    View API
                </button>
            </div>
            
            <hr>
            
            <div class="input-group">
                <input type="text" id="agentCommandInput" class="form-control" placeholder="Enter trading command..." 
                       value="Build an iron condor on SPY with 7 DTE">
                <div class="input-group-append">
                    <button class="btn btn-primary" onclick="testAgentCommand(document.getElementById('agentCommandInput').value)">
                        Process Command
                    </button>
                </div>
            </div>
            
            <small class="text-muted mt-2 d-block">
                Try commands like: "Create a covered call on AAPL", "Build protective puts on TSLA"
            </small>
        </div>
    </div>
    
    <script>
    function testAgentCommand(command) {
        if (!command.trim()) {
            alert('Please enter a command');
            return;
        }
        
        fetch('http://localhost:8085/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'text': command,
                'mode': 'text'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Command processed successfully: ' + data.message);
                // Refresh page to show new state
                setTimeout(() => window.location.reload(), 1000);
            } else {
                alert('Command failed: ' + data.message);
            }
        })
        .catch(error => {
            alert('Error: API server may not be running. Start with: python tools/agent_happy_path.py');
            console.error('Error:', error);
        });
    }
    </script>
    """

def inject_agent_cards_to_dashboard():
    """Inject agent cards into the existing dashboard."""
    
    dashboard_file = Path("build_dashboard.py")
    
    if not dashboard_file.exists():
        print("Dashboard file not found - creating agent integration note")
        return
    
    # Read current dashboard
    with open(dashboard_file, 'r') as f:
        dashboard_content = f.read()
    
    # Generate agent cards
    agent_cards = generate_agent_dashboard_cards()
    quick_actions = generate_agent_quick_actions()
    
    print("Agent Dashboard Integration")
    print("=" * 40)
    print("Generated agent cards:")
    print(f"- Agent status card: {'✅' if 'AI Agent Status' in agent_cards else '❌'}")
    print(f"- Last processing card: {'✅' if 'Last AI Processing' in agent_cards else '❌'}")
    print(f"- Quick actions: {'✅' if quick_actions else '❌'}")
    
    # Save as separate file for now
    integration_file = Path("dashboard_with_agent.html")
    
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>EMO Options Bot - Dashboard with AI Agent</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container-fluid mt-3">
            <h1>🤖 EMO Options Bot - AI Agent Dashboard</h1>
            <hr>
            
            {quick_actions}
            {agent_cards}
            
            <div class="alert alert-info">
                <h5>📋 Integration Instructions</h5>
                <p>To integrate with existing dashboard:</p>
                <ol>
                    <li>Start the agent: <code>python tools/agent_happy_path.py</code></li>
                    <li>Verify API: <a href="http://localhost:8085/health" target="_blank">http://localhost:8085/health</a></li>
                    <li>Add agent cards to your dashboard using the functions in <code>dashboard_agent_integration.py</code></li>
                </ol>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    with open(integration_file, 'w') as f:
        f.write(full_html)
    
    print(f"\n📄 Created: {integration_file}")
    print("Open this file in your browser to see the agent dashboard")
    
    return str(integration_file)

if __name__ == "__main__":
    inject_agent_cards_to_dashboard()