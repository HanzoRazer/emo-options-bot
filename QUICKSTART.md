# Quick Start Guide

Get started with EMO Options Bot in 5 minutes!

## Installation

### 1. Prerequisites

```bash
# Check Python version (3.9+ required)
python --version

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install EMO Options Bot

```bash
# Clone the repository
git clone https://github.com/HanzoRazer/emo-options-bot.git
cd emo-options-bot

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### 3. Configure (Optional)

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key (optional)
# OPENAI_API_KEY=your_key_here
```

**Note**: OpenAI API key is optional. The bot will work with rule-based parsing if not provided.

## Your First Trade

### Using Python API

```python
from emo_options_bot import EMOOptionsBot

# Initialize bot
bot = EMOOptionsBot()

# Process a trading command
result = bot.process_command("Buy 1 AAPL call at $150")

if result["success"]:
    print(f"✓ Strategy created: {result['strategy_id']}")
    print(f"  Risk Score: {result['risk_assessment']['risk_score']}/100")
    
    # Approve the strategy
    bot.approve_strategy(result['strategy_id'])
    print("✓ Strategy approved!")
else:
    print(f"✗ Error: {result['error']}")
```

### Using CLI - Interactive Mode

```bash
emo-bot interactive
```

```
EMO> Buy 1 AAPL call at $150
✓ Success!
  Strategy ID: STRAT_20241215120000000000
  Risk Score: 25.5/100
  
EMO> approve STRAT_20241215120000000000
✓ Strategy approved!

EMO> status
Portfolio Value: $100,000.00
Staged Orders: 1

EMO> exit
```

### Using CLI - Command Mode

```bash
# Process a command
emo-bot process "Buy 1 AAPL call at $150"

# List staged strategies
emo-bot list

# Approve a strategy
emo-bot approve STRAT_20241215120000000000

# Get status
emo-bot status
```

## Common Commands

### Natural Language Examples

```python
bot = EMOOptionsBot()

# Single option trades
bot.process_command("Buy 1 AAPL call at $150")
bot.process_command("Sell 2 TSLA puts at $200")
bot.process_command("Buy 5 SPY calls at $450 expiring in 30 days")

# The bot understands various formats
bot.process_command("Purchase GOOGL $100 call option")
bot.process_command("Sell to open 3 MSFT $300 put contracts")
```

## Configuration Examples

### Custom Risk Limits

```python
from emo_options_bot import EMOOptionsBot
from emo_options_bot.core.config import Config, RiskConfig

config = Config(
    risk=RiskConfig(
        max_position_size=5000.0,       # $5k max per position
        max_portfolio_exposure=20000.0,  # $20k total exposure
        max_loss_per_trade=500.0,        # $500 max loss per trade
        max_loss_per_day=2000.0          # $2k daily loss limit
    )
)

bot = EMOOptionsBot(config)
```

### Paper Trading (Recommended)

```python
from emo_options_bot.core.config import Config, TradingConfig

config = Config(
    trading=TradingConfig(
        enable_paper_trading=True,       # Use paper trading
        require_manual_approval=True      # Require approval
    )
)

bot = EMOOptionsBot(config)
```

## Next Steps

### Run Examples

```bash
# Basic usage
python examples/example_basic.py

# Advanced vertical spread
python examples/example_advanced.py

# Risk management
python examples/example_risk_management.py
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=emo_options_bot --cov-report=html

# Open coverage report
open htmlcov/index.html  # On Mac
```

### Explore Features

1. **Strategy Analysis**
   ```python
   from emo_options_bot.trading.strategy_engine import StrategyEngine
   
   engine = StrategyEngine()
   analysis = engine.analyze_strategy(strategy)
   print(analysis)
   ```

2. **Risk Assessment**
   ```python
   from emo_options_bot.risk.risk_manager import RiskManager
   
   manager = RiskManager()
   assessment = manager.assess_strategy(strategy)
   print(f"Risk Score: {assessment.risk_score}/100")
   ```

3. **Order Management**
   ```python
   staged = bot.get_staged_strategies()
   print(f"Staged strategies: {len(staged)}")
   ```

## Tips for Success

### 1. Start with Paper Trading

Always test with paper trading first:
- No real money at risk
- Learn the system
- Test strategies

### 2. Review Before Approving

Always review staged orders:
- Check the strategy details
- Verify risk assessment
- Confirm parameters match your intent

### 3. Set Appropriate Risk Limits

Configure risk limits based on your:
- Account size
- Risk tolerance
- Trading experience

### 4. Use Natural Language

The bot understands various formats:
- "Buy 1 AAPL call at $150"
- "Purchase AAPL $150 call option"
- "Long 1 AAPL 150 call"

### 5. Monitor and Adjust

- Check bot status regularly
- Review portfolio summary
- Adjust risk limits as needed

## Troubleshooting

### Bot doesn't parse my command

- Make sure command includes: action, symbol, option type, strike
- Try simpler wording
- Check examples in README

### Risk assessment fails

- Check configured risk limits
- Verify position size
- Review daily loss limits
- Check portfolio exposure

### Import errors

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Reinstall package
pip install -e .
```

## Getting Help

- 📖 Read the full [README](README.md)
- 🐛 Report issues on [GitHub](https://github.com/HanzoRazer/emo-options-bot/issues)
- 💬 Ask questions in [Discussions](https://github.com/HanzoRazer/emo-options-bot/discussions)
- 📚 Check [examples](examples/)

## Important Reminders

⚠️ **Trading Risk**: Options trading involves substantial risk. Only trade with funds you can afford to lose.

⚠️ **Paper Trading**: Always use paper trading mode when testing.

⚠️ **Manual Review**: Always review and approve orders manually before execution.

⚠️ **Educational Purpose**: This software is for educational and research purposes.

---

**Ready to trade smarter?** Start with `emo-bot interactive` and explore! 🚀
