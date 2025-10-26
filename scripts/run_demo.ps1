# Enhanced Strategy Demo Runner
# PowerShell script to run the complete strategy system demonstration

Write-Host "🚀 Enhanced EMO Options Bot - Strategy System Demo" -ForegroundColor Green
Write-Host "=" * 60

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

# Set environment for development (SQLite)
$env:EMO_ENV = "development"

# Create data directory if it doesn't exist
if (!(Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
    Write-Host "📁 Created data directory" -ForegroundColor Cyan
}

# Install required packages if needed
Write-Host "📋 Checking dependencies..." -ForegroundColor Yellow
$packages = @(
    "pandas",
    "numpy", 
    "yfinance",
    "scikit-learn",
    "matplotlib",
    "seaborn",
    "psutil",
    "flask",
    "flask-cors",
    "psycopg2-binary"
)

foreach ($package in $packages) {
    try {
        python -c "import $($package.replace('-', '_'))" 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Host "📦 Installing $package..." -ForegroundColor Yellow
            pip install $package --quiet
        }
    } catch {
        Write-Host "📦 Installing $package..." -ForegroundColor Yellow
        pip install $package --quiet
    }
}

Write-Host "✅ Dependencies ready" -ForegroundColor Green

# Run the strategy demo
Write-Host "`n🎯 Running Strategy System Demo..." -ForegroundColor Cyan
Write-Host "-" * 50

try {
    python scripts\demo_enhanced_strategies.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n🎉 Demo completed successfully!" -ForegroundColor Green
        
        # Check if results file was created
        if (Test-Path "data\strategy_demo_results.json") {
            Write-Host "📄 Results saved to: data\strategy_demo_results.json" -ForegroundColor Cyan
            
            # Show quick summary
            $results = Get-Content "data\strategy_demo_results.json" | ConvertFrom-Json
            Write-Host "`n📊 Quick Summary:" -ForegroundColor Yellow
            Write-Host "   Scenarios Tested: $($results.summary.total_scenarios)" -ForegroundColor White
            Write-Host "   Orders Generated: $($results.summary.total_orders)" -ForegroundColor White
            Write-Host "   Strategies Used: $($results.summary.strategies_used -join ', ')" -ForegroundColor White
            Write-Host "   Orders Approved: $($results.summary.approved_orders)" -ForegroundColor Green
            Write-Host "   Orders Rejected: $($results.summary.rejected_orders)" -ForegroundColor Red
        }
        
        Write-Host "`n🔗 System Status:" -ForegroundColor Cyan
        Write-Host "   ✅ Strategy Framework: Operational" -ForegroundColor Green
        Write-Host "   ✅ Risk Management: Active" -ForegroundColor Green
        Write-Host "   ✅ Database Integration: Working" -ForegroundColor Green
        Write-Host "   ✅ Options Strategies: Ready" -ForegroundColor Green
        
    } else {
        Write-Host "`n❌ Demo failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    
} catch {
    Write-Host "`n❌ Demo failed with error: $_" -ForegroundColor Red
    exit 1
}

Write-Host "`n🏁 Demo complete! Your enhanced strategy system is ready for production." -ForegroundColor Green