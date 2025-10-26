# EMO Options Bot Environment Setup Script
# This script initializes the .env file with default values
# Run from your project root directory

param(
    [switch]$Force,  # Force overwrite existing .env file
    [switch]$Help    # Show help information
)

function Show-Help {
    Write-Host @"
EMO Options Bot Environment Setup

USAGE:
    .\setup-env.ps1 [-Force] [-Help]

OPTIONS:
    -Force      Overwrite existing .env file if it exists
    -Help       Show this help message

DESCRIPTION:
    This script creates a .env file from the .env.example template with
    empty values that you can fill in with your actual API keys and settings.

EXAMPLES:
    .\setup-env.ps1               # Create .env if it doesn't exist
    .\setup-env.ps1 -Force        # Overwrite existing .env file

"@
}

if ($Help) {
    Show-Help
    exit 0
}

# Define paths
$projectRoot = Get-Location
$envExamplePath = Join-Path $projectRoot ".env.example"
$envPath = Join-Path $projectRoot ".env"

# Check if .env.example exists
if (-not (Test-Path $envExamplePath)) {
    Write-Error "❌ .env.example file not found in current directory"
    Write-Host "Please ensure you're running this script from the project root."
    exit 1
}

# Check if .env already exists
if ((Test-Path $envPath) -and -not $Force) {
    Write-Warning "⚠️ .env file already exists"
    Write-Host "Use -Force parameter to overwrite, or manually edit the existing file."
    Write-Host "Current .env file: $envPath"
    exit 0
}

# Create .env file from template
try {
    Write-Host "📝 Creating .env file from template..."
    
    # Read the example file and create a basic .env
    $envContent = @"
# EMO Options Bot Environment Configuration
# Generated on $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

# ============================================================================
# Core AI/LLM Providers (REQUIRED)
# ============================================================================
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# ============================================================================
# EMO Bot Runtime Configuration
# ============================================================================
EMO_ENV=dev
EMO_STAGING_DIR=ops/staged_orders
EMO_STAGE_ORDERS=1

# ============================================================================
# Trading Providers & Market Data (REQUIRED FOR LIVE TRADING)
# ============================================================================
ALPACA_KEY_ID=
ALPACA_SECRET_KEY=
ALPACA_API_BASE=https://paper-api.alpaca.markets
ALPACA_DATA_URL=https://data.alpaca.markets/v2

# ============================================================================
# Optional Services
# ============================================================================
POLYGON_API_KEY=
AZURE_SPEECH_KEY=
GOOGLE_APPLICATION_CREDENTIALS=

# ============================================================================
# Risk Management & Safety
# ============================================================================
MAX_POSITION_SIZE_PCT=0.05
MAX_PORTFOLIO_RISK_PCT=0.10
RISK_VALIDATION_ENABLED=1

# ============================================================================
# Dashboard & Web Interface
# ============================================================================
DASHBOARD_PORT=8083
SECRET_KEY=change-this-secret-key-$(Get-Random)

# ============================================================================
# Feature Flags
# ============================================================================
ENABLE_LIVE_TRADING=0
MOCK_TRADING=1
VOICE_ENABLED=0

"@

    # Write the content to .env file
    Set-Content -Path $envPath -Value $envContent -Encoding UTF8
    
    Write-Host "✅ .env file created successfully!"
    Write-Host ""
    Write-Host "📋 Next Steps:"
    Write-Host "   1. Edit .env file and add your API keys"
    Write-Host "   2. Required: OPENAI_API_KEY or ANTHROPIC_API_KEY"
    Write-Host "   3. For live trading: ALPACA_KEY_ID and ALPACA_SECRET_KEY"
    Write-Host "   4. For voice features: AZURE_SPEECH_KEY"
    Write-Host ""
    Write-Host "🔧 Configuration file: $envPath"
    Write-Host "📖 Full template with all options: $envExamplePath"
    
} catch {
    Write-Error "❌ Failed to create .env file: $($_.Exception.Message)"
    exit 1
}

# Create necessary directories
$directories = @(
    "ops/staged_orders",
    "ops/staged_orders/backup", 
    "logs",
    "data"
)

Write-Host ""
Write-Host "📁 Creating required directories..."

foreach ($dir in $directories) {
    $fullPath = Join-Path $projectRoot $dir
    if (-not (Test-Path $fullPath)) {
        try {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
            Write-Host "   ✅ Created: $dir"
        } catch {
            Write-Warning "   ⚠️ Could not create: $dir"
        }
    } else {
        Write-Host "   ✓ Exists: $dir"
    }
}

Write-Host ""
Write-Host "🚀 EMO Options Bot environment setup complete!"
Write-Host "   Remember to fill in your API keys in the .env file before running the bot."