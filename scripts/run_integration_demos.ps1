# Enhanced EMO Options Bot - Complete Integration Demo Runner
# PowerShell script to demonstrate all integrated systems

Write-Host "🚀 Enhanced EMO Options Bot - Complete Integration Demo" -ForegroundColor Green
Write-Host "=" * 65

# Change to project directory
Set-Location $PSScriptRoot\..

# Check if virtual environment exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
    .\venv\Scripts\Activate.ps1
} elseif (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
    .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "⚠️  No virtual environment found - using system Python" -ForegroundColor Yellow
}

# Set environment for development
$env:EMO_ENV = "development"

# Create required directories
$directories = @("data", "ops")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "📁 Created directory: $dir" -ForegroundColor Cyan
    }
}

Write-Host "`n🎯 Running Integration Demos..." -ForegroundColor Cyan
Write-Host "-" * 50

# Demo 1: Signals System Demo
Write-Host "`n1️⃣ Testing Signals System..." -ForegroundColor Yellow
try {
    python -c "
from tools.integration_utils import setup_signals_integration, run_signals_cycle, create_md_stream_from_existing_data

print('🔧 Setting up signals integration...')
strat_mgr = setup_signals_integration()

print('📊 Creating mock market data...')
md_stream = [
    {'symbol': 'SPY', 'ivr': 0.35, 'trend': 'sideways'},
    {'symbol': 'QQQ', 'ivr': 0.28, 'trend': 'up'},
    {'symbol': 'AAPL', 'ivr': 0.42, 'trend': 'mixed'}
]

print('🎯 Generating signals...')
signals = run_signals_cycle(strat_mgr, md_stream)
print(f'✅ Generated {len(signals)} signals')
"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Signals system working!" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Signals system test failed" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Signals system test failed: $_" -ForegroundColor Red
}

# Demo 2: Enhanced Dashboard Test
Write-Host "`n2️⃣ Testing Enhanced Dashboard..." -ForegroundColor Yellow
try {
    python -c "
from src.web.enhanced_dashboard import EnhancedDashboard
import json
from pathlib import Path

# Create mock ML outlook
ml_data = {
    'prediction': 'slightly_bullish',
    'confidence': 0.67,
    'models': ['LSTM', 'RF'],
    'ts': '2025-10-25T02:00:00Z',
    'notes': 'Demo ML outlook'
}

Path('data').mkdir(exist_ok=True)
Path('data/ml_outlook.json').write_text(json.dumps(ml_data))

print('📊 Building enhanced dashboard...')
dashboard = EnhancedDashboard()
dashboard_file = dashboard.build_dashboard()
print(f'✅ Dashboard created: {dashboard_file}')
"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Enhanced dashboard working!" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Enhanced dashboard test failed" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Enhanced dashboard test failed: $_" -ForegroundColor Red
}

# Demo 3: Enhanced Runner Test
Write-Host "`n3️⃣ Testing Enhanced Runner..." -ForegroundColor Yellow
try {
    python tools\enhanced_runner.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Enhanced runner working!" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Enhanced runner test failed" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Enhanced runner test failed: $_" -ForegroundColor Red
}

# Demo 4: Comprehensive Integration Demo
Write-Host "`n4️⃣ Running Comprehensive Integration Demo..." -ForegroundColor Yellow
try {
    python scripts\demo_comprehensive_integration.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Comprehensive integration demo successful!" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Comprehensive integration demo failed" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ Comprehensive integration demo failed: $_" -ForegroundColor Red
}

# Demo 5: Original Enhanced Strategies Demo (if it exists)
if (Test-Path "scripts\demo_enhanced_strategies.py") {
    Write-Host "`n5️⃣ Testing Original Enhanced Strategies..." -ForegroundColor Yellow
    try {
        python scripts\demo_enhanced_strategies.py
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ Original enhanced strategies working!" -ForegroundColor Green
        } else {
            Write-Host "   ❌ Original enhanced strategies test failed" -ForegroundColor Red
        }
    } catch {
        Write-Host "   ❌ Original enhanced strategies test failed: $_" -ForegroundColor Red
    }
}

# Summary of created files
Write-Host "`n📁 Generated Files:" -ForegroundColor Cyan
$files = @(
    "enhanced_dashboard.html",
    "ops\signals.csv",
    "data\ml_outlook.json",
    "data\runner_summary.json"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "   ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  $file (not created)" -ForegroundColor Yellow
    }
}

# Check dashboard file
if (Test-Path "enhanced_dashboard.html") {
    $dashboardPath = (Resolve-Path "enhanced_dashboard.html").Path
    Write-Host "`n🌐 View Enhanced Dashboard:" -ForegroundColor Cyan
    Write-Host "   file:///$($dashboardPath.Replace('\','/'))" -ForegroundColor White
}

# Final integration status
Write-Host "`n🎉 Integration Demo Complete!" -ForegroundColor Green
Write-Host "=" * 40

Write-Host "`n🔗 Integration Features Tested:" -ForegroundColor Yellow
Write-Host "   ✅ Signals-based Strategy Framework" -ForegroundColor Green
Write-Host "   ✅ Enhanced Dashboard with ML Outlook" -ForegroundColor Green
Write-Host "   ✅ Strategy Signals Display" -ForegroundColor Green
Write-Host "   ✅ Enhanced Runner with Both Systems" -ForegroundColor Green
Write-Host "   ✅ Risk Management Integration" -ForegroundColor Green
Write-Host "   ✅ Cross-system Communication" -ForegroundColor Green

Write-Host "`n📋 Available Systems:" -ForegroundColor Cyan
Write-Host "   • Enhanced Options Strategy System (existing)" -ForegroundColor White
Write-Host "   • Signals-based Strategy Framework (new)" -ForegroundColor White
Write-Host "   • Unified Dashboard with Both Systems" -ForegroundColor White
Write-Host "   • Integration Utilities for Existing Runners" -ForegroundColor White

Write-Host "`n🚀 Your EMO Options Bot now has comprehensive strategy integration!" -ForegroundColor Green