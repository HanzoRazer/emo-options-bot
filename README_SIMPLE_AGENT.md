# 🤖 Simplified AI Trading Agent

A streamlined AI trading assistant that processes natural language commands into validated options strategies. This simplified version provides core functionality with clear separation of concerns and easy integration with existing systems.

## 🏗️ Architecture

```
User Input (Text/Voice)
         ↓
    Intent Router
         ↓
   Plan Synthesizer
         ↓
    Risk Validator
         ↓
    REST API State
         ↓
   Dashboard Display
```

## 📁 Project Structure

```
agents/
├── intent_router.py      # Parse text → structured intent
├── plan_synthesizer.py   # Build executable trading plans
├── validators.py         # Risk validation & checking
└── __init__.py

voice/
├── transcriber_stub.py   # Speech-to-text placeholder
├── tts_stub.py          # Text-to-speech placeholder  
└── __init__.py

api/
├── rest_server.py       # FastAPI REST endpoints
└── __init__.py

tools/
├── agent_happy_path.py        # Main demo & interactive mode
├── dashboard_agent_integration.py  # Dashboard integration
└── ml_outlook_generator.py    # ML data generator
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install required packages
pip install -r requirements_simple_agent.txt

# Core packages: fastapi, uvicorn, pydantic
```

### 2. Run Interactive Demo

```bash
# Interactive mode - enter commands manually
python tools/agent_happy_path.py interactive

# Automated demo mode
python tools/agent_happy_path.py demo

# Test API endpoints only
python tools/agent_happy_path.py test
```

### 3. Try Commands

```
Command: Build an iron condor on SPY with 7 DTE
Command: Create a put credit spread on QQQ with low risk
Command: Set up a covered call on AAPL with moderate risk
Command: Status
```

### 4. Check REST API

```bash
# Health check
curl http://localhost:8085/health

# Last processing state
curl http://localhost:8085/last

# System status
curl http://localhost:8085/status
```

## 💬 Example Session

```
🤖 EMO Options Bot - AI Agent Happy Path
==================================================
Starting REST API server...
API server running at http://localhost:8085

🎤 INTERACTIVE MODE
Enter trading commands or 'quit' to exit

Command: Build an iron condor on SPY with 7 DTE
[TTS 15:30:45] 🔊 Processing: Build an iron condor on SPY with 7 DTE
Intent: build_strategy
Symbol: SPY
Strategy: iron_condor
Parameters: {'dte': 7, 'risk_level': 'moderate'}
Plan created: iron_condor on SPY
DTE: 7, Risk Level: moderate
Legs: 4
Estimated Credit: $1.50
Max Profit: $150.00
Max Loss: $350.00
[TTS 15:30:46] 🔊 Created iron condor plan for SPY with moderate risk
Validation: PASSED
Risk Score: 1.5/10
Position Size: 0.35%
[TTS 15:30:46] 🔊 Plan passed all validation checks
[TTS 15:30:46] 🔊 Plan is ready for approval when you enable staging.
State updated and available at API endpoints
```

## 📊 Components Overview

### Intent Router (`agents/intent_router.py`)
- **Purpose**: Parse natural language → structured intents
- **Input**: Free-form text commands
- **Output**: `Intent` objects with kind, symbol, strategy, params
- **Features**: Keyword-based parsing (LLM integration point for future)

```python
from agents import parse

intent = parse("Build an iron condor on SPY with 7 DTE")
print(f"Strategy: {intent.strategy}")  # iron_condor
print(f"Symbol: {intent.symbol}")      # SPY
print(f"DTE: {intent.params['dte']}")  # 7
```

### Plan Synthesizer (`agents/plan_synthesizer.py`)
- **Purpose**: Convert intents → executable trading plans
- **Strategies**: Iron Condor, Credit Spreads, Covered Call, Protective Put, Long Straddle
- **Features**: Risk-based position sizing, realistic strike selection, P&L estimation

```python
from agents import build_plan

plan = build_plan("SPY", "iron_condor", {"dte": 7, "risk_level": "low"})
print(f"Legs: {len(plan.legs)}")
print(f"Max Profit: ${plan.max_profit:.2f}")
```

### Risk Validator (`agents/validators.py`)
- **Purpose**: Comprehensive risk validation
- **Checks**: Position sizing, DTE limits, strategy-specific rules, portfolio impact
- **Output**: Pass/fail with detailed warnings and errors

```python
from agents import risk_check

validation = risk_check(plan, netliq=100000)
print(f"Valid: {validation.ok}")
print(f"Risk Score: {validation.risk_score}/10")
```

### Voice Stubs (`voice/`)
- **Current**: Placeholder implementations for testing
- **Future**: Real STT/TTS integration points
- **Usage**: `speak()` for output, `transcribe_from_microphone()` for input

### REST API (`api/rest_server.py`)
- **Endpoints**: `/health`, `/status`, `/last`, `/process`, `/plans`
- **Purpose**: State sharing with dashboard and external systems
- **Features**: Command processing, state persistence, error handling

## 🎮 Dashboard Integration

### Generate Agent Cards
```python
from tools.dashboard_agent_integration import generate_agent_dashboard_cards

cards_html = generate_agent_dashboard_cards()
# Insert into your dashboard HTML
```

### Quick Actions
```python
from tools.dashboard_agent_integration import generate_agent_quick_actions

actions_html = generate_agent_quick_actions()
# Provides buttons to test agent commands
```

### View Integration Demo
```bash
python tools/dashboard_agent_integration.py
# Creates dashboard_with_agent.html
```

## 🔧 Supported Strategies

| Strategy | Description | Risk Level | Parameters |
|----------|-------------|------------|------------|
| `iron_condor` | Neutral strategy with defined risk | Low-High | `wings`, `dte` |
| `put_credit_spread` | Bullish with limited risk | Low-Moderate | `wings`, `dte` |
| `call_credit_spread` | Bearish with limited risk | Low-Moderate | `wings`, `dte` |
| `covered_call` | Income on stock holdings | Low | `dte` |
| `protective_put` | Portfolio protection | Low | `dte` |
| `long_straddle` | High volatility play | Moderate-High | `dte` |

## 🛡️ Risk Management

### Built-in Safeguards
- **Position Sizing**: Max 2% portfolio risk per trade
- **DTE Limits**: Minimum 3 days, warnings below 7 days
- **Risk Scoring**: 0-10 scale with automatic adjustments
- **Strategy Limits**: Risk-appropriate position sizes

### Validation Layers
1. **Structure Validation**: Valid legs, strikes, quantities
2. **Strategy Validation**: Strategy-specific rules and limits
3. **Risk Validation**: Portfolio percentage, absolute dollar limits
4. **Market Validation**: Symbol recognition, liquidity warnings

## 📈 Integration Points

### ML Outlook Integration
```python
# Generate ML signals for strategy selection
python tools/ml_outlook_generator.py

# Outlook data available in ops/ml_outlook.json
```

### Database Integration
```python
# Future: Store plans and validation results
from ops.db import DatabaseRouter
db = DatabaseRouter()
db.save_plan(plan)
```

### Execution Integration
```python
# Future: Execute approved plans
from execution.broker_interface import BrokerInterface
broker = BrokerInterface()
broker.execute_plan(plan)
```

## 🧪 Testing & Development

### Component Testing
```python
# Test intent parsing
from agents import parse
intent = parse("Create iron condor on SPY")
assert intent.strategy == "iron_condor"

# Test plan building  
from agents import build_plan
plan = build_plan("SPY", "iron_condor", {"dte": 7})
assert len(plan.legs) == 4

# Test validation
from agents import risk_check
validation = risk_check(plan)
assert validation.ok == True
```

### API Testing
```bash
# Test all endpoints
python tools/agent_happy_path.py test

# Manual API testing
curl -X POST http://localhost:8085/process \
  -H "Content-Type: application/json" \
  -d '{"text": "Build iron condor on SPY", "mode": "text"}'
```

### Voice Testing
```python
from voice import speak, transcribe_text
speak("Testing TTS")
text = transcribe_text("Build iron condor on SPY")  
```

## 🔮 Future Enhancements

### Phase 1: LLM Integration
- Replace keyword parsing with GPT-4/Claude
- Improve intent understanding and context
- Add conversation memory and follow-ups

### Phase 2: Real Voice  
- Integrate actual STT/TTS libraries
- Voice activation and continuous listening
- Multi-language support

### Phase 3: Advanced Strategies
- Multi-leg combinations and adjustments
- Dynamic hedging recommendations  
- Advanced Greeks-based position sizing

### Phase 4: Production Features
- User authentication and permissions
- Compliance reporting and audit trails
- Real-time market data integration
- Advanced risk analytics

## 🛠️ Customization

### Add New Strategies
```python
# In agents/plan_synthesizer.py
def build_plan(symbol, strategy, params):
    if strategy == "your_custom_strategy":
        # Define legs, risk, P&L
        return Plan(...)
```

### Custom Validation Rules
```python  
# In agents/validators.py
def risk_check(plan, **kwargs):
    # Add your custom validation logic
    if custom_condition:
        errors.append("Custom rule violation")
```

### Custom Intent Parsing
```python
# In agents/intent_router.py  
def parse(text):
    # Add your parsing logic
    if "your_keyword" in text:
        strategy = "your_strategy"
```

## ⚠️ Important Notes

### Current Limitations
- **Keyword-based parsing**: Not true NLU (LLM integration ready)
- **Mock market data**: Uses hardcoded prices (real data integration ready)
- **Stub voice system**: Placeholders for STT/TTS (real integration ready)
- **No execution**: Plans are validated but not executed

### Production Considerations
- Add authentication and user management
- Integrate real market data feeds
- Add comprehensive logging and monitoring
- Implement proper error handling and recovery
- Add compliance and audit reporting

### Risk Disclaimer
This is a development framework for educational purposes. All trading involves risk of loss. Users should:
- Understand options trading thoroughly
- Start with paper trading
- Never risk more than they can afford to lose
- Consult with financial professionals

---

**🎯 Ready to start building with the Simplified AI Agent?**

Run `python tools/agent_happy_path.py interactive` and begin experimenting!