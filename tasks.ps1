# PowerShell Tasks for EMO Options Bot
# Convenience functions for Windows development workflow
# Usage: Import-Module .\tasks.ps1; Setup-Project

# ============================================================================
# Helper Functions
# ============================================================================

function Get-PythonExe {
    if (Test-Path ".\.venv\Scripts\python.exe") { 
        return ".\.venv\Scripts\python.exe" 
    }
    if (Get-Command python -ErrorAction SilentlyContinue) { 
        return "python" 
    }
    if (Get-Command py -ErrorAction SilentlyContinue) { 
        return "py" 
    }
    throw "Python not found. Please install Python or activate virtual environment."
}

function Ensure-VirtualEnv {
    if (-not (Test-Path ".\.venv")) {
        Write-Host "Creating virtual environment..." -ForegroundColor Cyan
        $python = Get-Command python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
        if (-not $python) {
            $python = Get-Command py -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
        }
        if (-not $python) {
            throw "Python not found. Please install Python first."
        }
        & $python -m venv .venv
        Write-Host "Virtual environment created." -ForegroundColor Green
    }
}

function Activate-VirtualEnv {
    Ensure-VirtualEnv
    $activateScript = ".\.venv\Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
        Write-Host "Virtual environment activated." -ForegroundColor Green
    } else {
        Write-Warning "Could not find activation script at $activateScript"
    }
}

function Set-EnvironmentVariable {
    param(
        [string]$Name, 
        [string]$Value, 
        [switch]$Persist
    )
    
    if ($Persist) {
        [Environment]::SetEnvironmentVariable($Name, $Value, "User")
        Write-Host "Environment variable $Name set persistently." -ForegroundColor Green
    } else {
        $env:$Name = $Value
        Write-Host "Environment variable $Name set for current session." -ForegroundColor Yellow
    }
}

function Test-ServicePort {
    param([int]$Port)
    
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue
        return $connection.TcpTestSucceeded
    } catch {
        return $false
    }
}

function Wait-ForService {
    param(
        [int]$Port,
        [int]$TimeoutSeconds = 30,
        [string]$ServiceName = "Service"
    )
    
    Write-Host "Waiting for $ServiceName on port $Port..." -ForegroundColor Cyan
    
    $elapsed = 0
    while ($elapsed -lt $TimeoutSeconds) {
        if (Test-ServicePort -Port $Port) {
            Write-Host "$ServiceName is ready on port $Port" -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds 1
        $elapsed++
    }
    
    Write-Warning "$ServiceName failed to start on port $Port within $TimeoutSeconds seconds"
    return $false
}

# ============================================================================
# Environment & Setup Functions
# ============================================================================

function Setup-Project {
    <#
    .SYNOPSIS
    Complete project setup including venv, dependencies, and database
    #>
    
    Write-Host "=== EMO Options Bot - Project Setup ===" -ForegroundColor Cyan
    
    try {
        # Ensure virtual environment
        Ensure-VirtualEnv
        
        # Install dependencies
        Install-Dependencies
        
        # Initialize database
        Initialize-Database
        
        # Validate configuration
        Test-Configuration
        
        Write-Host "✅ Project setup completed successfully!" -ForegroundColor Green
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "  1. Copy .env.example to .env and configure" -ForegroundColor White
        Write-Host "  2. Run: Start-EMO" -ForegroundColor White
        
    } catch {
        Write-Error "Setup failed: $_"
        throw
    }
}

function Install-Dependencies {
    <#
    .SYNOPSIS
    Install Python dependencies based on available requirements files
    #>
    
    Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
    
    $python = Get-PythonExe
    
    # Upgrade pip first
    & $python -m pip install --upgrade pip | Out-Null
    
    # Install from requirements files in priority order
    $reqFiles = @(
        "requirements.txt",
        "requirements_simple_agent.txt",
        "requirements_ai_agent.txt"
    )
    
    $installed = $false
    foreach ($reqFile in $reqFiles) {
        if (Test-Path $reqFile) {
            Write-Host "Installing from $reqFile..." -ForegroundColor Yellow
            & $python -m pip install -r $reqFile
            $installed = $true
            break
        }
    }
    
    if (-not $installed) {
        Write-Host "No requirements file found, installing base dependencies..." -ForegroundColor Yellow
        $baseDeps = @(
            "pandas>=1.5.0",
            "numpy>=1.20.0",
            "matplotlib>=3.5.0",
            "requests>=2.28.0",
            "python-dotenv>=0.19.0",
            "sqlalchemy>=1.4.0"
        )
        & $python -m pip install $baseDeps
    }
    
    Write-Host "Dependencies installed successfully." -ForegroundColor Green
}

function Initialize-Database {
    <#
    .SYNOPSIS
    Initialize SQLite database and run migrations
    #>
    
    Write-Host "Initializing database..." -ForegroundColor Cyan
    
    # Create data directory
    if (-not (Test-Path "data")) {
        New-Item -ItemType Directory -Path "data" -Force | Out-Null
        Write-Host "Created data directory." -ForegroundColor Green
    }
    
    # Initialize SQLite database
    $sqlitePath = "data\emo.sqlite"
    if (-not (Test-Path $sqlitePath)) {
        New-Item -ItemType File -Path $sqlitePath -Force | Out-Null
        Write-Host "Created SQLite database: $sqlitePath" -ForegroundColor Green
    }
    
    # Run migrations if available
    $python = Get-PythonExe
    $migrationScript = "scripts\migration\migrate_sqlite.py"
    if (Test-Path $migrationScript) {
        Write-Host "Running database migrations..." -ForegroundColor Yellow
        & $python $migrationScript
    }
    
    Write-Host "Database initialized successfully." -ForegroundColor Green
}

function Load-Environment {
    <#
    .SYNOPSIS
    Load environment variables from .env files
    .PARAMETER Environment
    Environment name (development, staging, production)
    #>
    param([string]$Environment = "development")
    
    # Environment file priority
    $envFiles = @(
        ".env.$Environment",
        ".env.local", 
        ".env"
    )
    
    $loaded = @()
    
    foreach ($envFile in $envFiles) {
        if (Test-Path $envFile) {
            Write-Host "Loading environment from: $envFile" -ForegroundColor Cyan
            
            Get-Content $envFile | ForEach-Object {
                if ($_ -match "^\s*#" -or $_ -match "^\s*$") {
                    return
                }
                
                if ($_ -match "^([^=]+)=(.*)$") {
                    $key = $matches[1].Trim()
                    $value = $matches[2].Trim()
                    
                    # Remove quotes
                    if ($value -match '^"(.*)"$') {
                        $value = $matches[1]
                    }
                    
                    Set-EnvironmentVariable -Name $key -Value $value
                }
            }
            
            $loaded += $envFile
        }
    }
    
    # Set EMO_ENV if not set
    if (-not $env:EMO_ENV) {
        Set-EnvironmentVariable -Name "EMO_ENV" -Value $Environment
    }
    
    if ($loaded.Count -gt 0) {
        Write-Host "Loaded configuration from: $($loaded -join ', ')" -ForegroundColor Green
    } else {
        Write-Warning "No environment files found. Using defaults."
    }
    
    return $loaded
}

function Show-Environment {
    <#
    .SYNOPSIS
    Display current environment configuration
    #>
    
    Write-Host "=== Current Environment Configuration ===" -ForegroundColor Cyan
    
    $envVars = @(
        "EMO_ENV",
        "EMO_DB_BACKEND", 
        "EMO_BROKER",
        "EMO_STAGE_ORDERS",
        "EMO_LIVE_DATA",
        "ALPACA_KEY_ID",
        "ALPACA_API_BASE",
        "EMO_HEALTH_PORT",
        "EMO_DASHBOARD_PORT"
    )
    
    foreach ($var in $envVars) {
        $value = [Environment]::GetEnvironmentVariable($var)
        if ($value) {
            # Mask sensitive values
            if ($var -like "*KEY*" -or $var -like "*SECRET*" -or $var -like "*PASSWORD*") {
                $displayValue = $value.Substring(0, [Math]::Min(4, $value.Length)) + "***"
            } else {
                $displayValue = $value
            }
            Write-Host "  $var = $displayValue" -ForegroundColor White
        } else {
            Write-Host "  $var = (not set)" -ForegroundColor Gray
        }
    }
}

# ============================================================================
# Database Functions
# ============================================================================

function Initialize-SQLiteDB {
    <#
    .SYNOPSIS
    Initialize SQLite database with schema
    #>
    
    Initialize-Database
}

function Initialize-TimescaleDB {
    <#
    .SYNOPSIS
    Initialize TimescaleDB with migrations
    #>
    
    Write-Host "Initializing TimescaleDB..." -ForegroundColor Cyan
    
    $python = Get-PythonExe
    $migrationScript = "scripts\migration\migrate_timescale.py"
    
    if (Test-Path $migrationScript) {
        & $python $migrationScript
        if ($LASTEXITCODE -eq 0) {
            Write-Host "TimescaleDB initialized successfully." -ForegroundColor Green
        } else {
            Write-Error "TimescaleDB initialization failed."
        }
    } else {
        Write-Error "TimescaleDB migration script not found: $migrationScript"
    }
}

function Reset-Database {
    <#
    .SYNOPSIS
    Reset database (WARNING: destroys all data)
    #>
    
    $confirmation = Read-Host "This will destroy all data. Type 'YES' to confirm"
    if ($confirmation -ne "YES") {
        Write-Host "Operation cancelled." -ForegroundColor Yellow
        return
    }
    
    Write-Host "Resetting database..." -ForegroundColor Red
    
    # Remove SQLite files
    $sqliteFiles = @("data\emo.sqlite", "data\describer.db")
    foreach ($file in $sqliteFiles) {
        if (Test-Path $file) {
            Remove-Item $file -Force
            Write-Host "Removed: $file" -ForegroundColor Yellow
        }
    }
    
    # Reinitialize
    Initialize-Database
    
    Write-Host "Database reset completed." -ForegroundColor Green
}

# ============================================================================
# Application Control Functions  
# ============================================================================

function Start-EMO {
    <#
    .SYNOPSIS
    Start the EMO Options Bot with all services
    .PARAMETER Environment
    Environment to run in (development, staging, production)
    .PARAMETER SkipServices
    Skip starting background services
    #>
    param(
        [string]$Environment = "development",
        [switch]$SkipServices
    )
    
    Write-Host "=== Starting EMO Options Bot ===" -ForegroundColor Cyan
    
    # Load environment
    Load-Environment -Environment $Environment
    
    # Validate configuration
    if (-not (Test-Configuration -Quiet)) {
        Write-Error "Configuration validation failed. Fix issues and try again."
        return
    }
    
    $jobs = @()
    
    try {
        if (-not $SkipServices) {
            # Start health service
            if ($env:EMO_HEALTH_ENABLE -eq "1") {
                $jobs += Start-HealthService
            }
            
            # Start dashboard service  
            if ($env:EMO_DASHBOARD_ENABLE -eq "1") {
                $jobs += Start-Dashboard
            }
        }
        
        # Start main application
        Start-MainApplication
        
    } finally {
        # Cleanup background jobs
        if ($jobs.Count -gt 0) {
            Write-Host "Stopping background services..." -ForegroundColor Yellow
            $jobs | ForEach-Object { 
                if ($_.State -eq "Running") {
                    Stop-Job $_ 
                    Remove-Job $_
                }
            }
        }
    }
}

function Start-HealthService {
    <#
    .SYNOPSIS
    Start health monitoring service in background
    #>
    
    $healthScript = "scripts\services\health_service.py"
    if (-not (Test-Path $healthScript)) {
        Write-Warning "Health service script not found: $healthScript"
        return $null
    }
    
    $port = $env:EMO_HEALTH_PORT
    if (-not $port) { $port = "8082" }
    
    Write-Host "Starting health service on port $port..." -ForegroundColor Cyan
    
    $job = Start-Job -ScriptBlock {
        param($Script, $Port, $Python)
        & $Python $Script --port $Port
    } -ArgumentList $healthScript, $port, (Get-PythonExe)
    
    # Wait for service to start
    if (Wait-ForService -Port $port -ServiceName "Health Service" -TimeoutSeconds 10) {
        Write-Host "Health service URL: http://localhost:$port/health" -ForegroundColor Green
    }
    
    return $job
}

function Start-Dashboard {
    <#
    .SYNOPSIS
    Start dashboard service in background
    .PARAMETER Mode
    Dashboard mode (serve or generate)
    #>
    param([string]$Mode = "serve")
    
    $dashboardScript = "dashboard\enhanced_dashboard.py"
    if (-not (Test-Path $dashboardScript)) {
        Write-Warning "Dashboard script not found: $dashboardScript"
        return $null
    }
    
    $port = $env:EMO_DASHBOARD_PORT
    if (-not $port) { $port = "8083" }
    
    if ($Mode -eq "generate") {
        Write-Host "Generating static dashboard..." -ForegroundColor Cyan
        $python = Get-PythonExe
        & $python $dashboardScript --mode generate
        
        if (Test-Path "dashboard.html") {
            Write-Host "Static dashboard generated: dashboard.html" -ForegroundColor Green
            Start-Process "dashboard.html"
        }
        return $null
    } else {
        Write-Host "Starting dashboard service on port $port..." -ForegroundColor Cyan
        
        $job = Start-Job -ScriptBlock {
            param($Script, $Port, $Python)
            & $Python $Script --mode serve --port $Port
        } -ArgumentList $dashboardScript, $port, (Get-PythonExe)
        
        # Wait for service to start
        if (Wait-ForService -Port $port -ServiceName "Dashboard" -TimeoutSeconds 15) {
            Write-Host "Dashboard URL: http://localhost:$port" -ForegroundColor Green
        }
        
        return $job
    }
}

function Start-MainApplication {
    <#
    .SYNOPSIS
    Start the main EMO application
    #>
    
    $python = Get-PythonExe
    
    # Find main entry point
    $mainScripts = @(
        "main.py",
        "scripts\automation\enhanced_runner.py",
        "scripts\runner\main_runner.py"
    )
    
    $mainScript = $null
    foreach ($script in $mainScripts) {
        if (Test-Path $script) {
            $mainScript = $script
            break
        }
    }
    
    if (-not $mainScript) {
        Write-Error "No main application script found. Expected one of: $($mainScripts -join ', ')"
        return
    }
    
    Write-Host "Starting main application: $mainScript" -ForegroundColor Cyan
    & $python $mainScript
}

function Stop-EMO {
    <#
    .SYNOPSIS
    Stop all EMO services and jobs
    #>
    
    Write-Host "Stopping EMO services..." -ForegroundColor Yellow
    
    # Stop PowerShell jobs
    Get-Job | Where-Object { $_.Name -like "*EMO*" -or $_.Name -like "*Health*" -or $_.Name -like "*Dashboard*" } | ForEach-Object {
        Stop-Job $_
        Remove-Job $_
        Write-Host "Stopped job: $($_.Name)" -ForegroundColor Yellow
    }
    
    # Stop processes on known ports
    $ports = @(8082, 8083)
    foreach ($port in $ports) {
        $processes = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | 
                     Select-Object -ExpandProperty OwningProcess | 
                     Get-Process -Id $_ -ErrorAction SilentlyContinue
        
        $processes | ForEach-Object {
            Write-Host "Stopping process on port $port : $($_.ProcessName)" -ForegroundColor Yellow
            Stop-Process -Id $_.Id -Force
        }
    }
    
    Write-Host "EMO services stopped." -ForegroundColor Green
}

# ============================================================================
# ML and Data Functions
# ============================================================================

function Train-MLModels {
    <#
    .SYNOPSIS
    Train ML models for specified symbol
    .PARAMETER Symbol
    Stock symbol to train models for
    #>
    param([string]$Symbol = "SPY")
    
    Write-Host "Training ML models for $Symbol..." -ForegroundColor Cyan
    
    $python = Get-PythonExe
    $mlScript = "scripts\ml\enhanced_ml_outlook.py"
    
    if (Test-Path $mlScript) {
        & $python $mlScript --train --symbol $Symbol
        if ($LASTEXITCODE -eq 0) {
            Write-Host "ML models trained successfully for $Symbol." -ForegroundColor Green
        } else {
            Write-Error "ML model training failed for $Symbol."
        }
    } else {
        Write-Error "ML script not found: $mlScript"
    }
}

function Generate-MLPredictions {
    <#
    .SYNOPSIS
    Generate ML predictions for specified symbol
    .PARAMETER Symbol
    Stock symbol to generate predictions for
    #>
    param([string]$Symbol = "SPY")
    
    Write-Host "Generating ML predictions for $Symbol..." -ForegroundColor Cyan
    
    $python = Get-PythonExe
    $mlScript = "scripts\ml\enhanced_ml_outlook.py"
    
    if (Test-Path $mlScript) {
        & $python $mlScript --predict --symbol $Symbol --export
        if ($LASTEXITCODE -eq 0) {
            Write-Host "ML predictions generated for $Symbol." -ForegroundColor Green
        } else {
            Write-Error "ML prediction generation failed for $Symbol."
        }
    } else {
        Write-Error "ML script not found: $mlScript"
    }
}

function Export-DashboardData {
    <#
    .SYNOPSIS
    Export data for dashboard display
    .PARAMETER Components
    Components to export (ml, market, alerts, all)
    #>
    param([string[]]$Components = @("all"))
    
    Write-Host "Exporting dashboard data..." -ForegroundColor Cyan
    
    $python = Get-PythonExe
    $integrationScript = "dashboard\integration.py"
    
    if (Test-Path $integrationScript) {
        foreach ($component in $Components) {
            & $python $integrationScript --export $component
        }
        Write-Host "Dashboard data exported successfully." -ForegroundColor Green
    } else {
        Write-Error "Dashboard integration script not found: $integrationScript"
    }
}

# ============================================================================
# Testing and Validation Functions
# ============================================================================

function Test-Configuration {
    <#
    .SYNOPSIS
    Validate current configuration
    .PARAMETER Quiet
    Suppress output and return boolean result
    #>
    param([switch]$Quiet)
    
    if (-not $Quiet) {
        Write-Host "Validating configuration..." -ForegroundColor Cyan
    }
    
    $errors = @()
    $warnings = @()
    
    # Check required environment variables
    $required = @("EMO_ENV")
    
    foreach ($var in $required) {
        if (-not [Environment]::GetEnvironmentVariable($var)) {
            $errors += "Missing required variable: $var"
        }
    }
    
    # Environment-specific validation
    $env = $env:EMO_ENV
    if ($env -eq "production") {
        if (-not $env:ALPACA_KEY_ID) { $errors += "Production requires ALPACA_KEY_ID" }
        if (-not $env:ALPACA_SECRET_KEY) { $errors += "Production requires ALPACA_SECRET_KEY" }
        
        $dbBackend = $env:EMO_DB_BACKEND
        if ($dbBackend -eq "timescaledb" -or ($dbBackend -eq "auto")) {
            if (-not $env:PG_HOST) { $errors += "TimescaleDB requires PG_HOST" }
            if (-not $env:PG_USER) { $errors += "TimescaleDB requires PG_USER" }
        }
    }
    
    # Port conflicts
    if ($env:EMO_HEALTH_PORT -eq $env:EMO_DASHBOARD_PORT) {
        $errors += "Health and Dashboard ports cannot be the same"
    }
    
    # Display results
    if (-not $Quiet) {
        if ($errors.Count -gt 0) {
            Write-Host "❌ Configuration Errors:" -ForegroundColor Red
            $errors | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
        }
        
        if ($warnings.Count -gt 0) {
            Write-Host "⚠️  Configuration Warnings:" -ForegroundColor Yellow
            $warnings | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
        }
        
        if ($errors.Count -eq 0) {
            Write-Host "✅ Configuration validation passed" -ForegroundColor Green
        }
    }
    
    return ($errors.Count -eq 0)
}

function Test-Database {
    <#
    .SYNOPSIS
    Test database connectivity
    #>
    
    Write-Host "Testing database connectivity..." -ForegroundColor Cyan
    
    $python = Get-PythonExe
    
    try {
        $result = & $python -c "
from src.database.enhanced_router import DBRouter
try:
    DBRouter.init()
    status = DBRouter.get_status()
    if status.get('healthy'):
        print('Database connection successful')
        exit(0)
    else:
        print('Database connection failed')
        exit(1)
except Exception as e:
    print(f'Database test failed: {e}')
    exit(1)
"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Database connection successful" -ForegroundColor Green
        } else {
            Write-Host "❌ Database connection failed" -ForegroundColor Red
        }
        
    } catch {
        Write-Host "❌ Database test failed: $_" -ForegroundColor Red
    }
}

function Test-APIConnectivity {
    <#
    .SYNOPSIS
    Test broker API connectivity
    #>
    
    Write-Host "Testing API connectivity..." -ForegroundColor Cyan
    
    if (-not $env:ALPACA_KEY_ID -or -not $env:ALPACA_SECRET_KEY) {
        Write-Warning "Alpaca API credentials not configured"
        return
    }
    
    $python = Get-PythonExe
    
    try {
        $result = & $python -c "
import os
import alpaca_trade_api as tradeapi

try:
    api = tradeapi.REST(
        os.getenv('ALPACA_KEY_ID'),
        os.getenv('ALPACA_SECRET_KEY'),
        os.getenv('ALPACA_API_BASE', 'https://paper-api.alpaca.markets')
    )
    account = api.get_account()
    print(f'API connection successful - Account: {account.status}')
    exit(0)
except Exception as e:
    print(f'API connection failed: {e}')
    exit(1)
"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ API connection successful" -ForegroundColor Green
        } else {
            Write-Host "❌ API connection failed" -ForegroundColor Red
        }
        
    } catch {
        Write-Host "❌ API test failed: $_" -ForegroundColor Red
    }
}

function Run-HealthCheck {
    <#
    .SYNOPSIS
    Run comprehensive system health check
    #>
    
    Write-Host "=== EMO System Health Check ===" -ForegroundColor Cyan
    
    # Configuration validation
    $configOK = Test-Configuration -Quiet
    Write-Host "Configuration: $(if ($configOK) { '✅ OK' } else { '❌ Failed' })" -ForegroundColor $(if ($configOK) { 'Green' } else { 'Red' })
    
    # Database test
    Test-Database
    
    # API test
    Test-APIConnectivity
    
    # Service availability
    $healthPort = $env:EMO_HEALTH_PORT
    if ($healthPort) {
        $healthOK = Test-ServicePort -Port $healthPort
        Write-Host "Health Service: $(if ($healthOK) { '✅ Running' } else { '❌ Not Running' }) (Port $healthPort)" -ForegroundColor $(if ($healthOK) { 'Green' } else { 'Red' })
    }
    
    $dashboardPort = $env:EMO_DASHBOARD_PORT
    if ($dashboardPort) {
        $dashboardOK = Test-ServicePort -Port $dashboardPort
        Write-Host "Dashboard Service: $(if ($dashboardOK) { '✅ Running' } else { '❌ Not Running' }) (Port $dashboardPort)" -ForegroundColor $(if ($dashboardOK) { 'Green' } else { 'Red' })
    }
    
    Write-Host "=== Health Check Complete ===" -ForegroundColor Cyan
}

# ============================================================================
# Utility Functions
# ============================================================================

function Show-ServiceStatus {
    <#
    .SYNOPSIS
    Show status of EMO services
    #>
    
    Write-Host "=== EMO Service Status ===" -ForegroundColor Cyan
    
    # PowerShell jobs
    $jobs = Get-Job | Where-Object { $_.Name -like "*EMO*" -or $_.Name -like "*Health*" -or $_.Name -like "*Dashboard*" }
    if ($jobs.Count -gt 0) {
        Write-Host "Background Jobs:" -ForegroundColor Yellow
        $jobs | ForEach-Object {
            $status = $_.State
            $color = switch ($status) {
                "Running" { "Green" }
                "Failed" { "Red" }
                default { "Yellow" }
            }
            Write-Host "  $($_.Name): $status" -ForegroundColor $color
        }
    } else {
        Write-Host "No background jobs running" -ForegroundColor Gray
    }
    
    # Network ports
    Write-Host "`nNetwork Services:" -ForegroundColor Yellow
    $ports = @(8082, 8083)
    foreach ($port in $ports) {
        $listening = Test-ServicePort -Port $port
        $serviceName = switch ($port) {
            8082 { "Health Service" }
            8083 { "Dashboard" }
            default { "Unknown" }
        }
        
        $status = if ($listening) { "✅ Listening" } else { "❌ Not Listening" }
        $color = if ($listening) { "Green" } else { "Red" }
        Write-Host "  $serviceName (Port $port): $status" -ForegroundColor $color
    }
}

function Show-RecentLogs {
    <#
    .SYNOPSIS
    Show recent log entries
    .PARAMETER Lines
    Number of lines to show
    #>
    param([int]$Lines = 50)
    
    $logFile = $env:EMO_LOG_FILE
    if (-not $logFile) { $logFile = "logs\emo.log" }
    
    if (Test-Path $logFile) {
        Write-Host "=== Recent Logs ($logFile) ===" -ForegroundColor Cyan
        Get-Content $logFile -Tail $Lines | Write-Host
    } else {
        Write-Host "Log file not found: $logFile" -ForegroundColor Yellow
    }
}

function Clear-LogFiles {
    <#
    .SYNOPSIS
    Clear log files
    #>
    
    $confirmation = Read-Host "Clear all log files? (y/N)"
    if ($confirmation -ne "y" -and $confirmation -ne "Y") {
        Write-Host "Operation cancelled." -ForegroundColor Yellow
        return
    }
    
    $logFiles = Get-ChildItem -Path "logs" -Filter "*.log" -ErrorAction SilentlyContinue
    if ($logFiles) {
        $logFiles | ForEach-Object {
            Remove-Item $_.FullName -Force
            Write-Host "Cleared: $($_.Name)" -ForegroundColor Yellow
        }
        Write-Host "Log files cleared." -ForegroundColor Green
    } else {
        Write-Host "No log files found." -ForegroundColor Gray
    }
}

# ============================================================================
# Quick Commands (Aliases)
# ============================================================================

Set-Alias -Name init -Value Setup-Project
Set-Alias -Name env -Value Show-Environment
Set-Alias -Name start -Value Start-EMO
Set-Alias -Name stop -Value Stop-EMO
Set-Alias -Name status -Value Show-ServiceStatus
Set-Alias -Name health -Value Run-HealthCheck
Set-Alias -Name logs -Value Show-RecentLogs

# ============================================================================
# Module Initialization
# ============================================================================

Write-Host "EMO Options Bot PowerShell Tasks loaded." -ForegroundColor Green
Write-Host "Available commands: Setup-Project, Start-EMO, Stop-EMO, Show-ServiceStatus, Run-HealthCheck" -ForegroundColor Cyan
Write-Host "Quick aliases: init, env, start, stop, status, health, logs" -ForegroundColor Yellow
Write-Host "For help on any command: Get-Help <CommandName>" -ForegroundColor Gray