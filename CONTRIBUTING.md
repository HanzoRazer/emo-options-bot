# Contributing to EMO Options Bot

Thank you for your interest in contributing to EMO Options Bot! This document provides guidelines and instructions for contributing.

## Code of Conduct

Be respectful, professional, and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- Virtual environment tool (venv, conda, etc.)

### Setting Up Development Environment

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/emo-options-bot.git
   cd emo-options-bot
   ```

3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

5. Copy environment template:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Development Workflow

### Creating a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

Use descriptive branch names:
- `feature/` for new features
- `bugfix/` for bug fixes
- `docs/` for documentation
- `refactor/` for code refactoring

### Making Changes

1. Write clean, readable code following PEP 8
2. Add docstrings to all functions, classes, and modules
3. Include type hints where appropriate
4. Write tests for new functionality
5. Update documentation as needed

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=emo_options_bot --cov-report=html

# Run specific test file
pytest tests/unit/test_nlp_processor.py

# Run with verbose output
pytest -v
```

### Code Style

We follow PEP 8 with some specific conventions:

- Line length: 100 characters maximum
- Use 4 spaces for indentation
- Use double quotes for strings
- Use trailing commas in multi-line structures

### Commit Messages

Write clear, descriptive commit messages:

```
Short summary (50 chars or less)

More detailed explanation if necessary. Wrap at 72 characters.
Explain the problem that this commit is solving, and why this
approach was chosen.

- Bullet points are okay
- Use present tense ("Add feature" not "Added feature")
- Reference issues: Fixes #123
```

### Submitting a Pull Request

1. Push your changes to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Create a Pull Request on GitHub
3. Provide a clear description of the changes
4. Link any relevant issues
5. Wait for review and address feedback

## Testing Guidelines

### Unit Tests

- Test individual components in isolation
- Mock external dependencies
- Use descriptive test names
- Aim for high code coverage (>80%)

Example:
```python
def test_risk_manager_rejects_oversized_position():
    """Test that risk manager rejects positions exceeding limits."""
    config = RiskConfig(max_position_size=100.0)
    manager = RiskManager(config)
    
    # Create strategy exceeding limit
    strategy = create_test_strategy(max_risk=Decimal("500"))
    
    assessment = manager.assess_strategy(strategy)
    
    assert not assessment.approved
    assert "position size" in assessment.violations[0].lower()
```

### Integration Tests

- Test complete workflows
- Test component interactions
- Use realistic scenarios

### Test Structure

```
tests/
├── unit/               # Unit tests for individual components
│   ├── test_nlp_processor.py
│   ├── test_strategy_engine.py
│   ├── test_risk_manager.py
│   └── test_order_stager.py
└── integration/        # Integration tests
    └── test_bot_integration.py
```

## Documentation

### Docstring Format

Use Google-style docstrings:

```python
def calculate_risk(strategy: TradingStrategy) -> Decimal:
    """
    Calculate total risk for a trading strategy.
    
    Args:
        strategy: Trading strategy to analyze
        
    Returns:
        Total risk amount in dollars
        
    Raises:
        ValueError: If strategy has no orders
    """
    pass
```

### README Updates

Update README.md when adding:
- New features
- Configuration options
- Usage examples
- API changes

## Areas for Contribution

We welcome contributions in these areas:

### High Priority

- [ ] Broker integrations (TD Ameritrade, Interactive Brokers)
- [ ] Real-time Greeks calculation
- [ ] Web dashboard interface
- [ ] Backtesting engine

### Medium Priority

- [ ] Advanced charting and visualization
- [ ] Machine learning for strategy optimization
- [ ] Mobile app
- [ ] Alert system (SMS/email/push)

### Always Welcome

- Bug fixes
- Documentation improvements
- Test coverage improvements
- Performance optimizations
- Code refactoring

## Security

### Reporting Security Issues

**Do not open public issues for security vulnerabilities.**

Email security concerns to: [maintainer email]

### Security Best Practices

- Never commit API keys or credentials
- Use environment variables for sensitive data
- Validate all user inputs
- Keep dependencies updated
- Follow principle of least privilege

## Questions?

- Open an issue with the "question" label
- Join our discussions on GitHub
- Check existing issues and pull requests

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to EMO Options Bot! 🚀
