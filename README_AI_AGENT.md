# 🤖 AI Trading Agent - Voice-Driven Options Trading Assistant

A sophisticated AI-powered trading assistant that converts natural language commands into validated options trading strategies. Features voice commands, intelligent intent parsing, comprehensive risk validation, and human approval workflows.

## 🎯 Key Features

### 🗣️ Natural Language Interface
- **Voice Commands**: "Generate low-risk income from SPY this month"
- **Text Input**: Full natural language processing for trading requests
- **Intent Understanding**: Converts free-form text to structured trading plans
- **Context Awareness**: Maintains conversation history and context

### 🧠 Intelligent Strategy Translation  
- **Multi-Strategy Support**: Iron Condor, Credit Spreads, Covered Calls, Straddles, Protective Puts
- **Risk-Aware Planning**: Automatic risk level assessment and position sizing
- **Market Context**: Incorporates current market conditions and volatility
- **Probability Analysis**: Estimates probability of profit for each strategy

### 🛡️ Comprehensive Risk Management
- **Multi-Layer Validation**: Structure, strategy-specific, risk limits, portfolio impact
- **Position Sizing**: Automatic contract calculation based on risk tolerance
- **Exposure Limits**: Portfolio-level risk concentration checks
- **Market Data Validation**: Real-time price and volatility verification

### ✋ Human Approval Workflow
- **Approval Queue**: All trades require explicit human approval
- **Risk Disclosure**: Clear explanation of risks, returns, and probabilities
- **Modification Requests**: Users can request changes before approval
- **Audit Trail**: Complete record of all decisions and modifications

## 🏗️ Architecture

```
User Voice/Text Input
         ↓
    NLU Router (LLM)
         ↓
   Intent Schema Validation
         ↓
  Strategy Translator
         ↓
   Risk Validator
         ↓
   Approval Flow
         ↓
    Execution (Future)
```

### Core Components

1. **NLU Router** (`nlu_router.py`): Natural language understanding with LLM integration
2. **Strategy Translator** (`strategy_translator.py`): Converts intents to executable strategies  
3. **Risk Validator** (`validator.py`): Multi-layer risk validation system
4. **Approval Flow** (`approval_flow.py`): Human approval and modification workflow
5. **Voice Interface** (`voice_interface.py`): Speech-to-text and text-to-speech
6. **AI Agent** (`ai_agent.py`): Main orchestrator coordinating all components

## 🚀 Quick Start

### 1. Installation

```bash
# Install core dependencies
pip install -r requirements_ai_agent.txt

# For voice features (optional)
pip install SpeechRecognition pyttsx3 pyaudio

# Set up OpenAI API key for LLM integration
export OPENAI_API_KEY="your-api-key-here"
```

### 2. Basic Usage

```python
from agents import create_ai_agent

# Create AI agent
agent = create_ai_agent(voice_enabled=True, auto_approve=False)

# Process natural language command
result = agent.process_user_input(
    "Generate low risk income from SPY this month"
)

print(f"Status: {result['status']}")
print(f"Strategy: {result['plan']['strategy']}")
print(f"Explanation: {result['explanation']}")
```

### 3. Voice Assistant Mode

```python
from agents import start_voice_trading_assistant

# Start voice assistant (say "trading assistant" to activate)
start_voice_trading_assistant(wake_word="trading assistant")
```

### 4. Demo Mode

```bash
# Run comprehensive demo
python demo_ai_agent.py

# Interactive testing mode
python demo_ai_agent.py interactive
```

## 💬 Example Conversations

### Low-Risk Income Generation
```
User: "Generate low risk income from SPY this month"

Agent: "I've created a Put Credit Spread strategy on SPY expiring November 15th. 
        This involves selling a $445 put and buying a $440 put for $0.80 credit per contract. 
        Maximum risk is 0.5% of portfolio with 85% probability of profit. 
        This plan requires your approval before execution."

User: [Approves via UI or voice]

Agent: "Plan approved! Strategy ready for execution."
```

### Bullish Strategy Request
```
User: "Create a bullish strategy on QQQ with moderate risk"

Agent: "I've designed a Long Call strategy on QQQ using $375 calls expiring November 15th. 
        Cost is $2.50 per contract with maximum risk of 1.2% of portfolio. 
        Break-even at $377.50 with unlimited upside potential. 
        Estimated 65% probability of profit."
```

### Risk Rejection Example
```
User: "Put my entire portfolio in TSLA options"

Agent: "I can't execute this request due to 3 risk concerns: 
        1) Exceeds maximum portfolio allocation of 20% per symbol. 
        2) Risk level 'high' exceeds user preference of 'moderate'. 
        3) Single position concentration violates diversification rules. 
        Please modify your request or adjust risk parameters."
```

## 🛠️ Configuration

### Environment Variables
```bash
# Required for LLM integration
OPENAI_API_KEY="your-openai-api-key"

# Optional configurations
AI_AGENT_VOICE_ENABLED="true"        # Enable voice interface
AI_AGENT_AUTO_APPROVE="false"        # Auto-approve very safe trades
AI_AGENT_DATA_DIR="data/agent"       # Data storage directory
AI_AGENT_LOG_LEVEL="INFO"            # Logging level
```

### Agent Configuration
```python
agent = AITradingAgent(
    data_dir=Path("custom/data/dir"),    # Custom data directory
    voice_enabled=True,                  # Enable voice interface
    auto_approve_safe_trades=False       # Auto-approve conservative trades
)
```

### Risk Limits (Configurable)
```python
# Default risk limits in validator.py
RISK_LIMITS = {
    "max_portfolio_risk_per_trade": 0.02,    # 2% max per trade
    "max_symbol_allocation": 0.20,           # 20% max per symbol  
    "min_probability_of_profit": 0.60,       # 60% minimum PoP
    "max_contracts_per_trade": 10,           # 10 contracts max
    "min_days_to_expiry": 7                  # 7 days minimum DTE
}
```

## 📊 Monitoring & Analytics

### Agent Status
```python
status = agent.get_agent_status()
print(f"Commands processed: {status['conversation_count']}")
print(f"Pending approvals: {status['pending_approvals']}")
print(f"Approval rate: {status['approval_stats']['approval_rate']}")
```

### Conversation History
```python
history = agent.get_conversation_history(limit=10)
for entry in history:
    print(f"{entry['timestamp']}: {entry['user_input']}")
    print(f"  Status: {entry['response']['status']}")
```

### Approval Analytics
```python
approval_stats = agent.approval_flow.get_approval_stats()
print(f"Total requests: {approval_stats['total_requests']}")
print(f"Approval rate: {approval_stats['approval_rate']:.1%}")
```

## 🔧 Advanced Features

### Custom Strategy Builders
```python
# Add custom strategy in strategy_translator.py
def build_custom_strategy(self, intent: Dict, market_ctx: Dict) -> Dict:
    """Build your custom options strategy."""
    return {
        "strategy": "custom_strategy",
        "legs": [...],  # Define option legs
        "risk_level": "moderate",
        "probability_of_profit": 0.70
    }
```

### Custom Validation Rules
```python
# Add custom validation in validator.py
def validate_custom_rule(self, plan: Dict) -> List[str]:
    """Add your custom validation logic."""
    errors = []
    if plan.get('custom_field') > threshold:
        errors.append("Custom rule violation")
    return errors
```

### LLM Provider Integration
```python
# Integrate alternative LLM in llm_client.py
def use_anthropic_claude(self, prompt: str) -> str:
    """Use Anthropic Claude instead of OpenAI."""
    # Implementation for Claude API
    pass
```

## 🧪 Testing

### Unit Tests
```bash
# Run unit tests (when implemented)
pytest tests/agents/

# Test specific component
pytest tests/agents/test_nlu_router.py -v
```

### Integration Testing
```bash
# Test complete workflow
python demo_ai_agent.py

# Test voice interface
python -c "from agents import VoiceInterface; VoiceInterface().test_voice_system()"
```

### Mock Mode for CI/CD
```python
# Disable voice and LLM for automated testing
agent = AITradingAgent(
    voice_enabled=False,  # No voice in CI
    auto_approve_safe_trades=True  # Auto-approve for testing
)
```

## 🚨 Safety & Risk Management

### Built-in Safety Features
- **Conservative Defaults**: All trades default to conservative risk levels
- **Multi-Layer Validation**: Structure → Strategy → Risk → Portfolio validation
- **Human Approval Required**: No automatic execution without explicit approval
- **Position Limits**: Maximum contracts and risk per trade
- **Diversification Rules**: Prevents over-concentration in single symbols

### Risk Disclosure
- **Clear Risk Metrics**: Maximum loss, probability of profit, break-even points
- **Strategy Explanation**: Plain English explanation of each trade
- **Market Context**: Current volatility and market conditions
- **Approval History**: Complete audit trail of all decisions

### Emergency Controls
- **Stop All Trading**: `agent.approval_flow.emergency_stop()`
- **Review Queue**: `agent.get_pending_approvals()`
- **Session Shutdown**: `agent.save_session_data()`

## 📈 Integration with EMO Options Bot

The AI Agent integrates seamlessly with the existing EMO Options Bot:

### Strategy Framework Integration
```python
# Uses existing strategy builders
from logic.strategies import IronCondorStrategy
from logic.risk_manager import RiskManager
from logic.portfolio import PortfolioSnapshot
```

### Database Integration
```python
# Stores plans and decisions in SQLite
from ops.db import DatabaseRouter
```

### Execution Integration (Future)
```python
# Will integrate with execution engine
from execution.broker_interface import BrokerInterface
```

## 🛣️ Roadmap

### Phase 1: Core AI Agent ✅
- [x] Natural language understanding with LLM integration
- [x] Strategy translation and risk validation  
- [x] Approval workflow and voice interface
- [x] Complete audit trail and session management

### Phase 2: Enhanced Intelligence (Q1 2024)
- [ ] Market sentiment analysis integration
- [ ] Advanced probability models
- [ ] Machine learning for strategy optimization
- [ ] Personalized risk profiling

### Phase 3: Advanced Features (Q2 2024)  
- [ ] Multi-asset strategy combinations
- [ ] Real-time market data integration
- [ ] Advanced order types and execution
- [ ] Portfolio rebalancing recommendations

### Phase 4: Enterprise Features (Q3 2024)
- [ ] Multi-user support and permissions
- [ ] Compliance reporting and audit logs
- [ ] API for third-party integrations
- [ ] Advanced analytics dashboard

## 📄 License & Disclaimer

This software is for educational and research purposes. Options trading involves substantial risk of loss. Users should:

- Understand options trading risks before use
- Start with paper trading and small positions
- Consult with financial advisors
- Never risk more than they can afford to lose

The AI agent provides suggestions, not financial advice. All trading decisions are the user's responsibility.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

- **Documentation**: See `/docs` directory for detailed guides
- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for questions and ideas
- **Email**: support@emo-options-bot.com (if available)

---

**🎯 Ready to revolutionize your options trading with AI?**

Start with `python demo_ai_agent.py` and experience the future of voice-driven trading!