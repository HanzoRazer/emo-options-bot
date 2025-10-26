#!/bin/bash
# Docker entrypoint script for EMO Options Bot
# Handles initialization, migrations, and service startup

set -euo pipefail

# =============================================================================
# Configuration and Environment Setup
# =============================================================================

# Default values
DEFAULT_COMMAND="web"
DEFAULT_PORT="8082"
DEFAULT_WORKERS="4"

# Environment setup
export PYTHONPATH="/app/src:${PYTHONPATH:-}"
export EMO_ENV="${EMO_ENV:-prod}"

# Logging configuration
setup_logging() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] EMO Options Bot starting..."
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Environment: ${EMO_ENV}"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Python Path: ${PYTHONPATH}"
}

# =============================================================================
# Health and Readiness Checks
# =============================================================================

check_database_connection() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking database connection..."
    
    # Wait for database to be ready (max 60 seconds)
    timeout=60
    while [ $timeout -gt 0 ]; do
        if python -c "
from src.config.enhanced_config import ConfigLoader
from src.database.db_router import DatabaseRouter
import asyncio

async def test_connection():
    config = ConfigLoader.load_config()
    router = DatabaseRouter(config)
    try:
        await router.test_connection()
        print('Database connection successful')
        return True
    except Exception as e:
        print(f'Database connection failed: {e}')
        return False

result = asyncio.run(test_connection())
exit(0 if result else 1)
        "; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Database connection successful"
            return 0
        fi
        
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Waiting for database... (${timeout}s remaining)"
        sleep 2
        timeout=$((timeout - 2))
    done
    
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: Database connection failed after 60 seconds"
    exit 1
}

# =============================================================================
# Database Migration
# =============================================================================

run_migrations() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running database migrations..."
    
    # Check if migrations are needed
    if alembic current >/dev/null 2>&1; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running alembic upgrade head..."
        alembic upgrade head
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Migrations completed successfully"
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Initializing database schema..."
        alembic stamp head
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Database schema initialized"
    fi
}

# =============================================================================
# Service Management
# =============================================================================

start_web_server() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting web server..."
    
    # Configuration
    PORT="${PORT:-$DEFAULT_PORT}"
    WORKERS="${WORKERS:-$DEFAULT_WORKERS}"
    
    # Gunicorn configuration for production
    if [ "$EMO_ENV" = "prod" ]; then
        exec gunicorn \
            --bind "0.0.0.0:${PORT}" \
            --workers "$WORKERS" \
            --worker-class gevent \
            --worker-connections 1000 \
            --max-requests 1000 \
            --max-requests-jitter 100 \
            --timeout 30 \
            --keep-alive 5 \
            --preload \
            --access-logfile /app/logs/access.log \
            --error-logfile /app/logs/error.log \
            --log-level info \
            --capture-output \
            "src.main:app"
    else
        # Development mode
        exec python -m uvicorn \
            src.main:app \
            --host "0.0.0.0" \
            --port "$PORT" \
            --log-level info \
            --access-log
    fi
}

start_worker() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting background worker..."
    exec python src/services/worker.py
}

start_scheduler() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting scheduler..."
    exec python src/services/scheduler.py
}

start_data_ingestion() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting data ingestion service..."
    exec python src/services/data_ingestion_engine.py
}

# =============================================================================
# Development and Utility Commands
# =============================================================================

run_shell() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting interactive shell..."
    exec /bin/bash
}

run_python() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting Python shell..."
    exec python
}

run_tests() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running tests..."
    python -m pytest tests/ -v --cov=src
}

run_migration_check() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Checking migration status..."
    alembic current
    alembic history --verbose
}

create_backup() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Creating database backup..."
    python scripts/backup/create_backup.py
}

# =============================================================================
# Main Entry Point
# =============================================================================

main() {
    setup_logging
    
    # Parse command
    COMMAND="${1:-$DEFAULT_COMMAND}"
    
    case "$COMMAND" in
        "web"|"server")
            check_database_connection
            run_migrations
            start_web_server
            ;;
        
        "worker")
            check_database_connection
            start_worker
            ;;
        
        "scheduler")
            check_database_connection
            start_scheduler
            ;;
        
        "data-ingestion")
            check_database_connection
            start_data_ingestion
            ;;
        
        "migrate")
            check_database_connection
            run_migrations
            ;;
        
        "shell"|"bash")
            run_shell
            ;;
        
        "python")
            run_python
            ;;
        
        "test"|"tests")
            run_tests
            ;;
        
        "migration-check")
            check_database_connection
            run_migration_check
            ;;
        
        "backup")
            check_database_connection
            create_backup
            ;;
        
        "health"|"healthcheck")
            check_database_connection
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Health check passed"
            ;;
        
        *)
            echo "Usage: $0 {web|worker|scheduler|data-ingestion|migrate|shell|python|test|migration-check|backup|health}"
            echo ""
            echo "Commands:"
            echo "  web              Start the web server (default)"
            echo "  worker           Start the background worker"
            echo "  scheduler        Start the scheduler service"
            echo "  data-ingestion   Start the data ingestion service"
            echo "  migrate          Run database migrations"
            echo "  shell            Start an interactive shell"
            echo "  python           Start a Python shell"
            echo "  test             Run the test suite"
            echo "  migration-check  Check migration status"
            echo "  backup           Create a database backup"
            echo "  health           Run health check"
            echo ""
            echo "Environment variables:"
            echo "  EMO_ENV          Environment (dev|staging|prod, default: prod)"
            echo "  PORT             Web server port (default: 8082)"
            echo "  WORKERS          Number of gunicorn workers (default: 4)"
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"