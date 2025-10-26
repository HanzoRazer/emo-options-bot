# 🚀 EMO Options Bot - Quick Setup Reference

## 📥 Installation & Setup

### 1. **Environment Setup**
```powershell
# Method 1: PowerShell (Recommended)
.\setup-env.ps1

# Method 2: Batch file
.\setup-env.bat

# Method 3: Manual
Copy-Item .env.example .env
```

### 2. **Install Dependencies**
```powershell
pip install -r requirements-ml.txt
```

### 3. **Validate Setup**
```powershell
python scripts\validate_environment.py
```

## 🔑 Essential Configuration

### **Minimum Required (Copy to .env)**
```properties
# Choose ONE AI provider
OPENAI_API_KEY=sk-your-openai-key

# OR
ANTHROPIC_API_KEY=sk-ant-your-key

# Runtime settings
EMO_ENV=dev
EMO_STAGING_DIR=ops/staged_orders
EMO_STAGE_ORDERS=1
```

### **For Live Trading (Add to .env)**
```properties
ALPACA_KEY_ID=your-key-id
ALPACA_SECRET_KEY=your-secret
ALPACA_API_BASE=https://paper-api.alpaca.markets
```

## 🧪 Testing Your Setup

### **Basic Functionality Test**
```powershell
python scripts\simple_options_demo.py
```

### **Full Integration Test**
```powershell
python scripts\test_options_integration.py
```

### **Environment Check**
```powershell
python scripts\validate_environment.py
```

## 🔗 Quick Links

### **Get API Keys**
- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/
- **Alpaca**: https://app.alpaca.markets/paper/dashboard/overview

### **Documentation**
- **Full Setup Guide**: `ENVIRONMENT_SETUP.md`
- **Options Integration**: `OPTIONS_CHAIN_INTEGRATION_COMPLETE.md`
- **Project README**: `README.md`

## ⚠️ Safety First

### **Development Mode** (Start Here)
```properties
EMO_ENV=dev
MOCK_TRADING=1
ENABLE_LIVE_TRADING=0
ALPACA_API_BASE=https://paper-api.alpaca.markets
```

### **Risk Settings**
```properties
MAX_POSITION_SIZE_PCT=0.05
RISK_VALIDATION_ENABLED=1
REQUIRE_MANUAL_APPROVAL=1
```

## 🛠️ Troubleshooting

### **Permission Errors**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### **Missing Dependencies**
```powershell
pip install openai anthropic yfinance python-dotenv
```

### **Import Errors**
```powershell
# Run from project root
cd C:\path\to\emo_options_bot
python scripts\validate_environment.py
```

## 📞 Support Checklist

Before asking for help:
- [ ] Ran `.\setup-env.ps1`
- [ ] Added API key to `.env`
- [ ] Installed dependencies
- [ ] Ran validation script
- [ ] Checked logs in `logs/` folder

---

**🎯 Goal**: Get from zero to running options analysis in under 5 minutes!