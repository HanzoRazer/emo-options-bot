# Enhanced EMO Options Bot - Integrated Pipeline
# Combines data collection, risk management, ML predictions, and dashboard generation

param(
    [string]$Mode = "full",  # full, data-only, ml-only, dashboard-only
    [string]$Symbols = "SPY,QQQ,IWM,DIA,AAPL,MSFT,GOOGL,AMZN,TSLA,NVDA",
    [switch]$SkipDashboard = $false,
    [switch]$Verbose = $false
)

# Configuration
$ProjectRoot = "C:\Users\thepr\Downloads\emo_options_bot_sqlite_plot_upgrade"
$VenvPath = "$ProjectRoot\.venv\Scripts\Activate.ps1"

# Colors for output
function Write-ColoredOutput {
    param([string]$Text, [string]$Color = "White")
    Write-Host $Text -ForegroundColor $Color
}

function Write-Step {
    param([string]$Step)
    Write-ColoredOutput "`n🔄 $Step..." "Cyan"
}

function Write-Success {
    param([string]$Message)
    Write-ColoredOutput "✅ $Message" "Green"
}

function Write-Warning {
    param([string]$Message)
    Write-ColoredOutput "⚠️  $Message" "Yellow"
}

function Write-Error {
    param([string]$Message)
    Write-ColoredOutput "❌ $Message" "Red"
}

# Banner
Write-ColoredOutput @"
██████╗░██████╗░██╗  ███████╗███╗░░██╗██╗░░██╗░█████╗░███╗░░██╗░█████╗░███████╗██████╗░
██╔══██╗██╔══██╗██║  ██╔════╝████╗░██║██║░░██║██╔══██╗████╗░██║██╔══██╗██╔════╝██╔══██╗
██████╔╝██████╦╝██║  █████╗░░██╔██╗██║███████║███████║██╔██╗██║██║░░╚═╝█████╗░░██║░░██║
██╔══██╗██╔══██╗██║  ██╔══╝░░██║╚████║██╔══██║██╔══██║██║╚████║██║░░██╗██╔══╝░░██║░░██║
██████╔╝██████╦╝██║  ███████╗██║░╚███║██║░░██║██║░░██║██║░╚███║╚█████╔╝███████╗██████╔╝
╚═════╝░╚═════╝░╚═╝  ╚══════╝╚═╝░░╚══╝╚═╝░░╚═╝╚═╝░░╚═╝╚═╝░░╚══╝░╚════╝░╚══════╝╚═════╝░

                          ENHANCED EMO OPTIONS BOT
                      Risk Management + ML Integration
"@ "Magenta"

Write-ColoredOutput "Mode: $Mode | Symbols: $($Symbols.Split(',').Count) | Verbose: $Verbose`n" "Gray"

try {
    # 1. Setup Environment
    Write-Step "Setting up environment"
    
    Set-Location $ProjectRoot
    if (Test-Path $VenvPath) {
        & $VenvPath
        Write-Success "Virtual environment activated"
    } else {
        Write-Warning "Virtual environment not found at $VenvPath"
    }
    
    # Set environment variables
    $env:PYTHONPATH = ".\src"
    $env:SYMBOLS = $Symbols
    
    # Check for required API keys
    if (-not $env:ALPACA_KEY_ID -or -not $env:ALPACA_SECRET_KEY) {
        Write-Warning "Alpaca API keys not found. Some features may not work."
        Write-ColoredOutput "Set ALPACA_KEY_ID and ALPACA_SECRET_KEY environment variables" "Yellow"
    } else {
        Write-Success "Alpaca API keys found"
    }
    
    if (-not $env:ALPACA_DATA_URL) {
        $env:ALPACA_DATA_URL = "https://data.alpaca.markets/v2"
    }
    
    # 2. Data Collection (Enhanced)
    if ($Mode -eq "full" -or $Mode -eq "data-only") {
        Write-Step "Running enhanced data collection with risk metrics"
        
        $dataResult = python -m src.database.enhanced_data_collector 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Enhanced data collection completed"
            if ($Verbose) { Write-ColoredOutput $dataResult "Gray" }
        } else {
            Write-Error "Data collection failed: $dataResult"
            throw "Data collection failed"
        }
    }
    
    # 3. Enhanced ML Training
    if ($Mode -eq "full" -or $Mode -eq "ml-only") {
        Write-Step "Running enhanced ML training with risk integration"
        
        $mlResult = python .\scripts\enhanced_retrain.py 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Enhanced ML training completed"
            if ($Verbose) { Write-ColoredOutput $mlResult "Gray" }
        } else {
            Write-Error "ML training failed: $mlResult"
            throw "ML training failed"
        }
    }
    
    # 4. Generate Enhanced Dashboard
    if (($Mode -eq "full" -or $Mode -eq "dashboard-only") -and -not $SkipDashboard) {
        Write-Step "Generating enhanced dashboard"
        
        $dashResult = python -m src.web.enhanced_dashboard 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Enhanced dashboard generated"
            if ($Verbose) { Write-ColoredOutput $dashResult "Gray" }
            
            # Also generate standard dashboard for comparison
            python -m src.web.dashboard 2>&1 | Out-Null
        } else {
            Write-Error "Dashboard generation failed: $dashResult"
            throw "Dashboard generation failed"
        }
    }
    
    # 5. Risk Assessment Summary
    Write-Step "Generating risk assessment summary"
    
    $riskSummaryPath = "$ProjectRoot\data\risk_summary.json"
    if (Test-Path $riskSummaryPath) {
        $riskData = Get-Content $riskSummaryPath | ConvertFrom-Json
        
        Write-ColoredOutput "`n📊 RISK ASSESSMENT SUMMARY" "Cyan"
        Write-ColoredOutput "================================" "Cyan"
        
        $portfolio = $riskData.portfolio
        $riskStatus = $riskData.risk_status
        $marketRegime = $riskData.market_regime
        
        # Portfolio metrics
        Write-ColoredOutput "Portfolio Heat: $([math]::Round($portfolio.heat_pct, 1))%" $(if ($portfolio.heat_pct -gt 20) { "Red" } elseif ($portfolio.heat_pct -gt 15) { "Yellow" } else { "Green" })
        Write-ColoredOutput "Beta Exposure: $([math]::Round($portfolio.beta_exposure, 2))" $(if ([math]::Abs($portfolio.beta_exposure) -gt 1.4) { "Red" } elseif ([math]::Abs($portfolio.beta_exposure) -gt 1.2) { "Yellow" } else { "Green" })
        Write-ColoredOutput "Positions: $($portfolio.num_positions)/5" "White"
        Write-ColoredOutput "Total Risk: $([math]::Round($portfolio.total_risk, 0))" "White"
        Write-ColoredOutput "Available Cash: $([math]::Round($portfolio.cash, 0))" "White"
        
        # Risk status
        $statusColor = switch ($riskStatus.overall_status) {
            "healthy" { "Green" }
            "warning" { "Yellow" }
            "violation" { "Red" }
            default { "White" }
        }
        Write-ColoredOutput "Overall Status: $($riskStatus.overall_status.ToUpper())" $statusColor
        
        # Market regime
        if ($marketRegime) {
            Write-ColoredOutput "Market Regime: $($marketRegime.regime.ToUpper())" "Cyan"
            Write-ColoredOutput "VIX Level: $([math]::Round($marketRegime.vix_level, 1))%" $(if ($marketRegime.vix_level -gt 25) { "Red" } elseif ($marketRegime.vix_level -gt 15) { "Yellow" } else { "Green" })
        }
        
        # Violations and warnings
        if ($riskStatus.violations -and $riskStatus.violations.Count -gt 0) {
            Write-ColoredOutput "`n⚠️  VIOLATIONS:" "Red"
            foreach ($violation in $riskStatus.violations) {
                Write-ColoredOutput "   • $violation" "Red"
            }
        }
        
        if ($riskStatus.warnings -and $riskStatus.warnings.Count -gt 0) {
            Write-ColoredOutput "`n⚡ WARNINGS:" "Yellow"
            foreach ($warning in $riskStatus.warnings) {
                Write-ColoredOutput "   • $warning" "Yellow"
            }
        }
    }
    
    # 6. ML Predictions Summary
    $mlOutlookPath = "$ProjectRoot\data\ml_outlook.json"
    if (Test-Path $mlOutlookPath) {
        $mlData = Get-Content $mlOutlookPath | ConvertFrom-Json
        
        Write-ColoredOutput "`n🧠 ML PREDICTIONS SUMMARY" "Cyan"
        Write-ColoredOutput "===========================" "Cyan"
        
        if ($mlData.trading_opportunities -and $mlData.trading_opportunities.Count -gt 0) {
            Write-ColoredOutput "Top Trading Opportunities:" "White"
            $topOpps = $mlData.trading_opportunities | Select-Object -First 5
            foreach ($opp in $topOpps) {
                $actionColor = switch ($opp.action) {
                    "consider_entry" { "Green" }
                    "consider_exit" { "Red" }
                    "hold_strong" { "Blue" }
                    default { "White" }
                }
                Write-ColoredOutput "   $($opp.symbol): $($opp.action.ToUpper()) (Priority: $($opp.priority), Conf: $([math]::Round($opp.confidence, 3)))" $actionColor
            }
        }
        
        # Strong predictions
        $strongPreds = $mlData.predictions | Where-Object { $_.confidence -gt 0.7 }
        if ($strongPreds.Count -gt 0) {
            Write-ColoredOutput "`nStrong Predictions (>70% confidence):" "White"
            foreach ($pred in $strongPreds) {
                $dirColor = if ($pred.direction -eq "up") { "Green" } elseif ($pred.direction -eq "down") { "Red" } else { "Yellow" }
                Write-ColoredOutput "   $($pred.symbol): $($pred.direction.ToUpper()) ($([math]::Round($pred.confidence * 100, 1))%)" $dirColor
            }
        }
    }
    
    # 7. Open Dashboards
    if (($Mode -eq "full" -or $Mode -eq "dashboard-only") -and -not $SkipDashboard) {
        Write-Step "Opening dashboards"
        
        $enhancedDashboard = "$ProjectRoot\enhanced_dashboard.html"
        $standardDashboard = "$ProjectRoot\dashboard.html"
        
        if (Test-Path $enhancedDashboard) {
            Start-Process $enhancedDashboard
            Write-Success "Enhanced dashboard opened"
        }
        
        if (Test-Path $standardDashboard) {
            Start-Process $standardDashboard
            Write-Success "Standard dashboard opened"
        }
    }
    
    Write-ColoredOutput "`n🎉 ENHANCED EMO PIPELINE COMPLETED SUCCESSFULLY!" "Green"
    Write-ColoredOutput "Features integrated: Risk Management, Enhanced ML, Market Regime Detection" "Gray"
    
} catch {
    Write-Error "Pipeline failed: $($_.Exception.Message)"
    exit 1
}

# Usage information
Write-ColoredOutput "`n📖 USAGE EXAMPLES:" "Cyan"
Write-ColoredOutput "Full pipeline:       .\enhanced_pipeline.ps1" "Gray"
Write-ColoredOutput "Data only:           .\enhanced_pipeline.ps1 -Mode data-only" "Gray"
Write-ColoredOutput "ML only:             .\enhanced_pipeline.ps1 -Mode ml-only" "Gray"
Write-ColoredOutput "Dashboard only:      .\enhanced_pipeline.ps1 -Mode dashboard-only" "Gray"
Write-ColoredOutput "Custom symbols:      .\enhanced_pipeline.ps1 -Symbols 'AAPL,MSFT,GOOGL'" "Gray"
Write-ColoredOutput "Verbose output:      .\enhanced_pipeline.ps1 -Verbose" "Gray"