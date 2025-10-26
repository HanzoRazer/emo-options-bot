# EMO Options Bot Environment Configuration Guide

## Quick Start

### 1. **Automatic Setup (Recommended)**
```powershell
# Run from project root
.\setup-env.ps1
```

### 2. **Manual Setup**
```powershell
# Copy template and edit
Copy-Item .env.example .env
# Then edit .env with your actual values
```

## 🔑 Required API Keys

### **AI/LLM Providers** (Choose One)

#### OpenAI (Recommended)
```properties
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4o-mini
```
- Get key: https://platform.openai.com/api-keys
- Cost: ~$0.01-0.03 per analysis
- Models: `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo`

#### Anthropic Claude (Alternative)
```properties
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
ANTHROPIC_MODEL=claude-3-haiku-20240307
```
- Get key: https://console.anthropic.com/
- Cost: ~$0.01-0.02 per analysis  
- Models: `claude-3-haiku-20240307`, `claude-3-sonnet-20240229`

### **Trading Providers** (For Live Trading)

#### Alpaca (Recommended Broker)
```properties
ALPACA_KEY_ID=your-alpaca-key-id
ALPACA_SECRET_KEY=your-alpaca-secret
ALPACA_API_BASE=https://paper-api.alpaca.markets
```
- Get keys: https://app.alpaca.markets/paper/dashboard/overview
- **Start with paper trading** (free, no risk)
- Switch to live: Change `ALPACA_API_BASE` to `https://api.alpaca.markets`

#### Polygon (Market Data - Optional)
```properties
POLYGON_API_KEY=your-polygon-key
```
- Get key: https://polygon.io/
- Used for enhanced options chain data
- Free tier available

## 🎯 Core Configuration

### **Environment Settings**
```properties
# Development, staging, or production
EMO_ENV=dev

# Where to stage orders before execution
EMO_STAGING_DIR=ops/staged_orders

# Enable order staging (recommended)
EMO_STAGE_ORDERS=1
```

### **Risk Management** 
```properties
# Maximum position size as % of portfolio
MAX_POSITION_SIZE_PCT=0.05

# Maximum portfolio risk exposure
MAX_PORTFOLIO_RISK_PCT=0.10

# Require manual approval for trades
RISK_VALIDATION_ENABLED=1
```

### **Dashboard & Web Interface**
```properties
DASHBOARD_PORT=8083
SECRET_KEY=your-secret-key-change-this
```

## 🚀 Optional Features

### **Voice Interface**
```properties
# Enable voice commands
VOICE_ENABLED=1

# Azure Speech Services (recommended)
AZURE_SPEECH_KEY=your-azure-speech-key
AZURE_SPEECH_REGION=eastus

# Alternative: Google Cloud Speech
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

### **Advanced Features**
```properties
# Enable live trading (when ready)
ENABLE_LIVE_TRADING=0

# Enable portfolio optimization
ENABLE_PORTFOLIO_OPTIMIZATION=1

# Enable advanced Greeks calculations
ENABLE_ADVANCED_GREEKS=1

# Enable machine learning analysis
ENABLE_ML_ANALYSIS=0
```

## 🛡️ Security Best Practices

### **API Key Security**
1. **Never commit `.env` to git**
   ```bash
   # Already in .gitignore
   echo ".env" >> .gitignore
   ```

2. **Use environment-specific files**
   - `.env` - Development (git-ignored)
   - `.env.staging` - Staging environment
   - `.env.prod` - Production environment

3. **Rotate keys regularly**
   - Change API keys every 90 days
   - Monitor usage for anomalies

### **Trading Security**
1. **Start with paper trading**
   ```properties
   ALPACA_API_BASE=https://paper-api.alpaca.markets
   MOCK_TRADING=1
   ```

2. **Enable risk validation**
   ```properties
   RISK_VALIDATION_ENABLED=1
   REQUIRE_MANUAL_APPROVAL=1
   ```

3. **Set position limits**
   ```properties
   MAX_SINGLE_TRADE_RISK=5000
   AUTO_APPROVAL_LIMIT=1000
   ```

## 📊 Provider Configuration

### **Provider Priority Orders**
```properties
# AI providers (first available used)
LLM_PROVIDER_ORDER=openai,anthropic,mock

# Options data providers
CHAIN_PROVIDER_ORDER=alpaca,polygon,yfinance,mock

# Voice providers
VOICE_PROVIDER_ORDER=azure,google,text_fallback
```

### **Fallback Behavior**
- System tries providers in order
- Falls back to mock data if all fail
- Ensures bot keeps running even with API issues

## 🔧 Development Configuration

### **Debug Settings**
```properties
EMO_LOG_LEVEL=INFO
DEBUG_LEVEL=INFO
VERBOSE_LOGGING=0
```

### **Testing**
```properties
TEST_MODE=0
MOCK_TRADING=1
SKIP_VALIDATION=0
```

## 📁 Directory Structure Created

```
project-root/
├── .env                    # Your configuration (git-ignored)
├── .env.example           # Template with all options
├── ops/
│   └── staged_orders/     # Staged trades before execution
│       └── backup/        # Backup of executed trades
├── logs/                  # Application logs
└── data/                  # Database and cache files
```

## 🚨 Troubleshooting

### **Common Issues**

#### "No module named 'openai'"
```bash
pip install openai anthropic yfinance
```

#### "Invalid API key"
- Check key format (starts with `sk-`)
- Verify key has sufficient credits
- Ensure no extra spaces in `.env`

#### "Permission denied"  
```powershell
# Fix PowerShell execution policy
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### "Directory not found"
```powershell
# Recreate directories
.\setup-env.ps1 -Force
```

### **Environment Validation**
```python
# Test your configuration
python scripts/simple_options_demo.py
```

## 🎯 Production Deployment

### **Pre-Production Checklist**
- [ ] All required API keys configured
- [ ] Risk limits set appropriately  
- [ ] Paper trading tested successfully
- [ ] Backup directories configured
- [ ] Monitoring enabled
- [ ] Manual approval enabled

### **Go-Live Process**
1. **Test in paper trading mode**
2. **Set conservative risk limits**
3. **Enable manual approval**
4. **Switch to live trading**
   ```properties
   ALPACA_API_BASE=https://api.alpaca.markets
   ENABLE_LIVE_TRADING=1
   MOCK_TRADING=0
   ```

## 📞 Support

- **Documentation**: See `README.md` and `docs/` folder
- **Configuration Issues**: Check this guide first
- **API Issues**: Verify keys and provider status
- **Trading Issues**: Ensure paper trading works first

---

**⚠️ Important**: Always start with paper trading and conservative settings. Never risk money you can't afford to lose.