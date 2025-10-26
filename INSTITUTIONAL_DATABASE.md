# EMO Options Bot - Institutional Database Infrastructure

## Overview

The EMO Options Bot has been enhanced with an institutional-grade database infrastructure that provides:

- **Enhanced Database Models**: SQLAlchemy 2.0+ models with comprehensive typing and institutional features
- **Migration System**: Schema versioning with TimescaleDB support and rollback capabilities  
- **Enhanced Database Router**: Environment-aware routing with connection pooling and health monitoring
- **Order Review System**: Comprehensive order analysis with HTML reporting
- **Institutional Integration**: Unified system monitoring and reporting
- **Legacy Compatibility**: Backward compatibility with existing systems

## Architecture

### Database Components

```
src/database/
├── enhanced_models.py          # SQLAlchemy 2.0+ models with institutional features
├── migrations.py               # Migration system with TimescaleDB support
├── router_v2.py               # Enhanced database router with health monitoring
├── enhanced_router.py         # Legacy compatibility wrapper
├── order_review.py            # Order analysis and HTML reporting
└── institutional_integration.py # Unified system integration and monitoring
```

### Key Features

#### 1. Enhanced Database Models (`enhanced_models.py`)

- **StagedOrder**: Order staging with workflow tracking
- **MarketEvent**: Time-series market data with optimization
- **ExecutedOrder**: Order execution tracking with performance analysis
- **StrategyPerformance**: Strategy metrics with risk assessment
- **SystemHealth**: Health monitoring with metadata tracking

Features:
- SQLAlchemy 2.0+ compatibility
- Comprehensive type hints
- Database indexes for performance
- JSON metadata fields
- Audit trails and timestamps

#### 2. Migration System (`migrations.py`)

- Schema versioning and rollback
- TimescaleDB hypertable support
- Retention policy management
- Legacy data migration
- Environment-aware migrations

#### 3. Enhanced Database Router (`router_v2.py`)

- Environment-aware database selection
- Connection pooling and health monitoring
- Automatic failover and recovery
- Performance monitoring
- Multi-database support

#### 4. Order Review System (`order_review.py`)

- Comprehensive order analysis
- Risk assessment and compliance checking
- HTML report generation
- Performance metrics calculation
- Real-time monitoring integration

#### 5. Institutional Integration (`institutional_integration.py`)

- Unified system health monitoring
- Comprehensive HTML reporting
- Component status tracking
- Performance dashboards
- Auto-refresh capabilities

## Environment Configuration

### Development Environment

```bash
# .env.dev
EMO_ENV=dev
EMO_DB_URL=sqlite:///data/emo_dev.sqlite
EMO_DB_DEBUG=false
```

### Production Environment

```bash
# .env.prod
EMO_ENV=prod
EMO_DB_URL=postgresql+psycopg://user:pass@host:5432/emo_prod
EMO_DB_DEBUG=false
EMO_DB_POOL_SIZE=10
```

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `EMO_ENV` | Environment (dev/staging/prod) | dev | No |
| `EMO_DB_URL` | Database URL override | Auto-detected | No |
| `EMO_DB_DEBUG` | Enable SQL query logging | false | No |
| `EMO_DB_POOL_SIZE` | Connection pool size | 5 | No |
| `POSTGRES_URL` | PostgreSQL connection URL | None | Prod only |
| `EMO_SQLITE_PATH` | SQLite database path | data/emo_{env}.sqlite | No |

## Usage

### Basic Database Operations

```python
from src.database.router_v2 import get_enhanced_router

# Get enhanced router
router = get_enhanced_router()

# Test connection
if router.test_connection():
    print("Database connection successful")

# Get connection
with router.get_connection() as conn:
    result = conn.execute(text("SELECT 1"))
    print(result.scalar())
```

### Legacy Compatibility

```python
from src.database.enhanced_router import DBRouter

# Initialize legacy router (uses enhanced router internally)
DBRouter.init()

# Test connection
if DBRouter.test_connection():
    print("Legacy compatibility working")

# Get engine
engine = DBRouter.engine()
```

### Order Analysis

```python
from src.database.order_review import EnhancedOrderReview

# Create order review instance
order_review = EnhancedOrderReview()

# Sample orders
orders = [
    {
        'symbol': 'AAPL',
        'type': 'limit',
        'quantity': 100,
        'value': 15000,
        'status': 'executed',
        'created_at': '2024-10-25T10:00:00Z'
    }
]

# Analyze orders
metrics = order_review.analyze_orders(orders)
print(f"Risk score: {metrics.risk_score}")
print(f"Compliance score: {metrics.compliance_score}")

# Generate HTML report
report_path = order_review.save_report(orders)
print(f"Report saved: {report_path}")
```

### System Integration

```python
from src.database.institutional_integration import InstitutionalIntegration

# Create integration instance
integration = InstitutionalIntegration()

# Check system health
status = integration.check_system_health()
print(f"System health: {status.system_health_score}%")

# Generate institutional report
report_path = integration.save_institutional_report()
print(f"Institutional report: {report_path}")

# Run full system check
success = integration.run_full_system_check()
```

## Database Schema

### Core Tables

#### staged_orders
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| symbol | String(20) | Trading symbol |
| order_type | String(50) | Order type |
| quantity | Decimal | Order quantity |
| price | Decimal | Order price |
| status | String(20) | Order status |
| workflow_state | JSON | Workflow tracking |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

#### market_events
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| symbol | String(20) | Trading symbol |
| event_type | String(50) | Event type |
| timestamp | DateTime | Event timestamp |
| price | Decimal | Event price |
| volume | Integer | Event volume |
| metadata | JSON | Additional event data |

#### executed_orders
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| staged_order_id | UUID | Reference to staged order |
| execution_price | Decimal | Execution price |
| execution_quantity | Decimal | Executed quantity |
| execution_timestamp | DateTime | Execution time |
| fees | Decimal | Transaction fees |
| performance_metrics | JSON | Performance data |

#### strategy_performance
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| strategy_name | String(100) | Strategy identifier |
| period_start | DateTime | Performance period start |
| period_end | DateTime | Performance period end |
| total_return | Decimal | Total return |
| sharpe_ratio | Decimal | Sharpe ratio |
| max_drawdown | Decimal | Maximum drawdown |
| risk_metrics | JSON | Risk assessment data |

#### system_health
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| component_name | String(100) | Component identifier |
| health_score | Decimal | Health score (0-100) |
| status | String(20) | Component status |
| timestamp | DateTime | Health check time |
| metrics | JSON | Health metrics |
| metadata | JSON | Additional health data |

## Migration Management

### Running Migrations

```python
from src.database.migrations import run_migrations
from src.database.router_v2 import get_enhanced_router

# Get database engine
router = get_enhanced_router()
engine = router.get_engine()

# Run migrations
success = run_migrations(engine)
print(f"Migration successful: {success}")
```

### Creating Migrations

Migrations are automatically handled by the enhanced migration system. The system will:

1. Create base tables if they don't exist
2. Apply schema updates for new columns/indexes
3. Configure TimescaleDB hypertables for time-series data
4. Set up retention policies for data management

### TimescaleDB Configuration

For production environments using TimescaleDB:

```sql
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Hypertables are automatically created by the migration system
-- for time-series tables like market_events and system_health
```

## Build System Integration

The institutional database infrastructure is integrated into the build system:

```bash
# Validate institutional infrastructure
python build.py --validate

# Full build with institutional components
python build.py

# Deploy with institutional infrastructure
python build.py --deploy prod
```

### Build Validation Checks

- Enhanced database router functionality
- Legacy database compatibility
- Order review system functionality
- Institutional integration health
- Migration system availability

## Monitoring and Reporting

### Health Monitoring

The system provides comprehensive health monitoring:

1. **Database Health**: Connection status, query performance, error rates
2. **Component Health**: Individual component status and metrics
3. **System Health**: Overall system performance and availability
4. **Migration Status**: Schema version and migration history

### HTML Reports

#### Institutional Report
- System-wide health dashboard
- Component status overview
- Performance metrics
- Environment information
- Auto-refresh capabilities

#### Order Review Report
- Order analysis dashboard
- Risk assessment metrics
- Compliance scoring
- Performance analytics
- Recent order activity

### Report Generation

Reports are automatically generated in:
- `data/integration/` - Institutional reports
- `data/reports/` - Order review reports

### Accessing Reports

Reports are saved as HTML files and can be opened in any web browser:

```bash
# Example report paths
data/integration/institutional_report_20241025_215517.html
data/reports/order_review_20241025_215517.html
```

## Performance Optimization

### Database Optimization

1. **Indexes**: Comprehensive indexing on frequently queried columns
2. **Connection Pooling**: Efficient connection management
3. **Query Optimization**: Optimized SQLAlchemy queries
4. **Time-series Optimization**: TimescaleDB hypertables for market data

### Monitoring Optimization

1. **Health Check Intervals**: Configurable health check frequency
2. **Report Caching**: Intelligent report caching
3. **Resource Management**: Efficient memory and CPU usage
4. **Background Processing**: Non-blocking health checks

## Security

### Database Security

1. **Connection Security**: Secure database connections
2. **Environment Isolation**: Separate environments for dev/staging/prod
3. **Access Control**: Database-level access controls
4. **Audit Trails**: Comprehensive audit logging

### Data Security

1. **Sensitive Data**: Proper handling of sensitive trading data
2. **Encryption**: Data encryption in transit and at rest
3. **Backup Security**: Secure backup procedures
4. **Compliance**: Financial data compliance standards

## Troubleshooting

### Common Issues

#### Database Connection Issues
```bash
# Check database connectivity
python -c "
from src.database.router_v2 import get_enhanced_router
router = get_enhanced_router()
print('Connection OK' if router.test_connection() else 'Connection Failed')
"
```

#### Migration Issues
```bash
# Check migration status
python -c "
from src.database.institutional_integration import InstitutionalIntegration
integration = InstitutionalIntegration()
status = integration.check_system_health()
print(f'Migration status: {status.migration_status}')
"
```

#### Component Health Issues
```bash
# Run full system check
python -c "
from src.database.institutional_integration import InstitutionalIntegration
integration = InstitutionalIntegration()
success = integration.run_full_system_check()
print(f'System check: {\"PASS\" if success else \"FAIL\"}')
"
```

### Log Analysis

Check application logs for detailed error information:
- Database connection errors
- Migration failures
- Component health issues
- Performance warnings

### Recovery Procedures

1. **Database Recovery**: Restore from backup if needed
2. **Migration Recovery**: Rollback problematic migrations
3. **Component Recovery**: Restart failed components
4. **System Recovery**: Full system restart if needed

## Deployment

### Development Deployment

```bash
# Set environment
export EMO_ENV=dev

# Run build validation
python build.py --validate

# Start development server
python app.py
```

### Production Deployment

```bash
# Set environment
export EMO_ENV=prod
export EMO_DB_URL=postgresql+psycopg://user:pass@host:5432/emo_prod

# Run full build
python build.py

# Deploy application
python build.py --deploy prod
```

### Environment Setup

1. **Database Setup**: Configure PostgreSQL/TimescaleDB for production
2. **Environment Variables**: Set required environment variables
3. **Migration**: Run database migrations
4. **Health Check**: Verify system health
5. **Monitoring**: Enable monitoring and alerting

## Support

For issues with the institutional database infrastructure:

1. Check the build system validation: `python build.py --validate`
2. Review system health reports in `data/integration/`
3. Check application logs for detailed error information
4. Verify environment configuration and database connectivity
5. Run comprehensive system check for detailed diagnostics

The institutional database infrastructure provides enterprise-grade reliability, monitoring, and reporting capabilities for the EMO Options Bot trading system.