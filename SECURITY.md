# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Security Considerations

### Financial Risk

⚠️ **IMPORTANT**: This software deals with financial trading and options, which involve substantial risk. Users should:

- Always use paper trading mode for testing
- Never trade with funds you cannot afford to lose
- Set appropriate risk limits in configuration
- Review all staged orders before approval
- Understand options trading risks before using this system

### API Keys and Credentials

- Never commit API keys, tokens, or credentials to version control
- Use environment variables or secure configuration management
- Rotate API keys regularly
- Use minimum required permissions for API keys
- Store credentials securely (use password managers, secret vaults)

### Data Security

- Market data and trading data should be treated as sensitive
- Portfolio information should be encrypted at rest if persisted
- Use HTTPS for all external API communications
- Validate all input data to prevent injection attacks

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### Do Not

- **DO NOT** open a public GitHub issue for security vulnerabilities
- **DO NOT** discuss the vulnerability publicly until it has been addressed

### Do

1. **Email** security concerns to the maintainer (details in GitHub profile)
2. **Include** the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

3. **Wait** for acknowledgment (typically within 48 hours)

### What to Expect

1. **Acknowledgment**: We'll confirm receipt within 48 hours
2. **Assessment**: We'll assess the vulnerability and determine severity
3. **Fix**: We'll work on a fix and keep you updated on progress
4. **Disclosure**: Once fixed, we'll coordinate public disclosure
5. **Credit**: You'll be credited in the security advisory (if desired)

## Security Best Practices for Users

### Configuration

```python
# Good: Use environment variables
config = Config(
    ai=AIConfig(
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
)

# Bad: Hard-code API keys
config = Config(
    ai=AIConfig(
        openai_api_key="your-api-key-here"  # NEVER DO THIS
    )
)
```

### Risk Management

Always configure appropriate risk limits:

```python
config = Config(
    risk=RiskConfig(
        max_position_size=1000.0,        # Limit per position
        max_portfolio_exposure=5000.0,   # Total portfolio limit
        max_loss_per_trade=100.0,        # Max loss per trade
        max_loss_per_day=500.0,          # Daily loss limit
        enable_risk_checks=True          # NEVER disable in production
    )
)
```

### Paper Trading

Always start with paper trading:

```python
config = Config(
    trading=TradingConfig(
        enable_paper_trading=True,       # Use paper trading
        require_manual_approval=True      # Require approval
    )
)
```

### Input Validation

Be cautious with natural language input:

```python
# The bot validates input, but be aware of:
# - Extremely large quantities
# - Unrealistic strike prices
# - Malformed commands

# Always review staged orders before approval
strategies = bot.get_staged_strategies()
for strategy in strategies:
    print(f"Review: {strategy['name']}")
    print(f"Max Risk: ${strategy['max_risk']}")
```

## Known Security Considerations

### 1. API Rate Limits

The bot uses external APIs (OpenAI, Yahoo Finance) which have rate limits:
- Implement appropriate delays between requests
- Cache market data when possible
- Handle rate limit errors gracefully

### 2. Market Data Accuracy

Market data from free sources may be delayed or inaccurate:
- Verify prices before execution
- Use official broker data for actual trading
- Be aware of data latency

### 3. AI-Generated Strategies

AI-parsed strategies should always be reviewed:
- AI may misinterpret commands
- Always verify parsed parameters
- Use manual approval workflow

### 4. Order Staging

The order staging system is a security feature:
- Never bypass approval workflow in production
- Review all risk assessments
- Verify order details match intent

## Dependency Security

We monitor dependencies for known vulnerabilities:
- Dependencies are specified with minimum versions
- Regular security audits using GitHub advisory database
- Update dependencies promptly when vulnerabilities are discovered

### Checking Dependencies

```bash
# Check for vulnerabilities (requires pip-audit)
pip install pip-audit
pip-audit

# Or use GitHub's Dependabot (enabled by default)
```

## Development Security

### Code Review

All code changes go through review:
- Security-sensitive changes require extra scrutiny
- Test security features thoroughly
- Never disable security checks without justification

### Testing

Security-related code must have tests:
- Test risk limit enforcement
- Test input validation
- Test authentication/authorization
- Test error handling

## Incident Response

In case of a security incident:

1. **Contain**: Stop affected services immediately
2. **Assess**: Determine scope and impact
3. **Notify**: Inform affected users
4. **Fix**: Apply patches and updates
5. **Document**: Record incident details
6. **Review**: Conduct post-incident review

## Compliance

### Financial Regulations

Users are responsible for compliance with:
- Securities regulations in their jurisdiction
- Broker terms of service
- Tax reporting requirements
- Know Your Customer (KYC) requirements

This software is for **educational and research purposes**. Users must:
- Understand applicable regulations
- Consult with financial/legal advisors
- Use at their own risk

## Updates

This security policy is reviewed and updated regularly. Last updated: 2024-12-15

## Contact

For security concerns: See GitHub profile for contact information

---

**Remember**: Security is everyone's responsibility. When in doubt, ask!
