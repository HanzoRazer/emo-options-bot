# Dashboard Quick Start Guide

## Overview
The Enhanced Dashboard system provides comprehensive monitoring and visualization for the EMO Options Bot, integrating ML outlook, market data, system health, and portfolio analytics.

## Features
- **Real-time System Health**: Database status, data freshness, ML model performance
- **ML Outlook Panel**: Live predictions from ensemble models with confidence scores
- **Portfolio Summary**: Orders, risk violations, execution statistics
- **Market Data Visualization**: Charts and real-time price data
- **Automated Alerts**: System warnings and notifications
- **Responsive Design**: Works on desktop and mobile devices

## Quick Start

### 1. Install Dependencies (Optional for FastAPI mode)
```powershell
pip install fastapi uvicorn jinja2
```

### 2. Generate Static Dashboard (Recommended)
```powershell
# Generate current dashboard
python dashboard\enhanced_dashboard.py --mode generate

# Open the dashboard
start dashboard.html
```

### 3. Run Live Dashboard Server (If FastAPI available)
```powershell
# Start dashboard server
python dashboard\enhanced_dashboard.py --mode serve --host 127.0.0.1 --port 8000

# Open in browser: http://127.0.0.1:8000
```

### 4. Export Dashboard Data
```powershell
# Export all data for dashboard
python dashboard\integration.py --export all

# Export specific components
python dashboard\integration.py --export ml
python dashboard\integration.py --export market --symbols SPY QQQ --hours 48
python dashboard\integration.py --export alerts
```

## File Structure
```
dashboard/
├── enhanced_dashboard.py      # Main dashboard application
├── integration.py            # Data export and integration utilities
├── templates/
│   └── dashboard.html        # Dashboard HTML template
├── static/                   # Static assets (auto-created)
└── README.md                # This file
```

## Dashboard Components

### 1. System Health Panel
- Overall system status (Healthy/Warning/Error)
- Health score percentage
- Component-level status:
  - Database connectivity
  - Data ingestion freshness
  - ML outlook availability

### 2. ML Outlook Panel
- Current ensemble signal and confidence
- Individual model predictions
- Market summary and recommendation
- Last update timestamp

### 3. Portfolio Summary
- Order statistics (total, pending, executed)
- Risk violation counts
- Database metrics (size, tables, status)

### 4. ML Performance Panel
- Model prediction counts
- Average confidence scores
- Per-model performance breakdown

## API Endpoints (FastAPI Mode)
- `GET /` - Main dashboard page
- `GET /api/system-health` - System health status
- `GET /api/ml-outlook` - ML predictions and outlook
- `GET /api/portfolio-summary` - Portfolio and trading statistics
- `GET /api/market-data/{symbol}` - Market data for charts
- `GET /api/ml-performance` - ML model performance metrics
- `WebSocket /ws` - Real-time updates

## Configuration

### Environment Variables
- `EMO_DB_MODE`: Set to `sqlite` or `timescale` (default: sqlite)
- `EMO_DB_URL`: Database connection string
- `DASHBOARD_HOST`: Dashboard server host (default: 127.0.0.1)
- `DASHBOARD_PORT`: Dashboard server port (default: 8000)

### Data Export Configuration
Edit `dashboard/integration.py` to customize:
- Export symbols and timeframes
- Alert thresholds and rules
- Data retention policies

## Automation Integration

### 1. Add to Weekly Retrain Task
```powershell
# Modify scripts/setup_weekly_task.ps1 to include dashboard export
$Action = New-ScheduledTaskAction -Execute "python" -Argument "dashboard/integration.py --export all"
```

### 2. Standalone Dashboard Update Task
```powershell
# Create dashboard update task (every 30 minutes)
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 30)
$Action = New-ScheduledTaskAction -Execute "python" -Argument "dashboard/integration.py --export all"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "EMO-Dashboard-Update" -Trigger $Trigger -Action $Action -Settings $Settings
```

## Troubleshooting

### Dashboard Shows "Loading..."
1. Check if data files exist in `data/` directory
2. Run: `python dashboard/integration.py --export all`
3. Verify database connectivity

### FastAPI Server Won't Start
1. Install dependencies: `pip install fastapi uvicorn jinja2`
2. Check if port 8000 is available
3. Try different port: `--port 8080`

### No ML Outlook Data
1. Run ML outlook generation: `python scripts/ml/enhanced_ml_outlook.py --export`
2. Check ML model files exist
3. Verify database has sufficient market data

### Stale Data Warnings
1. Run data ingestion: `python scripts/ingestion/enhanced_ingestion.py`
2. Check Alpaca API connectivity
3. Verify database write permissions

### Database Connection Errors
1. Check database service is running
2. Verify connection string in config
3. Run: `python src/database/enhanced_router.py` to test

## Advanced Usage

### Custom Symbols and Timeframes
```powershell
# Export specific symbols with extended timeframe
python dashboard\integration.py --export market --symbols SPY QQQ IWM TSLA --hours 72
```

### Automated Static Generation
```powershell
# Create automated dashboard generation script
@echo off
cd /d "C:\Users\thepr\Downloads\emo_options_bot_sqlite_plot_upgrade"
python dashboard\integration.py --export all
python dashboard\enhanced_dashboard.py --mode generate --output public\dashboard.html
echo Dashboard updated at %date% %time%
```

### Dashboard Customization
1. Edit `dashboard/templates/dashboard.html` for layout changes
2. Modify `dashboard/enhanced_dashboard.py` for new API endpoints
3. Update `dashboard/integration.py` for additional data exports

## Production Deployment

### 1. Static Dashboard (Recommended)
- Generate dashboard HTML files
- Serve via web server (IIS, Apache, nginx)
- Update via scheduled tasks

### 2. FastAPI Server
- Use production ASGI server (gunicorn, uvicorn)
- Configure reverse proxy
- Set up monitoring and logging

### 3. Security Considerations
- Restrict dashboard access to internal networks
- Use authentication for sensitive data
- Regular security updates

## Support and Maintenance

### Regular Tasks
1. Clean up old export files: `python dashboard/integration.py --cleanup`
2. Monitor dashboard performance and responsiveness
3. Update alert thresholds based on system behavior
4. Review and optimize data export schedules

### Monitoring
- Check dashboard update frequency
- Monitor API response times
- Verify data freshness alerts
- Review system health trends

## Integration with Phase 3 Components
The dashboard automatically integrates with:
- **Database Router**: Multi-database support (SQLite/Timescale)
- **ML Outlook Engine**: Ensemble predictions and model management
- **Risk Management**: Violation tracking and alerts
- **Order Management**: Staging and execution monitoring
- **Data Ingestion**: Market data freshness and quality

For additional customization or support, refer to the main EMO documentation or contact the development team.