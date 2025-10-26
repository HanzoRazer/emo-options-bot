# CLI Tools Documentation

## Overview

EMO Options Bot v2.0 provides comprehensive command-line interface (CLI) tools for order management, database operations, and system monitoring. These tools are designed for both interactive use and automation.

## Core CLI Tools

### 1. Order Staging CLI (`stage_order_cli.py`)

Comprehensive order management interface with advanced features.

#### Basic Usage

```bash
# Get help
python tools/stage_order_cli.py --help

# Stage a new order
python tools/stage_order_cli.py stage-order \
    --symbol AAPL \
    --side buy \
    --quantity 100 \
    --order-type market \
    --strategy long_call

# List orders
python tools/stage_order_cli.py list-orders

# List pending approvals
python tools/stage_order_cli.py list-pending

# Check system status
python tools/stage_order_cli.py status
```

#### Advanced Features

```bash
# Risk assessment
python tools/stage_order_cli.py risk-check \
    --symbol AAPL \
    --quantity 500 \
    --strategy covered_call

# Compliance validation
python tools/stage_order_cli.py compliance-check \
    --symbol TSLA \
    --quantity 200

# Institutional status
python tools/stage_order_cli.py institutional-status

# Order approval
python tools/stage_order_cli.py approve-order \
    --order-id 123 \
    --approver supervisor1

# Bulk operations
python tools/stage_order_cli.py bulk-approve \
    --status pending \
    --approver supervisor1
```

#### Command Reference

| Command | Description | Arguments |
|---------|-------------|-----------|
| `stage-order` | Create new staged order | symbol, side, quantity, order-type, strategy |
| `list-orders` | List all orders | --status, --symbol, --user, --limit |
| `list-pending` | List pending approvals | --priority, --age |
| `get-order` | Get specific order | --order-id |
| `update-order` | Update order details | --order-id, fields to update |
| `cancel-order` | Cancel staged order | --order-id, --reason |
| `approve-order` | Approve pending order | --order-id, --approver |
| `reject-order` | Reject pending order | --order-id, --reason |
| `risk-check` | Assess order risk | --symbol, --quantity, --strategy |
| `compliance-check` | Validate compliance | --symbol, --quantity |
| `status` | System status | --detailed |
| `institutional-status` | Institutional integration status | none |

#### Order Status Values

- `staged`: Order created, awaiting processing
- `pending`: Requires approval
- `approved`: Approved for execution
- `rejected`: Rejected by approver
- `submitted`: Submitted to broker
- `executed`: Successfully executed
- `cancelled`: Cancelled by user
- `expired`: Expired due to time limit

#### Examples

```bash
# Stage a complex options order
python tools/stage_order_cli.py stage-order \
    --symbol SPY \
    --side buy \
    --quantity 10 \
    --order-type limit \
    --price 450.00 \
    --strategy iron_condor \
    --expiry "2025-01-17" \
    --metadata '{"strike_price": 450, "spread_width": 10}'

# List high-risk orders
python tools/stage_order_cli.py list-orders \
    --status staged \
    --risk-level high \
    --limit 20

# Approve all pending orders for a specific symbol
python tools/stage_order_cli.py bulk-approve \
    --symbol AAPL \
    --status pending \
    --approver supervisor1

# Generate order report
python tools/stage_order_cli.py report \
    --format json \
    --output daily_report.json \
    --date-range "2025-10-01,2025-10-31"
```

### 2. Database Manager (`db_manage.py`)

Comprehensive database management and maintenance tool.

#### Basic Usage

```bash
# Initialize databases
python tools/db_manage.py init

# Check database health
python tools/db_manage.py health

# Get database statistics
python tools/db_manage.py stats

# Create backup
python tools/db_manage.py backup

# Restore from backup
python tools/db_manage.py restore backups/backup_20251025_120000
```

#### Advanced Operations

```bash
# Run migrations
python tools/db_manage.py migrate

# Optimize database performance
python tools/db_manage.py optimize

# Repair data integrity
python tools/db_manage.py repair

# Import data
python tools/db_manage.py import data_export.json

# Export data
python tools/db_manage.py export

# Cleanup old data
python tools/db_manage.py cleanup --older-than 90
```

#### Command Reference

| Command | Description | Arguments |
|---------|-------------|-----------|
| `init` | Initialize databases | none |
| `migrate` | Run database migrations | none |
| `health` | Check database health | none |
| `stats` | Get database statistics | --detailed |
| `backup` | Create database backup | --name |
| `restore` | Restore from backup | backup_path |
| `optimize` | Optimize performance | none |
| `repair` | Repair data integrity | none |
| `import` | Import data from file | file_path |
| `export` | Export data to file | --output |
| `cleanup` | Clean old data | --older-than |

#### Backup Management

```bash
# Create named backup
python tools/db_manage.py backup --name "pre_migration_backup"

# List available backups
python tools/db_manage.py list-backups

# Verify backup integrity
python tools/db_manage.py verify-backup backups/backup_20251025_120000

# Schedule automatic backups
python tools/db_manage.py schedule-backup \
    --frequency daily \
    --time "02:00" \
    --retention 30
```

### 3. Health Monitor (`emit_health.py`)

System health monitoring and web interface.

#### Basic Usage

```bash
# Start health monitoring server
python tools/emit_health.py --port 8082

# Start with custom configuration
python tools/emit_health.py \
    --port 8083 \
    --host 0.0.0.0 \
    --daemon

# Configuration test
python tools/emit_health.py --config-test
```

#### Server Options

```bash
# Development mode (verbose logging)
python tools/emit_health.py \
    --port 8082 \
    --host localhost \
    --debug

# Production mode (background daemon)
python tools/emit_health.py \
    --port 8082 \
    --host 0.0.0.0 \
    --daemon \
    --log-file /var/log/emo_health.log

# Custom configuration
python tools/emit_health.py \
    --config config/health_server.yaml \
    --port 8082
```

#### Health Check Endpoints

Once running, the health monitor provides several endpoints:

- **Web Interface**: http://localhost:8082/orders.html
- **Health Status**: http://localhost:8082/health
- **System Metrics**: http://localhost:8082/metrics
- **Orders API**: http://localhost:8082/orders.json
- **Readiness Probe**: http://localhost:8082/ready

## Common Use Cases

### Daily Operations

```bash
# Morning startup routine
python tools/db_manage.py health
python tools/emit_health.py --daemon --port 8082
python tools/stage_order_cli.py status

# Check pending approvals
python tools/stage_order_cli.py list-pending

# Review overnight orders
python tools/stage_order_cli.py list-orders \
    --created-after "2025-10-25 00:00:00" \
    --status staged
```

### Order Management Workflow

```bash
# 1. Stage new order
python tools/stage_order_cli.py stage-order \
    --symbol AAPL \
    --side buy \
    --quantity 100 \
    --order-type market \
    --strategy long_call

# 2. Check risk assessment
python tools/stage_order_cli.py risk-check \
    --symbol AAPL \
    --quantity 100

# 3. Review and approve
python tools/stage_order_cli.py list-pending
python tools/stage_order_cli.py approve-order \
    --order-id 123 \
    --approver supervisor1

# 4. Monitor execution
python tools/stage_order_cli.py get-order --order-id 123
```

### Maintenance Operations

```bash
# Weekly maintenance
python tools/db_manage.py backup
python tools/db_manage.py optimize
python tools/db_manage.py stats --detailed

# Monthly cleanup
python tools/db_manage.py cleanup --older-than 90
python tools/db_manage.py repair

# Quarterly backup
python tools/db_manage.py backup --name "quarterly_$(date +%Y%m%d)"
```

## Automation and Scripting

### Bash Script Examples

```bash
#!/bin/bash
# Daily monitoring script

echo "=== EMO Options Bot Daily Check ==="
date

# Check system health
echo "Checking system health..."
python tools/db_manage.py health || exit 1

# Get pending approvals count
echo "Checking pending approvals..."
PENDING=$(python tools/stage_order_cli.py list-pending --count-only)
echo "Pending approvals: $PENDING"

# Create daily backup
echo "Creating daily backup..."
python tools/db_manage.py backup --name "daily_$(date +%Y%m%d)"

echo "Daily check completed successfully"
```

### Python Script Examples

```python
#!/usr/bin/env python3
"""
Automated order approval script
"""
import subprocess
import json
import sys

def get_pending_orders():
    """Get list of pending orders."""
    result = subprocess.run([
        'python', 'tools/stage_order_cli.py', 'list-pending', '--format', 'json'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        return json.loads(result.stdout)
    return []

def approve_low_risk_orders():
    """Auto-approve low-risk orders."""
    orders = get_pending_orders()
    
    for order in orders:
        if order.get('risk_score', 100) < 25:  # Low risk threshold
            result = subprocess.run([
                'python', 'tools/stage_order_cli.py', 'approve-order',
                '--order-id', str(order['id']),
                '--approver', 'auto_system'
            ])
            
            if result.returncode == 0:
                print(f"Auto-approved order {order['id']}")
            else:
                print(f"Failed to approve order {order['id']}")

if __name__ == "__main__":
    approve_low_risk_orders()
```

## Configuration

### Environment Variables

```bash
# Database configuration
export OPS_DATABASE_URL="sqlite:///data/emo_ops.db"
export INSTITUTIONAL_DATABASE_URL="postgresql://user:pass@localhost/emo_inst"

# Logging configuration
export LOG_LEVEL=INFO
export LOG_FILE=/var/log/emo_cli.log

# Health monitoring
export HEALTH_SERVER_PORT=8082
export HEALTH_SERVER_HOST=localhost

# CLI defaults
export DEFAULT_APPROVER=supervisor1
export DEFAULT_ORDER_LIMIT=50
export AUTO_APPROVAL_THRESHOLD=25
```

### Configuration Files

```yaml
# config/cli_config.yaml
database:
  ops_url: "sqlite:///data/emo_ops.db"
  institutional_url: "postgresql://user:pass@localhost/emo_inst"
  
logging:
  level: INFO
  file: /var/log/emo_cli.log
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

health_monitoring:
  port: 8082
  host: localhost
  auto_refresh: 30
  
order_management:
  default_approver: supervisor1
  auto_approval_threshold: 25
  max_order_age_hours: 24
  
risk_management:
  max_position_size: 10000
  max_portfolio_concentration: 0.10
  risk_score_threshold: 75
```

## Error Handling and Troubleshooting

### Common Error Messages

1. **Database Connection Error**
   ```
   Error: Could not connect to database
   Solution: Check database URL and ensure database is running
   ```

2. **Order Validation Error**
   ```
   Error: Order validation failed - invalid symbol
   Solution: Check symbol format and market availability
   ```

3. **Permission Error**
   ```
   Error: Insufficient permissions for approval
   Solution: Check user permissions and approval workflow
   ```

4. **Risk Assessment Error**
   ```
   Error: Risk assessment failed - missing market data
   Solution: Ensure market data service is available
   ```

### Debugging Options

```bash
# Enable verbose logging
python tools/stage_order_cli.py --verbose stage-order ...

# Debug mode
python tools/stage_order_cli.py --debug list-orders

# Dry run (test without execution)
python tools/stage_order_cli.py --dry-run approve-order --order-id 123

# Output to file
python tools/stage_order_cli.py list-orders > orders_report.txt
```

### Log Analysis

```bash
# View recent CLI activity
tail -f /var/log/emo_cli.log

# Search for errors
grep "ERROR" /var/log/emo_cli.log

# Filter by operation
grep "stage-order" /var/log/emo_cli.log

# Get statistics
grep "SUCCESS" /var/log/emo_cli.log | wc -l
```

## Integration with External Systems

### REST API Integration

```bash
# Use CLI tools with REST APIs
curl -X POST http://localhost:8082/api/orders \
    -H "Content-Type: application/json" \
    -d "$(python tools/stage_order_cli.py stage-order --symbol AAPL --format json)"

# Webhook integration
python tools/stage_order_cli.py stage-order \
    --webhook-url "https://api.example.com/orders" \
    --symbol AAPL \
    --side buy \
    --quantity 100
```

### Database Direct Access

```bash
# Export to external database
python tools/db_manage.py export --format sql > emo_export.sql
psql external_db < emo_export.sql

# Sync with external system
python tools/stage_order_cli.py sync \
    --external-db "postgresql://user:pass@external.db/orders" \
    --sync-direction both
```

## Performance Optimization

### Batch Operations

```bash
# Batch order creation
python tools/stage_order_cli.py batch-create orders_batch.json

# Bulk status updates
python tools/stage_order_cli.py bulk-update \
    --status staged \
    --new-status reviewed \
    --reviewer supervisor1

# Parallel processing
python tools/stage_order_cli.py list-orders \
    --parallel-processing \
    --max-workers 4
```

### Caching

```bash
# Enable result caching
python tools/stage_order_cli.py list-orders --cache

# Clear cache
python tools/stage_order_cli.py clear-cache

# Cache statistics
python tools/stage_order_cli.py cache-stats
```

## Security Considerations

### Access Control

1. **User Authentication**: CLI tools respect user permissions
2. **Audit Logging**: All operations are logged
3. **Approval Workflows**: Multi-level approval processes
4. **Data Encryption**: Sensitive data is encrypted

### Best Practices

1. **Use Strong Passwords**: For database connections
2. **Limit Permissions**: Principle of least privilege
3. **Regular Audits**: Review access logs regularly
4. **Secure Storage**: Store credentials securely

---

This documentation covers all CLI tools provided by EMO Options Bot v2.0. For additional information, refer to the main README.md or specific component documentation.