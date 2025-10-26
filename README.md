# EMO Options Bot v2.0 - Enhanced Trading System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)]()

## 🚀 Overview

EMO Options Bot v2.0 is a comprehensive, institutional-grade options trading system with advanced database management, real-time monitoring, and professional-grade infrastructure.

### 🌟 Key Features

- **🗄️ Dual Database Architecture**: OPS (Operational) + Institutional databases
- **📊 Real-time Web Interface**: Professional HTML dashboard with auto-refresh
- **🔧 Advanced CLI Tools**: Comprehensive command-line interface for order management
- **🏥 Health Monitoring**: Live system health monitoring with REST APIs
- **🛡️ Risk Management**: Built-in risk scoring and compliance validation
- **📈 Institutional Integration**: Enterprise-grade order management and approval workflows
- **🔄 Backup & Recovery**: Comprehensive data backup and restore capabilities
- **⚡ Performance Optimized**: Efficient database operations and caching

## 🏗️ Architecture

```
EMO Options Bot v2.0
├── 📦 OPS Database (SQLite/PostgreSQL)
│   ├── Order Staging & Management
│   ├── Risk Assessment Engine  
│   └── Compliance Validation
├── 🏛️ Institutional Database
│   ├── Enterprise Order Management
│   ├── Approval Workflows
│   └── Audit Trails
├── 🌐 Web Interface (Port 8082)
│   ├── Order Dashboard
│   ├── Health Monitoring
│   └── Real-time Metrics
└── 🛠️ CLI Tools
    ├── Order Staging CLI
    ├── Database Manager
    └── Health Monitor
```

## 📋 Prerequisites

- **Python 3.8+** (3.11+ recommended)
- **pip** package manager
- **SQLite** (included with Python)
- **PostgreSQL** (optional, for production)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or extract the project
cd emo_options_bot_sqlite_plot_upgrade

# Install dependencies
pip install -r requirements.txt

# Run setup (initializes databases and validates system)
python setup.py --full
```

### 2. Start the System

```bash
# Start all services
python start_emo.py

# Or start components individually
python tools/emit_health.py --port 8082  # Health monitoring
python tools/stage_order_cli.py --help   # CLI tools
```

### 3. Access the Web Interface

- **Order Dashboard**: http://localhost:8082/orders.html
- **Health Status**: http://localhost:8082/health
- **System Metrics**: http://localhost:8082/metrics

## ✨ Key Features

### 🎯 Enhanced Orchestration System (`tools/runner.py`)
- **Health Monitoring Integration**: Real-time component health tracking
- **Order Staging Hooks**: Seamless integration with order management
- **Performance Metrics**: Comprehensive execution time and resource monitoring
- **Email Notifications**: Automated alerts for critical events
- **Backup Management**: Automated database backup with rotation
- **Error Recovery**: Robust error handling with graceful degradation

### 📊 Live Data Collection (`data/live_logger.py`)
- **Robust API Error Handling**: Intelligent retry logic with exponential backoff
- **Performance Monitoring**: Real-time metrics collection and reporting
- **Integration Hooks**: Seamless connection to runner system
- **Health Check Endpoints**: Status monitoring for operational dashboards
- **Configurable Symbols**: Dynamic symbol management for data collection
- **Rate Limit Handling**: Intelligent API rate limit management

### 🔄 Order Management Systems
- **Order Rotation** (`tools/rotate_staged_orders.py`): Date-based archival with configurable retention
- **Order Staging** (`tools/stage_order_cli.py`): Interactive order review and approval
- **Health Monitoring** (`tools/emit_health.py`): Component status tracking

### 🗄️ Enhanced Database Infrastructure
- **Database Router** (`db/router.py`): Environment-aware SQLite/PostgreSQL routing
- **Health Monitoring**: Connection pool management and health checks
- **Schema Management**: Automatic migration and version tracking
- **CLI Management**: Command-line database operations

### ✅ Environment & Validation
- **Environment Validator** (`tools/validate_env.py`): Multi-mode production readiness checks
- **Workspace Manager** (`workspace_config.py`): Comprehensive environment setup
- **Enhanced Configuration** (`src/utils/enhanced_config.py`): Type-safe configuration management

### 🧪 Testing & Quality Assurance
- **Comprehensive Test Suite** (`test_suite.py`): Unit, integration, and performance tests
- **Enhanced Build System** (`build.py`): Automated build, test, and deployment pipeline
- **Health Monitoring**: Real-time component status tracking

## 🚀 Quick Start

### 1. Environment Setup

```powershell
# Initialize workspace
python workspace_config.py --init

# Setup development environment
python workspace_config.py --setup-dev

# Verify installation
python workspace_config.py --health
```

### 2. Configuration

Copy and configure environment variables:

```powershell
# Copy development template
copy .env.dev .env

# Edit configuration (required)
notepad .env
```

**Required Environment Variables:**
```bash
# Core Configuration
EMO_ENV=dev
EMO_SQLITE_PATH=./ops/emo.sqlite
EMO_SYMBOLS=SPY,QQQ,AAPL

# API Credentials (required for live data)
ALPACA_KEY_ID=your_alpaca_key_id
ALPACA_SECRET_KEY=your_alpaca_secret_key

# Optional: Email Notifications
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASS=your_app_password
NOTIFY_EMAIL=notifications@example.com
```

### 3. Build & Test

```powershell
# Full build with tests
python build.py

# Quick build (skip tests)
python build.py --quick

# Run tests only
python test_suite.py
```

### 4. Run Components

```powershell
# Start health monitoring
python tools/emit_health.py

# Run live data collection
python data/live_logger.py

# Execute main orchestration
python tools/runner.py

# Manual order staging
python tools/stage_order_cli.py
```

## 🔧 Component Documentation

### 🎯 Main Orchestration (`tools/runner.py`)

Enhanced orchestration system with comprehensive monitoring:

```powershell
# Basic execution
python tools/runner.py

# With email notifications
python tools/runner.py --email-notifications

# Performance monitoring mode
python tools/runner.py --performance-monitoring

# Health integration mode
python tools/runner.py --health-integration
```

**Features:**
- Real-time health monitoring integration
- Performance metrics collection and reporting
- Automatic backup management with rotation
- Email notifications for critical events
- Order staging hooks for review workflow
- Robust error handling with recovery

### 📊 Live Data Collection (`data/live_logger.py`)

Enhanced live market data collector with error handling:

```powershell
# Start live data collection
python data/live_logger.py

# Specific symbols
python data/live_logger.py --symbols SPY,QQQ,AAPL

# Performance monitoring
python data/live_logger.py --performance-monitoring

# Health check
python data/live_logger.py --health-check
```

**Features:**
- Robust API error handling with retry logic
- Real-time performance metrics collection
- Integration hooks for runner system
- Health check endpoints for monitoring
- Configurable symbol lists
- Rate limit intelligent handling

### 🔄 Order Management (`tools/rotate_staged_orders.py`)

Automated order archival and cleanup:

```powershell
# Archive orders older than 7 days
python tools/rotate_staged_orders.py --archive --retention-days 7

# Preview what would be archived (dry run)
python tools/rotate_staged_orders.py --archive --dry-run

# Clean up old archives
python tools/rotate_staged_orders.py --cleanup --archive-retention-days 30
```

### ✅ Environment Validation (`tools/validate_env.py`)

Production readiness validation:

```powershell
# Validate development environment
python tools/validate_env.py dev

# Validate production with all checks
python tools/validate_env.py prod --check-database --check-broker

# Generate validation report
python tools/validate_env.py staging --output-format json
```

### 🏗️ Build System (`build.py`)

Comprehensive build and deployment pipeline:

```powershell
# Full development build
python build.py

# Production deployment
python build.py --deploy prod

# Staging deployment
python build.py --deploy staging

# Test-only build
python build.py --test-only

# Environment validation only
python build.py --validate
```

**Build Phases:**
1. Environment validation and setup
2. Component dependency checking  
3. Database migration and health validation
4. Comprehensive testing (unit/integration/performance)
5. Live logger integration and validation
6. Workspace configuration and validation
7. Health monitoring setup
8. Deployment readiness verification

### 🧪 Test Suite (`test_suite.py`)

Comprehensive testing framework:

```powershell
# Run all tests
python test_suite.py

# Unit tests only
python test_suite.py --unit

# Integration tests
python test_suite.py --integration

# Performance benchmarking
python test_suite.py --performance

# Test specific component
python test_suite.py --component live_logger
```

## 🌍 Multi-Environment Support

### Development Environment
- **Purpose**: Local development and testing
- **Configuration**: `.env.dev`
- **Features**: Order staging enabled, email notifications disabled, auto-backup enabled
- **Database**: Local SQLite
- **API**: Paper trading enabled

### Staging Environment  
- **Purpose**: Pre-production testing
- **Configuration**: `.env.staging`
- **Features**: Order staging enabled, email notifications enabled, comprehensive monitoring
- **Database**: Staging SQLite or PostgreSQL
- **API**: Paper trading (Alpaca Paper API)

### Production Environment
- **Purpose**: Live trading operations
- **Configuration**: `.env.prod`
- **Features**: Order staging disabled, all monitoring enabled, email notifications enabled
- **Database**: Production PostgreSQL or SQLite
- **API**: Live trading (Alpaca Live API)

## 📊 Monitoring & Health

### Health Endpoints
- **Component Health**: `python tools/emit_health.py`
- **Live Logger Health**: `python data/live_logger.py --health-check`
- **Workspace Health**: `python workspace_config.py --health`

### Performance Monitoring
- **Runner Metrics**: Execution time, resource usage, component performance
- **Live Logger Metrics**: API response times, error rates, data collection rates
- **Database Metrics**: Query performance, connection health, schema status

### Error Handling
- **Robust Retry Logic**: Exponential backoff for API failures
- **Graceful Degradation**: Continues operation with reduced functionality
- **Error Reporting**: Comprehensive logging with email notifications
- **Recovery Procedures**: Automatic recovery from transient failures

## 🔐 Security Features

### Configuration Security
- **Environment Separation**: Distinct configurations for dev/staging/prod
- **Credential Management**: Secure handling of API keys and secrets
- **Validation**: Environment-specific security validations

### Data Security
- **Database Encryption**: SQLite encryption support (optional)
- **API Security**: Secure credential storage and transmission
- **Backup Security**: Encrypted backup storage (configurable)

## 🛠️ Development Workflow

### 1. Setup Development Environment
```powershell
python workspace_config.py --setup-dev
python build.py --validate
```

### 2. Make Changes
```powershell
# Edit code
# Run tests for affected components
python test_suite.py --component your_component
```

### 3. Test Integration
```powershell
# Run integration tests
python test_suite.py --integration

# Validate environment
python tools/validate_env.py dev
```

### 4. Deploy to Staging
```powershell
python build.py --deploy staging
python tools/validate_env.py staging --check-database
```

### 5. Deploy to Production
```powershell
python build.py --deploy prod
python tools/validate_env.py prod --check-database --check-broker
```

## 📈 Performance Optimization

### Database Performance
- **Connection Pooling**: Efficient database connection management
- **Query Optimization**: Optimized database queries and indexing
- **Health Monitoring**: Real-time database performance tracking

### API Performance
- **Rate Limiting**: Intelligent API rate limit management
- **Retry Logic**: Exponential backoff for failed requests
- **Caching**: Response caching for frequently accessed data

### System Performance
- **Metrics Collection**: Real-time performance monitoring
- **Resource Management**: Efficient memory and CPU usage
- **Background Processing**: Non-blocking operations for better responsiveness

## 🚨 Troubleshooting

### Common Issues

#### Build Failures
```powershell
# Check environment
python build.py --validate

# Check component health
python workspace_config.py --health

# Run tests to identify issues
python test_suite.py --verbose
```

#### Database Issues
```powershell
# Test database connection
python -c "from db.router import test_connection; print(test_connection())"

# Reset database (development only)
rm ops/emo.sqlite
python workspace_config.py --setup-dev
```

#### API Connection Issues
```powershell
# Validate API credentials
python tools/validate_env.py dev --check-broker

# Test live logger connectivity
python data/live_logger.py --health-check
```

#### Configuration Issues
```powershell
# Validate configuration
python tools/validate_env.py dev

# Check environment variables
python -c "from src.utils.enhanced_config import Config; c = Config(); print(c.get('EMO_ENV'))"
```

### Log Analysis
- **Application Logs**: `logs/` directory
- **Build Reports**: `build_report_*.json` files
- **Health Reports**: Component health endpoints
- **Performance Reports**: Generated by build system

## 🔧 Customization

### Adding New Components
1. Create component in appropriate directory
2. Add to `workspace_config.py` component list
3. Add tests in `test_suite.py`
4. Update build system in `build.py`

### Environment Configuration
1. Add new environment to `workspace_config.py`
2. Create environment template
3. Update validation in `tools/validate_env.py`
4. Add deployment support in `build.py`

### Monitoring Integration
1. Implement health check interface
2. Add to health monitoring system
3. Update performance tracking
4. Add to build validation

## 📚 API Reference

### Configuration System
```python
from src.utils.enhanced_config import Config
config = Config()
value = config.get("SETTING_NAME", "default_value")
bool_value = config.as_bool("BOOLEAN_SETTING")
int_value = config.as_int("INTEGER_SETTING")
```

### Database Router
```python
from db.router import DatabaseRouter
router = DatabaseRouter()
connection = router.get_connection()
health = router.test_connection()
```

### Live Logger
```python
from data.live_logger import LiveLogger
logger = LiveLogger()
health = logger.health_check()
report = logger.get_performance_report()
```

## 🤝 Contributing

1. **Fork the Repository**: Create your own fork for development
2. **Create Feature Branch**: `git checkout -b feature/your-feature`
3. **Make Changes**: Implement your feature with tests
4. **Run Tests**: `python test_suite.py`
5. **Validate Build**: `python build.py`
6. **Submit Pull Request**: With comprehensive description

### Code Standards
- **Type Hints**: Use type hints for all public APIs
- **Documentation**: Comprehensive docstrings and comments
- **Error Handling**: Robust error handling with logging
- **Testing**: Unit and integration tests for all functionality

## 📝 License

This project is licensed under the MIT License. See LICENSE file for details.

## 📞 Support

For support and questions:
- **Issues**: GitHub Issues for bug reports and feature requests
- **Documentation**: This README and inline code documentation
- **Health Monitoring**: Built-in health check endpoints
- **Logs**: Comprehensive logging for troubleshooting

---

**Built with ❤️ for robust, production-ready EMO Options Bot operations**