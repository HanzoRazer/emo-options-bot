# EMO Options Bot - Developer Quick Start Guide

Welcome to the **EMO Options Bot** - an AI-powered options trading platform with real-time analysis, risk management, and comprehensive monitoring.

## 🎯 **What We're Building**

This is a **production-ready options trading bot** that combines:
- **AI/ML-driven market analysis** with ensemble models
- **Professional options trading strategies** (Iron Condor, Put Credit Spreads, etc.)
- **Real-time risk management** and portfolio monitoring
- **Multi-environment deployment** (SQLite dev → PostgreSQL staging → TimescaleDB production)
- **Comprehensive monitoring dashboard** with live ML predictions

## 🚀 **30-Second Overview**

**Core Value Proposition**: Automated options trading with AI-powered outlook, professional risk management, and institutional-grade monitoring.

**Key Components**:
- **Trading Engine**: Executes options strategies with real-time risk validation
- **ML Outlook System**: Ensemble models predict market direction and volatility
- **Dashboard**: Real-time monitoring of positions, health, and ML predictions
- **Multi-Environment**: Development → Staging → Production deployment pipeline

## 📋 **Essential Files for Understanding the Platform**

### **🔥 Start Here - Core Documentation**
1. **[README_INTEGRATION.md](README_INTEGRATION.md)** - Complete system overview and architecture
2. **[CONFIG.md](CONFIG.md)** - Environment setup and configuration guide
3. **[main.py](main.py)** - Application entry point and command structure

### **⚡ Quick Setup & Demo**
4. **[.env.example](.env.example)** - Configuration template with all required settings
5. **[Makefile](Makefile)** - Cross-platform build commands for all environments
6. **[requirements.txt](requirements.txt)** - Core dependencies (+ requirements-ml.txt, requirements-dev.txt)

### **🏗️ Architecture Deep Dive**
7. **[src/config/enhanced_config.py](src/config/enhanced_config.py)** - Environment-based configuration system
8. **[src/database/db_router.py](src/database/db_router.py)** - Multi-database routing (SQLite→PostgreSQL→TimescaleDB)
9. **[src/strategies/manager.py](src/strategies/manager.py)** - Strategy orchestration and execution

### **📊 Dashboard & Monitoring**
10. **[dashboard/README.md](dashboard/README.md)** - Dashboard quick start and features
11. **[dashboard/enhanced_dashboard.py](dashboard/enhanced_dashboard.py)** - Real-time monitoring system

### **🤖 ML & AI Components**
12. **[src/ml/outlook.py](src/ml/outlook.py)** - ML ensemble prediction system
13. **[tools/ml_outlook_bridge.py](tools/ml_outlook_bridge.py)** - ML integration bridge

### **🐳 Production Deployment**
14. **[docker-compose.prod.yml](docker-compose.prod.yml)** - Production Docker orchestration

## Phase 3: Auto-Load, Tests & CI

We added a small **auto-loader** that makes Phase 3 development painless:

* `src/phase3/auto_loader.py` picks a module directory via `PHASE3_MODULE_DIR` env var or falls back to `./src/phase3` and `./src`.
* It tries to import these core modules: `schemas`, `orchestrator`, `synthesizer`, `gates`, `asr_tts`, `phase3_integration`.
* It prints clear diagnostics and fails gracefully if modules aren't present yet.

### Run the loader locally
```bash
python -m src.phase3.auto_loader
```
Optionally point to a custom location:
```bash
$env:PHASE3_MODULE_DIR="C:\path\to\your\phase3"   # PowerShell
export PHASE3_MODULE_DIR=/path/to/phase3          # bash/zsh
```

### Tests
Two lightweight smoke tests were added:
* `tests/test_phase3_autoload.py` – ensures the loader finds your modules (or skips cleanly).
* `tests/test_phase3_pipeline.py` – if `Phase3TradingSystem` exists, it spins up and handles a simple NL request.

Install dev deps:
```bash
pip install -r requirements-dev.txt
pytest -q
```

### Phase 3 Test Harness
Run the end-to-end Phase 3 acceptance test:
```bash
python tools/phase3_e2e_test.py
```

This executes three test scenarios (neutral/volatile/bullish) and:
- Creates structured staged artifacts in `data/staged_orders/`
- Shows ✅ "Order OK" or clear "blocked" messages
- Provides repeatable, offline Phase 3 testing (no live LLM required)

### CI
We added comprehensive CI workflow that:
* Installs your `requirements.txt`, optional `requirements-ml.txt`, and `requirements-dev.txt`
* Runs `pytest -q` with skip-friendly behavior for fresh clones
* Environment variables set for CI safety (`EMO_ENV=ci`, `PHASE3_MODULE_DIR=""`)

## Phase 3 Skeleton & Local Dev Env

A new placeholder module (`src/phase3/skeleton.py`) keeps imports stable while you build out Phase 3.

### Local Env Setup
Quickly create a machine-specific `.env` file:
```bash
python tools/generate_local_env.py
```
This produces `local.dev.env` with your paths and key variables for Phase 3 development.

### Schema Contract Test
`tests/test_phase3_schema_contract.py` verifies the core Phase 3 objects exist and are importable. Run:
```bash
pytest -q tests/test_phase3_schema_contract.py
```

### **🐳 Production Deployment**
15. **[.github/workflows/ci.yml](.github/workflows/ci.yml)** - CI/CD pipeline
16. **[Dockerfile](Dockerfile)** - Multi-stage production container

## 🏃‍♂️ **Get Running in 5 Minutes**

### **1. Environment Setup**
```powershell
# Clone and setup
git clone <repository>
cd emo_options_bot_sqlite_plot_upgrade

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

### **2. Configuration**
```powershell
# Copy configuration template
Copy-Item .env.example .env

# Edit .env with your Alpaca credentials:
# ALPACA_KEY_ID=your_key_here
# ALPACA_SECRET_KEY=your_secret_here
# EMO_ENV=dev  # Starts with paper trading
```

### **3. Run the Platform**
```powershell
# Quick demo of the system
python scripts/demo_enhanced_strategies.py

# Start the dashboard
python dashboard/enhanced_dashboard.py --mode generate
start dashboard.html

# Or run live dashboard server
python main.py dashboard --host localhost --port 8083
```

### **4. Key Commands (via Makefile)**
```powershell
# Development environment
make dev-setup     # Full development setup
make dev-run       # Start all development services

# Testing
make test          # Run full test suite
make lint          # Code quality checks

# Production deployment
make deploy-staging  # Deploy to staging
make deploy-prod     # Deploy to production
```

## 🧠 **Understanding the Architecture**

### **Core Philosophy**: 
- **Environment-driven**: Same code runs differently in dev/staging/prod
- **Risk-first**: Every trade validated through risk management
- **ML-enhanced**: Human strategies + AI insights
- **Production-ready**: Monitoring, logging, deployment automation

### **Data Flow**:
```
Market Data → ML Analysis → Strategy Selection → Risk Validation → Order Execution → Monitoring
```

### **Environment Progression**:
```
Development (SQLite, Paper Trading) → Staging (PostgreSQL, Paper Trading) → Production (TimescaleDB, Live Trading)
```

## 🎨 **What Makes This Special**

✅ **Professional Options Strategies**: Iron Condor, Put Credit Spreads, Covered Calls
✅ **AI-Powered Market Analysis**: Ensemble ML models with confidence scoring
✅ **Institutional Risk Management**: Portfolio heat monitoring, position sizing
✅ **Real-time Dashboard**: Live monitoring with health checks and alerts
✅ **Multi-Environment Pipeline**: Dev → Staging → Production with CI/CD
✅ **Scalable Architecture**: Microservices with Docker orchestration

## 🔍 **Key Technologies**

- **Backend**: Python, FastAPI, SQLAlchemy, Alembic
- **Database**: SQLite (dev) → PostgreSQL (staging) → TimescaleDB (prod)
- **ML/AI**: scikit-learn, TensorFlow, OpenAI/Anthropic APIs
- **Trading**: Alpaca API, real-time market data
- **Frontend**: HTML/CSS/JS dashboard with Chart.js
- **Infrastructure**: Docker, GitHub Actions, Prometheus/Grafana

## 📚 **Next Steps**

1. **Read [README_INTEGRATION.md](README_INTEGRATION.md)** for complete system understanding
2. **Explore [dashboard/](dashboard/)** for monitoring capabilities
3. **Check [src/strategies/](src/strategies/)** for trading strategy implementations
4. **Review [CONFIG.md](CONFIG.md)** for environment-specific configurations
5. **Study [.github/workflows/ci.yml](.github/workflows/ci.yml)** for deployment pipeline

## Phase 3: JSON-LLM + Trade Staging (Fast Start)

This phase lets you describe trades in natural language, converts them to a structured plan via the LLM, enforces non-bypassable risk gates, then **stages** the trade to disk for review (no live orders unless you promote them).

### Setup
1) Create/complete your `.env` (top-level):
   - `OPENAI_API_KEY` – required for LLM mode (or system falls back to mock)
   - `EMO_STAGING_DIR` – where staged orders are written (default: `ops/staged_orders`)
   - `ALPACA_*` – (paper trading) account keys if you later enable execution

2) Ensure the staging folder exists:
```bash
mkdir -p ops/staged_orders
```

### Usage Examples

#### 1. Generate Trade Plan from Natural Language
```bash
python tools/llm_trade_plan.py --prompt "Iron condor on SPY with ~$500 max risk"
```

#### 2. Validate Generated Plan
```bash
python tools/validate_trade_plan.py --file ops/staged_orders/PLAN.json
```

#### 3. Stage Order for Review
```bash
python tools/phase3_stage_trade.py --from-plan ops/staged_orders/PLAN.json --note "review and approve"
```

### Quick Apply (PowerShell)
```powershell
# Ensure staging directory exists
if (-not (Test-Path "ops/staged_orders")) { 
    New-Item -ItemType Directory -Path "ops/staged_orders" -Force 
}

# Quick test of the pipeline
python tools/llm_trade_plan.py --prompt "Conservative iron condor on SPY"
python tools/validate_trade_plan.py --file ops/staged_orders/PLAN.json
python tools/phase3_stage_trade.py --from-plan ops/staged_orders/PLAN.json
```

## 🆘 **Need Help?**

- **Configuration issues**: Check [CONFIG.md](CONFIG.md)
- **Dashboard not working**: See [dashboard/README.md](dashboard/README.md)
- **Trading questions**: Review [src/strategies/README.md](src/strategies/README.md)
- **Deployment problems**: Check [Dockerfile](Dockerfile) and docker-compose files

---

**Happy Trading!** 🚀📈