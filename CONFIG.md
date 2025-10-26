# EMO Options Bot Configuration Guide

This guide provides comprehensive configuration instructions for development, staging, and production environments.

## Quick Start

1. **Copy environment template:**
   ```powershell
   Copy-Item .env.example .env
   ```

2. **Edit .env with your settings:**
   - Set `ALPACA_KEY_ID` and `ALPACA_SECRET_KEY`
   - Choose environment: `EMO_ENV=development|staging|production`
   - Configure database backend if needed

3. **Run setup:**
   ```powershell
   .\scripts\setup.ps1
   ```

## Environment Modes

### Development (`EMO_ENV=development`)
- **Database**: SQLite (local file)
- **Broker**: Paper trading only
- **Orders**: Staged by default (`EMO_STAGE_ORDERS=1`)
- **Data**: Historical data, limited live feeds
- **Safety**: Maximum safety features enabled

**Recommended settings:**
```env
EMO_ENV=development
EMO_DB_BACKEND=auto
EMO_STAGE_ORDERS=1
EMO_LIVE_DATA=0
EMO_DEBUG=1
```

### Staging (`EMO_ENV=staging`)
- **Database**: SQLite or TimescaleDB
- **Broker**: Paper trading with live data
- **Orders**: Can be staged or live (configurable)
- **Data**: Live data feeds enabled
- **Testing**: Production-like environment

**Recommended settings:**
```env
EMO_ENV=staging
EMO_DB_BACKEND=auto
EMO_STAGE_ORDERS=0
EMO_LIVE_DATA=1
EMO_ML_ENABLE=1
```

### Production (`EMO_ENV=production`)
- **Database**: TimescaleDB (required)
- **Broker**: Live trading
- **Orders**: Live execution (staging disabled)
- **Data**: Full live data feeds
- **Monitoring**: All monitoring enabled

**Required settings:**
```env
EMO_ENV=production
EMO_DB_BACKEND=timescaledb
EMO_STAGE_ORDERS=0
EMO_LIVE_DATA=1
PG_HOST=your-timescale-host
PG_USER=your-db-user
PG_PASSWORD=your-db-password
```

## Configuration Categories

### Database Configuration

The Enhanced Database Router automatically selects the appropriate database backend:

| Setting | Description | Values |
|---------|-------------|--------|
| `EMO_DB_BACKEND` | Database backend selection | `auto`, `sqlite`, `timescaledb` |
| `SQLITE_PATH` | SQLite database file path | `./data/emo.sqlite` |
| `PG_HOST` | PostgreSQL/TimescaleDB host | `localhost` |
| `PG_PORT` | Database port | `5432` |
| `PG_DB` | Database name | `emo` |
| `PG_USER` | Database user | `emo_user` |
| `PG_PASSWORD` | Database password | (secure password) |

**Database Selection Logic:**
- `auto` + `EMO_ENV=development` → SQLite
- `auto` + `EMO_ENV=production` → TimescaleDB
- `auto` + `EMO_ENV=staging` → SQLite (unless `PG_HOST` is set)

### Broker Configuration

| Setting | Description | Values |
|---------|-------------|--------|
| `EMO_BROKER` | Broker adapter | `alpaca`, `mock` |
| `ALPACA_KEY_ID` | Alpaca API key | Your API key |
| `ALPACA_SECRET_KEY` | Alpaca secret key | Your secret |
| `ALPACA_API_BASE` | API endpoint | Paper: `https://paper-api.alpaca.markets`<br>Live: `https://api.alpaca.markets` |
| `ALPACA_DATA_URL` | Data feed URL | `https://data.alpaca.markets/v2` |

### Trading & Risk Management

| Setting | Description | Default |
|---------|-------------|---------|
| `EMO_STAGE_ORDERS` | Stage orders instead of executing | `1` (safe default) |
| `EMO_LIVE_DATA` | Enable live data feeds | `0` (development) |
| `EMO_SYMBOLS` | Default symbols to monitor | `SPY,QQQ,IWM` |
| `EMO_MAX_POSITION_SIZE` | Maximum position size ($) | `10000` |
| `EMO_MAX_DAILY_LOSS` | Daily loss limit ($) | `1000` |
| `SHOCK_ALERT_THRESHOLD` | Market shock alert level | `0.65` |

### ML & AI Features

| Setting | Description | Values |
|---------|-------------|--------|
| `EMO_ML_ENABLE` | Enable ML models | `1` (enabled), `0` (disabled) |
| `EMO_ML_RETRAIN_CRON` | Retraining schedule | `weekly`, `daily`, `off` |
| `OPENAI_API_KEY` | OpenAI API key (optional) | Your API key |
| `EMO_LLM_MODEL` | LLM model to use | `gpt-4`, `gpt-3.5-turbo` |
| `EMO_LLM_ENABLE` | Enable LLM features | `0` (disabled by default) |

### Services & Monitoring

| Setting | Description | Default |
|---------|-------------|---------|
| `EMO_HEALTH_PORT` | Health check endpoint port | `8082` |
| `EMO_DASHBOARD_PORT` | Dashboard server port | `8083` |
| `EMO_DASHBOARD_AUTO_REFRESH` | Dashboard refresh interval (seconds) | `30` |
| `EMO_LOG_LEVEL` | Logging verbosity | `INFO` |
| `EMO_LOG_FILE` | Log file path | `./logs/emo.log` |

### Alerts & Notifications

| Setting | Description | Example |
|---------|-------------|---------|
| `SMTP_SERVER` | Email server | `smtp.gmail.com` |
| `SMTP_PORT` | Email server port | `587` |
| `SMTP_USER` | Email username | `your-email@gmail.com` |
| `SMTP_PASS` | Email password/app password | `your-app-password` |
| `ALERT_EMAIL` | Alert recipient email | `alerts@yourcompany.com` |

## Security Best Practices

### 1. Environment File Security
- **Never commit `.env` files** to source control
- Use `.env.example` as a template
- Store production secrets in secure credential management

### 2. API Key Management
- Use **paper trading keys** for development
- Rotate API keys regularly
- Monitor API key usage and permissions

### 3. Database Security
- Use **strong passwords** for database users
- Restrict database access by IP when possible
- Enable SSL/TLS for database connections in production

### 4. Network Security
- Bind dashboard/health endpoints to localhost in development
- Use reverse proxy with authentication in production
- Monitor and log all API access

## Environment-Specific Configurations

### Development Environment
```env
# .env.dev
EMO_ENV=development
EMO_DB_BACKEND=sqlite
EMO_STAGE_ORDERS=1
EMO_LIVE_DATA=0
EMO_DEBUG=1
EMO_LOG_LEVEL=DEBUG
ALPACA_API_BASE=https://paper-api.alpaca.markets
```

### Staging Environment
```env
# .env.staging
EMO_ENV=staging
EMO_DB_BACKEND=auto
EMO_STAGE_ORDERS=0
EMO_LIVE_DATA=1
EMO_ML_ENABLE=1
EMO_LOG_LEVEL=INFO
ALPACA_API_BASE=https://paper-api.alpaca.markets
```

### Production Environment
```env
# .env.prod
EMO_ENV=production
EMO_DB_BACKEND=timescaledb
EMO_STAGE_ORDERS=0
EMO_LIVE_DATA=1
EMO_ML_ENABLE=1
EMO_HEALTH_ENABLE=1
EMO_DASHBOARD_ENABLE=1
EMO_LOG_LEVEL=WARNING
ALPACA_API_BASE=https://api.alpaca.markets
PG_HOST=your-production-db
PG_USER=emo_prod
PG_PASSWORD=secure-production-password
```

## Validation & Testing

The build system includes configuration validation:

### 1. Required Variables Check
- Validates all required environment variables are set
- Checks API key format and permissions
- Verifies database connectivity

### 2. Environment Consistency
- Ensures configuration matches selected environment
- Validates database backend availability
- Checks service port conflicts

### 3. Security Validation
- Warns about insecure configurations
- Validates SSL/TLS settings in production
- Checks file permissions

## Troubleshooting

### Common Configuration Issues

**Database Connection Errors:**
- Verify `PG_HOST`, `PG_PORT`, `PG_USER`, `PG_PASSWORD`
- Check database service is running
- Ensure database user has required permissions

**API Authentication Failures:**
- Verify `ALPACA_KEY_ID` and `ALPACA_SECRET_KEY`
- Check API key permissions and status
- Ensure correct `ALPACA_API_BASE` endpoint

**Service Port Conflicts:**
- Check if ports `8082`, `8083` are available
- Modify `EMO_HEALTH_PORT`, `EMO_DASHBOARD_PORT` if needed
- Use `netstat -an` to check port usage

**Order Execution Issues:**
- Check `EMO_STAGE_ORDERS` setting
- Verify broker configuration and permissions
- Review risk management limits

### Configuration Validation Commands

```powershell
# Validate configuration
python scripts\validate_config.py

# Test database connectivity
python scripts\test_database.py

# Check API connectivity
python scripts\test_broker.py

# Full system health check
python scripts\health_check.py
```

## Advanced Configuration

### Custom Symbol Lists
```env
# Multiple symbol sets
EMO_SYMBOLS_MAIN=SPY,QQQ,IWM
EMO_SYMBOLS_TECH=AAPL,MSFT,GOOGL,AMZN
EMO_SYMBOLS_CRYPTO=BTCUSD,ETHUSD
```

### Performance Tuning
```env
# Database connection pooling
EMO_DB_POOL_SIZE=10
EMO_DB_MAX_OVERFLOW=20
EMO_DB_POOL_TIMEOUT=30

# API rate limiting
EMO_API_RATE_LIMIT=60
EMO_API_BURST_LIMIT=10
```

### Custom Data Sources
```env
# Additional data providers
EMO_DATA_PROVIDERS=alpaca,polygon,iex
POLYGON_API_KEY=your-polygon-key
IEX_API_KEY=your-iex-key
```

For additional configuration options and advanced setups, refer to the specific component documentation in the `docs/` directory.