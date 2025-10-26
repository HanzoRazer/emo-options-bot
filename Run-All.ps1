# Enhanced EMO Options Bot - One-Click Windows Runner
# Supports development, staging, and production environments
# Usage: .\Run-All.ps1 [-Environment dev|staging|prod] [-ConfigFile .env.custom]

param(
    [ValidateSet("dev", "staging", "prod", "development", "production")]
    [string]$Environment = "dev",
    [string]$ConfigFile = "",
    [switch]$SkipSetup,
    [switch]$ValidateOnly,
    [switch]$Verbose
)

# ============================================================================
# Configuration and Setup
# ============================================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

# Normalize environment names
$NormalizedEnv = switch ($Environment) {
    { $_ -in @("dev", "development") } { "development" }
    { $_ -in @("prod", "production") } { "production" }
    default { $Environment }
}

Write-Host "=== EMO Options Bot - Enhanced Runner ===" -ForegroundColor Cyan
Write-Host "Environment: $NormalizedEnv" -ForegroundColor Yellow
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Yellow

# ============================================================================
# Utility Functions
# ============================================================================

function Write-Step {
    param([string]$Message)
    Write-Host "`n>>> $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "WARNING: $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

function Test-Command {
    param([string]$Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

function Load-Environment {
    param([string]$EnvFile)
    
    # Load environment-specific .env file if it exists
    $EnvFiles = @()
    
    if ($ConfigFile) {
        $EnvFiles += $ConfigFile
    }
    
    # Environment-specific files
    $EnvFiles += @(
        ".env.$NormalizedEnv",
        ".env.local",
        ".env"
    )
    
    $LoadedFiles = @()
    
    foreach ($EnvFile in $EnvFiles) {
        $EnvPath = Join-Path $ProjectRoot $EnvFile
        if (Test-Path $EnvPath) {
            Write-Host "Loading environment from: $EnvFile" -ForegroundColor Cyan
            
            try {
                Get-Content $EnvPath | ForEach-Object {
                    if ($_ -match "^\s*#" -or $_ -match "^\s*$") { 
                        return 
                    }
                    
                    if ($_ -match "^([^=]+)=(.*)$") {
                        $key = $matches[1].Trim()
                        $value = $matches[2].Trim()
                        
                        # Remove quotes if present
                        if ($value -match '^"(.*)"$') {
                            $value = $matches[1]
                        }
                        
                        [Environment]::SetEnvironmentVariable($key, $value, "Process")
                        if ($Verbose) {
                            Write-Host "  Set $key=$value" -ForegroundColor DarkGray
                        }
                    }
                }
                $LoadedFiles += $EnvFile
            } catch {
                Write-Warning "Failed to load $EnvFile : $_"
            }
        }
    }
    
    # Set EMO_ENV if not already set
    if (-not $env:EMO_ENV) {
        $env:EMO_ENV = $NormalizedEnv
        Write-Host "Set EMO_ENV=$NormalizedEnv" -ForegroundColor Yellow
    }
    
    return $LoadedFiles
}

function Test-Prerequisites {
    Write-Step "Checking Prerequisites"
    
    $Missing = @()
    
    # Check Python
    if (-not (Test-Command "python")) {
        if (-not (Test-Command "py")) {
            $Missing += "Python (python or py command)"
        } else {
            # Create python alias for py
            Set-Alias -Name python -Value py -Scope Global
        }
    }
    
    # Check Git (optional but recommended)
    if (-not (Test-Command "git")) {
        Write-Warning "Git not found (optional but recommended)"
    }
    
    if ($Missing.Count -gt 0) {
        Write-Error "Missing prerequisites: $($Missing -join ', ')"
        Write-Host "Please install the missing tools and try again." -ForegroundColor Red
        exit 1
    }
    
    # Show Python version
    $PythonVersion = python --version 2>&1
    Write-Host "Python: $PythonVersion" -ForegroundColor Green
}

function Setup-VirtualEnvironment {
    Write-Step "Setting up Virtual Environment"
    
    $VenvPath = Join-Path $ProjectRoot ".venv"
    
    if (-not (Test-Path $VenvPath)) {
        Write-Host "Creating virtual environment..." -ForegroundColor Cyan
        python -m venv $VenvPath
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create virtual environment"
            exit 1
        }
    } else {
        Write-Host "Virtual environment already exists" -ForegroundColor Green
    }
    
    # Activate virtual environment
    $ActivateScript = Join-Path $VenvPath "Scripts\Activate.ps1"
    if (Test-Path $ActivateScript) {
        Write-Host "Activating virtual environment..." -ForegroundColor Cyan
        & $ActivateScript
    } else {
        Write-Error "Virtual environment activation script not found"
        exit 1
    }
    
    # Verify activation
    $WhichPython = Get-Command python | Select-Object -ExpandProperty Source
    if ($WhichPython -like "*\.venv\*") {
        Write-Host "Virtual environment activated: $WhichPython" -ForegroundColor Green
    } else {
        Write-Warning "Virtual environment may not be properly activated"
    }
}

function Install-Dependencies {
    Write-Step "Installing Dependencies"
    
    # Upgrade pip first
    python -m pip install --upgrade pip | Out-Null
    
    # Determine requirements file based on environment
    $RequirementsFiles = @()
    
    # Environment-specific requirements
    $EnvReqFile = "requirements.$NormalizedEnv.txt"
    if (Test-Path (Join-Path $ProjectRoot $EnvReqFile)) {
        $RequirementsFiles += $EnvReqFile
    }
    
    # Main requirements file
    if (Test-Path (Join-Path $ProjectRoot "requirements.txt")) {
        $RequirementsFiles += "requirements.txt"
    }
    
    # AI agent requirements (if AI features enabled)
    if ($env:EMO_LLM_ENABLE -eq "1" -or $env:EMO_ML_ENABLE -eq "1") {
        if (Test-Path (Join-Path $ProjectRoot "requirements_ai_agent.txt")) {
            $RequirementsFiles += "requirements_ai_agent.txt"
        }
    }
    
    # Fallback to simple agent requirements
    if ($RequirementsFiles.Count -eq 0) {
        if (Test-Path (Join-Path $ProjectRoot "requirements_simple_agent.txt")) {
            $RequirementsFiles += "requirements_simple_agent.txt"
        }
    }
    
    # Install base dependencies if no requirements file found
    if ($RequirementsFiles.Count -eq 0) {
        Write-Host "No requirements file found, installing base dependencies..." -ForegroundColor Yellow
        $BaseDeps = @(
            "pandas>=1.5.0",
            "numpy>=1.20.0", 
            "matplotlib>=3.5.0",
            "requests>=2.28.0",
            "python-dotenv>=0.19.0",
            "pydantic>=1.9.0",
            "sqlalchemy>=1.4.0",
            "alpaca-trade-api>=3.0.0"
        )
        python -m pip install $BaseDeps
    } else {
        # Install from requirements files
        foreach ($ReqFile in $RequirementsFiles) {
            Write-Host "Installing from: $ReqFile" -ForegroundColor Cyan
            python -m pip install -r $ReqFile
            
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "Some packages failed to install from $ReqFile"
            }
        }
    }
    
    Write-Host "Dependencies installed successfully" -ForegroundColor Green
}

function Initialize-Database {
    Write-Step "Initializing Database"
    
    # Create data directory
    $DataDir = Join-Path $ProjectRoot "data"
    if (-not (Test-Path $DataDir)) {
        New-Item -ItemType Directory -Path $DataDir -Force | Out-Null
        Write-Host "Created data directory: $DataDir" -ForegroundColor Green
    }
    
    # Initialize database based on backend
    $DbBackend = $env:EMO_DB_BACKEND
    if (-not $DbBackend -or $DbBackend -eq "auto") {
        $DbBackend = if ($NormalizedEnv -eq "production") { "timescaledb" } else { "sqlite" }
    }
    
    Write-Host "Database backend: $DbBackend" -ForegroundColor Cyan
    
    switch ($DbBackend) {
        "sqlite" {
            # Create SQLite databases if they don't exist
            $SqlitePath = $env:SQLITE_PATH
            if (-not $SqlitePath) {
                $SqlitePath = Join-Path $DataDir "emo.sqlite"
            }
            
            if (-not (Test-Path $SqlitePath)) {
                # Touch the file
                New-Item -ItemType File -Path $SqlitePath -Force | Out-Null
                Write-Host "Created SQLite database: $SqlitePath" -ForegroundColor Green
            }
            
            # Run SQLite migrations if available
            $MigrationScript = Join-Path $ProjectRoot "scripts\migration\migrate_sqlite.py"
            if (Test-Path $MigrationScript) {
                Write-Host "Running SQLite migrations..." -ForegroundColor Cyan
                python $MigrationScript
            }
        }
        
        "timescaledb" {
            # Run TimescaleDB migrations
            $MigrationScript = Join-Path $ProjectRoot "scripts\migration\migrate_timescale.py"
            if (Test-Path $MigrationScript) {
                Write-Host "Running TimescaleDB migrations..." -ForegroundColor Cyan
                python $MigrationScript
                
                if ($LASTEXITCODE -ne 0) {
                    Write-Error "TimescaleDB migration failed"
                    exit 1
                }
            } else {
                Write-Warning "TimescaleDB migration script not found"
            }
        }
        
        default {
            Write-Warning "Unknown database backend: $DbBackend"
        }
    }
}

function Validate-Configuration {
    Write-Step "Validating Configuration"
    
    $ValidationErrors = @()
    $ValidationWarnings = @()
    
    # Check required environment variables
    $RequiredVars = @("EMO_ENV")
    
    # Environment-specific required variables
    switch ($NormalizedEnv) {
        "production" {
            $RequiredVars += @("ALPACA_KEY_ID", "ALPACA_SECRET_KEY")
            if ($env:EMO_DB_BACKEND -eq "timescaledb" -or $env:EMO_ENV -eq "production") {
                $RequiredVars += @("PG_HOST", "PG_USER", "PG_PASSWORD")
            }
        }
        "staging" {
            $RequiredVars += @("ALPACA_KEY_ID", "ALPACA_SECRET_KEY")
        }
    }
    
    foreach ($Var in $RequiredVars) {
        $Value = [Environment]::GetEnvironmentVariable($Var)
        if (-not $Value) {
            $ValidationErrors += "Missing required environment variable: $Var"
        }
    }
    
    # Validate Alpaca API configuration
    if ($env:ALPACA_KEY_ID -and $env:ALPACA_SECRET_KEY) {
        if ($env:ALPACA_KEY_ID.Length -lt 10) {
            $ValidationWarnings += "ALPACA_KEY_ID seems too short"
        }
        if ($env:ALPACA_SECRET_KEY.Length -lt 20) {
            $ValidationWarnings += "ALPACA_SECRET_KEY seems too short"
        }
    }
    
    # Check database configuration
    $DbBackend = $env:EMO_DB_BACKEND
    if ($DbBackend -eq "timescaledb" -or ($DbBackend -eq "auto" -and $NormalizedEnv -eq "production")) {
        if (-not $env:PG_HOST) {
            $ValidationErrors += "TimescaleDB requires PG_HOST"
        }
    }
    
    # Validate ports
    $HealthPort = $env:EMO_HEALTH_PORT
    $DashboardPort = $env:EMO_DASHBOARD_PORT
    
    if ($HealthPort -and $DashboardPort -and $HealthPort -eq $DashboardPort) {
        $ValidationErrors += "Health and Dashboard ports cannot be the same"
    }
    
    # Display validation results
    if ($ValidationErrors.Count -gt 0) {
        Write-Error "Configuration validation failed:"
        foreach ($Error in $ValidationErrors) {
            Write-Host "  ❌ $Error" -ForegroundColor Red
        }
        exit 1
    }
    
    if ($ValidationWarnings.Count -gt 0) {
        Write-Warning "Configuration warnings:"
        foreach ($Warning in $ValidationWarnings) {
            Write-Host "  ⚠️  $Warning" -ForegroundColor Yellow
        }
    }
    
    Write-Host "✅ Configuration validation passed" -ForegroundColor Green
    
    # Display key configuration
    Write-Host "`nKey Configuration:" -ForegroundColor Cyan
    Write-Host "  Environment: $env:EMO_ENV" -ForegroundColor White
    Write-Host "  Database: $($env:EMO_DB_BACKEND)" -ForegroundColor White
    Write-Host "  Broker: $($env:EMO_BROKER)" -ForegroundColor White
    Write-Host "  Stage Orders: $($env:EMO_STAGE_ORDERS)" -ForegroundColor White
    Write-Host "  Live Data: $($env:EMO_LIVE_DATA)" -ForegroundColor White
}

function Start-Services {
    Write-Step "Starting Services"
    
    $Services = @()
    
    # Health service
    if ($env:EMO_HEALTH_ENABLE -eq "1") {
        $HealthScript = Join-Path $ProjectRoot "scripts\services\health_service.py"
        if (Test-Path $HealthScript) {
            Write-Host "Starting health service on port $($env:EMO_HEALTH_PORT)..." -ForegroundColor Cyan
            $HealthJob = Start-Job -ScriptBlock {
                param($Script, $Port)
                python $Script --port $Port
            } -ArgumentList $HealthScript, $env:EMO_HEALTH_PORT
            $Services += @{ Name = "Health Service"; Job = $HealthJob; Port = $env:EMO_HEALTH_PORT }
        }
    }
    
    # Dashboard service
    if ($env:EMO_DASHBOARD_ENABLE -eq "1") {
        $DashboardScript = Join-Path $ProjectRoot "dashboard\enhanced_dashboard.py"
        if (Test-Path $DashboardScript) {
            Write-Host "Starting dashboard service on port $($env:EMO_DASHBOARD_PORT)..." -ForegroundColor Cyan
            $DashboardJob = Start-Job -ScriptBlock {
                param($Script, $Port)
                python $Script --mode serve --port $Port
            } -ArgumentList $DashboardScript, $env:EMO_DASHBOARD_PORT
            $Services += @{ Name = "Dashboard Service"; Job = $DashboardJob; Port = $env:EMO_DASHBOARD_PORT }
        }
    }
    
    return $Services
}

function Start-MainApplication {
    Write-Step "Starting Main Application"
    
    # Determine main entry point
    $MainScripts = @(
        "main.py",
        "scripts\runner\enhanced_runner.py",
        "scripts\automation\main_runner.py"
    )
    
    $MainScript = $null
    foreach ($Script in $MainScripts) {
        $ScriptPath = Join-Path $ProjectRoot $Script
        if (Test-Path $ScriptPath) {
            $MainScript = $ScriptPath
            break
        }
    }
    
    if (-not $MainScript) {
        Write-Error "No main application script found"
        exit 1
    }
    
    Write-Host "Starting main application: $MainScript" -ForegroundColor Cyan
    
    # Run main application
    python $MainScript
}

function Show-ServiceStatus {
    param([array]$Services)
    
    if ($Services.Count -eq 0) {
        return
    }
    
    Write-Host "`n=== Service Status ===" -ForegroundColor Cyan
    foreach ($Service in $Services) {
        $JobState = $Service.Job.State
        $StatusColor = if ($JobState -eq "Running") { "Green" } else { "Red" }
        Write-Host "$($Service.Name): $JobState (Port: $($Service.Port))" -ForegroundColor $StatusColor
    }
    
    Write-Host "`nService URLs:" -ForegroundColor Cyan
    foreach ($Service in $Services) {
        if ($Service.Job.State -eq "Running") {
            Write-Host "  $($Service.Name): http://localhost:$($Service.Port)" -ForegroundColor White
        }
    }
}

function Cleanup-Services {
    param([array]$Services)
    
    if ($Services.Count -eq 0) {
        return
    }
    
    Write-Host "`nStopping services..." -ForegroundColor Yellow
    foreach ($Service in $Services) {
        if ($Service.Job.State -eq "Running") {
            Stop-Job $Service.Job
            Remove-Job $Service.Job
            Write-Host "Stopped: $($Service.Name)" -ForegroundColor Yellow
        }
    }
}

# ============================================================================
# Main Execution
# ============================================================================

try {
    # Load environment configuration
    $LoadedEnvFiles = Load-Environment
    if ($LoadedEnvFiles.Count -gt 0) {
        Write-Host "Loaded configuration from: $($LoadedEnvFiles -join ', ')" -ForegroundColor Green
    } else {
        Write-Warning "No environment files found, using defaults"
    }
    
    # Validate configuration
    Validate-Configuration
    
    # Exit if validation only
    if ($ValidateOnly) {
        Write-Host "`n✅ Validation completed successfully" -ForegroundColor Green
        exit 0
    }
    
    # Check prerequisites
    Test-Prerequisites
    
    # Setup environment if not skipped
    if (-not $SkipSetup) {
        Setup-VirtualEnvironment
        Install-Dependencies
        Initialize-Database
    }
    
    # Start background services
    $BackgroundServices = Start-Services
    
    # Show service status
    Show-ServiceStatus $BackgroundServices
    
    # Start main application
    Start-MainApplication
    
} catch {
    Write-Error "Execution failed: $_"
    exit 1
} finally {
    # Cleanup background services
    if ($BackgroundServices) {
        Cleanup-Services $BackgroundServices
    }
}

Write-Host "`n=== EMO Options Bot - Execution Complete ===" -ForegroundColor Cyan