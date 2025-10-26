@echo off
REM EMO Options Bot Environment Setup (Windows Batch)
REM Simple alternative to PowerShell script

echo EMO Options Bot Environment Setup
echo ================================

REM Check if .env already exists
if exist ".env" (
    echo WARNING: .env file already exists
    echo Delete it first if you want to recreate it
    pause
    exit /b 1
)

echo Creating .env file from template...

REM Create basic .env file
(
echo # EMO Options Bot Environment Configuration
echo # Fill in your actual API keys and settings
echo.
echo # === Core AI/LLM Providers ===
echo OPENAI_API_KEY=
echo ANTHROPIC_API_KEY=
echo.
echo # === EMO Bot Runtime ===
echo EMO_ENV=dev
echo EMO_STAGING_DIR=ops/staged_orders
echo EMO_STAGE_ORDERS=1
echo.
echo # === Alpaca Paper Trading ===
echo ALPACA_KEY_ID=
echo ALPACA_SECRET_KEY=
echo ALPACA_API_BASE=https://paper-api.alpaca.markets
echo ALPACA_DATA_URL=https://data.alpaca.markets/v2
echo.
echo # === Optional Services ===
echo POLYGON_API_KEY=
echo AZURE_SPEECH_KEY=
echo.
echo # === Risk Management ===
echo MAX_POSITION_SIZE_PCT=0.05
echo RISK_VALIDATION_ENABLED=1
echo.
echo # === Dashboard ===
echo DASHBOARD_PORT=8083
echo.
echo # === Feature Flags ===
echo ENABLE_LIVE_TRADING=0
echo MOCK_TRADING=1
echo VOICE_ENABLED=0
) > .env

echo ✓ .env file created successfully!
echo.

REM Create required directories
echo Creating required directories...
if not exist "ops\staged_orders" mkdir "ops\staged_orders"
if not exist "ops\staged_orders\backup" mkdir "ops\staged_orders\backup"
if not exist "logs" mkdir "logs"
if not exist "data" mkdir "data"

echo ✓ Directories created
echo.
echo Setup complete! 
echo.
echo Next steps:
echo 1. Edit .env file and add your API keys
echo 2. Required: OPENAI_API_KEY or ANTHROPIC_API_KEY  
echo 3. For live trading: ALPACA_KEY_ID and ALPACA_SECRET_KEY
echo.
pause