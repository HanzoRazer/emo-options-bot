# EMO Options Bot 🤖📈

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**AI-Powered Intelligent Trading System for Options**

An enterprise-grade, AI-driven options trading platform that transforms natural language into intelligent trading strategies with built-in risk management and order staging capabilities.

## 🎯 Features

### 🧠 AI-Powered Natural Language Processing
- Convert plain English commands into executable trading strategies
- Intelligent parsing of trading intent, symbols, strikes, and expiration dates
- Supports OpenAI GPT-4 for advanced understanding (with graceful fallback)

### 📊 Advanced Trading Strategy Engine
- Single option trades (calls/puts)
- Vertical spreads (bull/bear spreads)
- Iron condors, butterflies, straddles, and strangles
- Strategy analysis with risk/reward calculations
- Greeks estimation and probability analysis

### 🛡️ Built-in Risk Management
- Position size limits
- Portfolio exposure tracking
- Daily loss limits
- Risk scoring (0-100 scale)
- Margin requirement validation
- Real-time risk assessment

### 📋 Order Staging & Validation
- Multi-stage order approval workflow
- Order status tracking (pending → staged → approved → submitted → filled)
- Strategy-level and order-level approval
- Complete audit trail and order history

### 📈 Market Data Integration
- Real-time stock price lookup via Yahoo Finance
- Option chain data retrieval
- Price caching for performance
- Implied volatility tracking

### 💼 Portfolio Management
- Position tracking
- P&L monitoring (realized and unrealized)
- Portfolio value calculation
- Cash and margin management

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/HanzoRazer/emo-options-bot.git
cd emo-options-bot

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### Configuration

Create a `.env` file in the project root:

```bash
# Optional: For AI-powered parsing (recommended)
OPENAI_API_KEY=your_api_key_here
```

### Basic Usage

#### Interactive Mode

```bash
emo-bot interactive
```

```
EMO> Buy 1 AAPL call at $150 expiring in 30 days
EMO> status
EMO> list
EMO> approve STRAT_20241215120000000000
```

#### Command-Line Mode

```bash
# Process a trading command
emo-bot process "Buy 1 AAPL call at $150"

# Get bot status
emo-bot status

# List staged strategies
emo-bot list

# Approve a strategy
emo-bot approve STRAT_20241215120000000000

# Reject a strategy
emo-bot reject STRAT_20241215120000000000 "Too risky"
```

#### Python API

```python
from emo_options_bot import EMOOptionsBot
from emo_options_bot.core.config import Config

# Initialize bot
bot = EMOOptionsBot()

# Process a natural language command
result = bot.process_command("Buy 1 AAPL call at $150 strike expiring in 30 days")

if result["success"]:
    print(f"Strategy created: {result['strategy_id']}")
    print(f"Risk Score: {result['risk_assessment']['risk_score']}/100")
    
    # Approve the strategy
    approval = bot.approve_strategy(result['strategy_id'])
    print(f"Strategy approved: {approval['success']}")
else:
    print(f"Error: {result['error']}")

# Get bot status
status = bot.get_status()
print(f"Portfolio Value: ${status['portfolio']['total_value']}")

# Get staged strategies
strategies = bot.get_staged_strategies()
print(f"Staged strategies: {len(strategies)}")
```

## 📚 Architecture

### Core Components

```
emo_options_bot/
├── ai/                    # Natural language processing
│   └── nlp_processor.py   # Command parsing with AI/rules
├── trading/               # Trading strategy logic
│   └── strategy_engine.py # Strategy validation & analysis
├── risk/                  # Risk management
│   └── risk_manager.py    # Risk assessment & limits
├── orders/                # Order management
│   └── order_stager.py    # Order staging & workflow
├── market_data/           # Market data
│   └── provider.py        # Market data interface
├── core/                  # Core functionality
│   ├── bot.py            # Main bot orchestration
│   ├── config.py         # Configuration management
│   └── models.py         # Data models
├── utils/                 # Utilities
│   └── helpers.py        # Helper functions
└── cli.py                # Command-line interface
```

### Workflow

```
User Command
    ↓
NLP Processor (AI/Rules)
    ↓
Strategy Engine (Validation)
    ↓
Risk Manager (Assessment)
    ↓
Order Stager (Staging)
    ↓
User Approval
    ↓
Order Execution (External)
```

## 🔧 Configuration

The bot can be configured via `Config` object or JSON file:

```python
from emo_options_bot.core.config import Config, RiskConfig, TradingConfig

config = Config(
    ai=AIConfig(
        openai_api_key="your_key",
        model="gpt-4",
        temperature=0.1
    ),
    risk=RiskConfig(
        max_position_size=10000.0,
        max_portfolio_exposure=50000.0,
        max_loss_per_trade=1000.0,
        max_loss_per_day=5000.0,
        enable_risk_checks=True
    ),
    trading=TradingConfig(
        enable_paper_trading=True,
        require_manual_approval=True,
        max_orders_per_day=50
    )
)

bot = EMOOptionsBot(config)
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=emo_options_bot --cov-report=html

# Run specific test file
pytest tests/unit/test_nlp_processor.py

# Run integration tests
pytest tests/integration/
```

## 📖 Examples

### Example 1: Simple Call Purchase

```python
bot = EMOOptionsBot()

result = bot.process_command("Buy 1 AAPL call at $150")

# Output:
# {
#   "success": true,
#   "strategy_id": "STRAT_20241215120000000000",
#   "strategy": {...},
#   "risk_assessment": {
#     "approved": true,
#     "risk_score": 25.5,
#     "max_loss": 1500.0
#   }
# }
```

### Example 2: Vertical Spread

```python
from emo_options_bot.trading.strategy_engine import StrategyEngine
from emo_options_bot.core.models import OptionType
from decimal import Decimal
from datetime import datetime, timedelta

engine = StrategyEngine()

strategy = engine.create_vertical_spread(
    underlying="SPY",
    option_type=OptionType.CALL,
    long_strike=Decimal("450"),
    short_strike=Decimal("455"),
    expiration=(datetime.now() + timedelta(days=30)).date(),
    quantity=1
)

print(f"Strategy: {strategy.name}")
print(f"Max Risk: ${strategy.max_risk}")
```

### Example 3: Risk Assessment

```python
from emo_options_bot.risk.risk_manager import RiskManager

manager = RiskManager()

assessment = manager.assess_strategy(strategy)

print(f"Approved: {assessment.approved}")
print(f"Risk Score: {assessment.risk_score}/100")
print(f"Violations: {assessment.violations}")
print(f"Warnings: {assessment.warnings}")
```

## 🔒 Security & Risk Considerations

⚠️ **Important**: This is a trading system that can execute real financial transactions. Please note:

- Always use **paper trading mode** for testing
- Review all staged orders before approval
- Set appropriate **risk limits** in configuration
- Never commit API keys or credentials to version control
- This system is for **educational and research purposes**
- Past performance does not guarantee future results
- Options trading involves substantial risk

## 🛣️ Roadmap

- [ ] Add broker integrations (TD Ameritrade, Interactive Brokers, etc.)
- [ ] Real-time Greeks calculation with Black-Scholes model
- [ ] Advanced charting and visualization
- [ ] Backtesting engine
- [ ] Machine learning for strategy optimization
- [ ] Web dashboard interface
- [ ] Mobile app
- [ ] Multi-account support
- [ ] Automated strategy execution
- [ ] Alert system (SMS/email/push)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Ross Echols**

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Yahoo Finance for market data
- The Python trading community

## 📞 Support

For questions or support, please open an issue on GitHub.

---

**Disclaimer**: This software is provided "as is", without warranty of any kind. Trading options involves risk and may not be suitable for all investors. Always consult with a qualified financial advisor before making investment decisions.
