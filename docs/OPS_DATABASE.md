# OPS Database Documentation

## Overview

The OPS (Operational) Database is the core data management system for EMO Options Bot v2.0, providing comprehensive order staging, risk management, and compliance tracking capabilities.

## Architecture

### Database Structure

```
OPS Database
├── StagedOrder (Primary Table)
│   ├── Order Management Fields
│   ├── Risk Assessment Data
│   ├── Compliance Validation
│   ├── Approval Workflow
│   └── Audit Trail
├── OrderMetadata (JSON Fields)
│   ├── Strategy Parameters
│   ├── Market Data
│   ├── Risk Metrics
│   └── Custom Attributes
└── Indexes & Constraints
    ├── Performance Indexes
    ├── Unique Constraints
    └── Foreign Key Relationships
```

### Technology Stack

- **SQLAlchemy 2.0+**: Modern ORM with async support
- **SQLite**: Default database (development/testing)
- **PostgreSQL**: Production database option
- **Connection Pooling**: Efficient connection management
- **Migration Support**: Automated schema migrations

## StagedOrder Model

### Core Fields

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | Integer | Primary key | Auto-increment |
| `symbol` | String(10) | Trading symbol | Required, indexed |
| `side` | String(10) | Order side (buy/sell) | Required |
| `qty` | Integer | Order quantity | Required, > 0 |
| `order_type` | String(20) | Order type (market/limit/stop) | Required |
| `price` | Decimal(10,2) | Order price | Optional |
| `strategy` | String(50) | Trading strategy | Required |
| `user` | String(50) | User identifier | Required |
| `status` | String(20) | Order status | Required, default='staged' |

### Timestamp Fields

| Field | Type | Description |
|-------|------|-------------|
| `created_at` | DateTime | Order creation time |
| `updated_at` | DateTime | Last modification time |
| `expires_at` | DateTime | Order expiration time |
| `submitted_at` | DateTime | Broker submission time |
| `executed_at` | DateTime | Execution time |

### Risk Management

| Field | Type | Description |
|-------|------|-------------|
| `risk_score` | Float | Calculated risk score (0-100) |
| `risk_factors` | JSON | Detailed risk analysis |
| `portfolio_impact` | JSON | Portfolio impact assessment |
| `concentration_check` | Boolean | Concentration limit validation |

### Compliance & Approval

| Field | Type | Description |
|-------|------|-------------|
| `compliance_flags` | JSON | Compliance validation results |
| `approval_required` | Boolean | Requires manual approval |
| `approved_by` | String(50) | Approver identifier |
| `approved_at` | DateTime | Approval timestamp |
| `rejection_reason` | Text | Rejection explanation |

### Metadata & Audit

| Field | Type | Description |
|-------|------|-------------|
| `metadata` | JSON | Strategy-specific parameters |
| `market_data` | JSON | Market data at order time |
| `audit_trail` | JSON | Complete audit log |
| `tags` | JSON | Custom tags and labels |

## Database Operations

### Session Management

```python
from ops.db.session import get_session, init_db

# Initialize database
init_db()

# Use session context manager
with get_session() as session:
    orders = session.query(StagedOrder).all()
```

### CRUD Operations

#### Create Order
```python
from ops.staging.models import StagedOrder

# Create new staged order
order = StagedOrder(
    symbol="AAPL",
    side="buy",
    qty=100,
    order_type="market",
    strategy="long_call",
    user="trader1"
)

with get_session() as session:
    session.add(order)
    session.commit()
```

#### Query Orders
```python
# Get all orders
with get_session() as session:
    orders = session.query(StagedOrder).all()

# Filter by status
pending_orders = session.query(StagedOrder).filter(
    StagedOrder.status == "staged"
).all()

# Filter by symbol and date
recent_aapl = session.query(StagedOrder).filter(
    StagedOrder.symbol == "AAPL",
    StagedOrder.created_at >= datetime.now() - timedelta(days=7)
).all()
```

#### Update Order
```python
# Update order status
with get_session() as session:
    order = session.query(StagedOrder).filter(
        StagedOrder.id == order_id
    ).first()
    
    if order:
        order.status = "approved"
        order.approved_by = "supervisor1"
        order.approved_at = datetime.now(timezone.utc)
        session.commit()
```

#### Delete Order
```python
# Delete order (soft delete recommended)
with get_session() as session:
    order = session.query(StagedOrder).filter(
        StagedOrder.id == order_id
    ).first()
    
    if order:
        order.status = "cancelled"
        order.updated_at = datetime.now(timezone.utc)
        session.commit()
```

## Risk Assessment Engine

### Risk Score Calculation

The risk score is calculated based on multiple factors:

1. **Position Size**: Relative to account size
2. **Symbol Volatility**: Historical volatility analysis
3. **Portfolio Concentration**: Position concentration limits
4. **Market Conditions**: Current market volatility
5. **Strategy Risk**: Strategy-specific risk factors

### Risk Factors JSON Structure

```json
{
  "position_size_risk": 25.5,
  "volatility_risk": 45.2,
  "concentration_risk": 15.0,
  "market_risk": 30.8,
  "strategy_risk": 20.0,
  "total_score": 67.3,
  "risk_level": "Medium",
  "recommendations": [
    "Consider reducing position size",
    "Monitor market volatility"
  ]
}
```

## Compliance Framework

### Compliance Checks

1. **Position Limits**: Maximum position size per symbol
2. **Concentration Limits**: Portfolio concentration rules
3. **Risk Limits**: Maximum risk exposure per trade
4. **Regulatory Requirements**: Specific regulatory compliance
5. **Internal Policies**: Custom business rules

### Compliance Flags JSON Structure

```json
{
  "position_limit_check": {
    "passed": true,
    "limit": 1000,
    "current": 250
  },
  "concentration_check": {
    "passed": false,
    "limit": 0.10,
    "current": 0.15,
    "warning": "Exceeds 10% concentration limit"
  },
  "risk_check": {
    "passed": true,
    "max_risk": 100000,
    "current_risk": 25000
  }
}
```

## Approval Workflow

### Approval Requirements

Orders requiring approval are determined by:

1. **Order Size**: Large orders above threshold
2. **Risk Score**: High-risk orders (score > 75)
3. **Compliance Issues**: Failed compliance checks
4. **Strategy Type**: High-risk strategies
5. **User Permissions**: User-specific approval requirements

### Approval Process

1. **Automatic Screening**: System checks all criteria
2. **Queue Assignment**: Orders requiring approval are queued
3. **Notification**: Approvers are notified
4. **Review Process**: Manual review and decision
5. **Final Status**: Approved, rejected, or modified

## Database Configuration

### Connection Settings

```python
# SQLite (Development)
DATABASE_URL = "sqlite:///data/emo_ops.db"

# PostgreSQL (Production)
DATABASE_URL = "postgresql://user:password@localhost:5432/emo_ops"

# Configuration options
DATABASE_CONFIG = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_timeout": 30,
    "pool_recycle": 3600,
    "echo": False  # Set to True for SQL logging
}
```

### Environment Variables

```bash
# Database connection
export OPS_DATABASE_URL="sqlite:///data/emo_ops.db"

# Connection pool settings
export DB_POOL_SIZE=10
export DB_MAX_OVERFLOW=20

# Logging
export DB_ECHO=false
export LOG_LEVEL=INFO
```

## Performance Optimization

### Indexing Strategy

```sql
-- Primary indexes
CREATE INDEX idx_staged_order_symbol ON staged_order(symbol);
CREATE INDEX idx_staged_order_status ON staged_order(status);
CREATE INDEX idx_staged_order_created_at ON staged_order(created_at);
CREATE INDEX idx_staged_order_user ON staged_order(user);

-- Composite indexes
CREATE INDEX idx_staged_order_symbol_status ON staged_order(symbol, status);
CREATE INDEX idx_staged_order_user_created ON staged_order(user, created_at);
```

### Query Optimization

1. **Use Appropriate Indexes**: Ensure queries use existing indexes
2. **Limit Result Sets**: Use LIMIT and pagination for large result sets
3. **Avoid N+1 Queries**: Use eager loading for related data
4. **Connection Pooling**: Reuse database connections efficiently

### Maintenance Operations

```python
# Database statistics
from ops.db.session import get_database_info
info = get_database_info()

# Optimize database
from tools.db_manage import DatabaseManager
manager = DatabaseManager()
manager.optimize_databases()

# Vacuum and analyze (SQLite)
manager._optimize_ops_database()
```

## Backup and Recovery

### Automated Backups

```python
# Create backup
from tools.db_manage import DatabaseManager
manager = DatabaseManager()
backup_path = manager.create_backup()

# Restore from backup
manager.restore_backup(backup_path)
```

### Backup Strategy

1. **Daily Backups**: Automatic daily backup creation
2. **Retention Policy**: Keep backups for configurable period
3. **Integrity Checks**: Verify backup integrity
4. **Point-in-Time Recovery**: Restore to specific timestamp

## Monitoring and Logging

### Health Monitoring

```python
# Check database health
from ops.db.session import test_connection
healthy = test_connection()

# Get detailed status
from tools.db_manage import DatabaseManager
manager = DatabaseManager()
health = manager.check_health()
```

### Performance Metrics

1. **Query Performance**: Track query execution times
2. **Connection Usage**: Monitor connection pool utilization
3. **Error Rates**: Track database error rates
4. **Storage Usage**: Monitor database size and growth

## API Integration

### REST API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/orders` | GET | List orders with filtering |
| `/orders` | POST | Create new order |
| `/orders/{id}` | GET | Get specific order |
| `/orders/{id}` | PUT | Update order |
| `/orders/{id}` | DELETE | Cancel order |
| `/orders/{id}/approve` | POST | Approve order |
| `/orders/{id}/reject` | POST | Reject order |

### WebSocket Support

Real-time order updates via WebSocket:

```javascript
// Connect to order updates
const ws = new WebSocket('ws://localhost:8082/orders/ws');

ws.onmessage = function(event) {
    const orderUpdate = JSON.parse(event.data);
    // Handle order update
};
```

## Security Considerations

### Data Protection

1. **Encryption**: Database encryption at rest
2. **Access Controls**: Role-based access controls
3. **Audit Logging**: Complete audit trail
4. **Data Retention**: Configurable data retention policies

### Connection Security

1. **SSL/TLS**: Encrypted database connections
2. **Authentication**: Database user authentication
3. **Authorization**: Granular permission controls
4. **Network Security**: Database network isolation

## Troubleshooting

### Common Issues

1. **Connection Timeouts**
   - Check connection pool settings
   - Verify database server status
   - Review network connectivity

2. **Performance Issues**
   - Analyze slow queries
   - Check index usage
   - Review connection pool utilization

3. **Data Integrity Issues**
   - Run database validation
   - Check constraint violations
   - Review audit logs

### Diagnostic Tools

```bash
# Database health check
python tools/db_manage.py health

# Performance statistics
python tools/db_manage.py stats

# Repair operations
python tools/db_manage.py repair

# Optimize database
python tools/db_manage.py optimize
```

## Migration Guide

### Schema Migrations

```python
# Run migrations
from ops.db.session import run_migrations
run_migrations()

# Check migration status
from ops.db.session import get_migration_status
status = get_migration_status()
```

### Data Migration

```python
# Export data
from tools.db_manage import DatabaseManager
manager = DatabaseManager()
export_file = manager.export_data()

# Import data
manager.import_data(export_file)
```

## Best Practices

### Development

1. **Use Transactions**: Wrap related operations in transactions
2. **Handle Exceptions**: Proper error handling and rollback
3. **Connection Management**: Use session context managers
4. **Testing**: Comprehensive unit and integration tests

### Production

1. **Connection Pooling**: Configure appropriate pool sizes
2. **Monitoring**: Implement comprehensive monitoring
3. **Backup Strategy**: Regular automated backups
4. **Performance Tuning**: Regular performance optimization

### Security

1. **Principle of Least Privilege**: Minimal required permissions
2. **Regular Updates**: Keep database software updated
3. **Access Logging**: Log all database access
4. **Encryption**: Encrypt sensitive data

---

This documentation provides comprehensive coverage of the OPS Database system. For additional support, refer to the main README.md or contact the development team.