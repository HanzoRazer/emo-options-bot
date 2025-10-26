"""
EMO Options Bot Build Configuration
===================================
Comprehensive build configuration for development and production deployment.
"""

import os
from pathlib import Path

# Project configuration
PROJECT_NAME = "emo-options-bot"
VERSION = "2.0.0"
DESCRIPTION = "Enhanced EMO Options Bot with OPS Database and Institutional Integration"

# Build settings
BUILD_DIR = Path("build")
DIST_DIR = Path("dist")
SRC_DIR = Path("src")
OPS_DIR = Path("ops")
TOOLS_DIR = Path("tools")

# Package structure for deployment
PACKAGE_STRUCTURE = {
    "src/": [
        "**/*.py",
        "database/**/*",
        "models/**/*", 
        "utils/**/*"
    ],
    "ops/": [
        "**/*.py",
        "db/**/*",
        "staging/**/*"
    ],
    "tools/": [
        "stage_order_cli.py",
        "emit_health.py", 
        "db_manage.py",
        "plot_shock.py"
    ],
    "": [
        "requirements.txt",
        "README*.txt",
        "setup.py",
        "start_emo.py",
        "validate_system.py"
    ]
}

# Dependencies categorized by environment
DEPENDENCIES = {
    "core": [
        "sqlalchemy>=2.0.0",
        "pandas>=1.5.0",
        "numpy>=1.21.0"
    ],
    "database": [
        "sqlite3",  # Built-in
        "psycopg2-binary>=2.9.0"  # PostgreSQL support
    ],
    "trading": [
        "yfinance>=0.2.0",
        "finnhub-python>=2.4.0"
    ],
    "monitoring": [
        "psutil>=5.9.0"
    ],
    "configuration": [
        "PyYAML>=6.0"
    ],
    "development": [
        "pytest>=7.0.0",
        "black>=22.0.0",
        "flake8>=5.0.0",
        "mypy>=1.0.0"
    ]
}

# Environment configurations
ENVIRONMENTS = {
    "development": {
        "database_url": "sqlite:///data/emo_dev.db",
        "log_level": "DEBUG",
        "health_port": 8082,
        "enable_debug": True
    },
    "staging": {
        "database_url": "sqlite:///data/emo_staging.db", 
        "log_level": "INFO",
        "health_port": 8082,
        "enable_debug": False
    },
    "production": {
        "database_url": "postgresql://user:pass@localhost/emo_prod",
        "log_level": "INFO", 
        "health_port": 8082,
        "enable_debug": False
    }
}

# Build targets
BUILD_TARGETS = {
    "local": {
        "description": "Local development build",
        "include_dev_deps": True,
        "create_venv": True,
        "run_tests": True
    },
    "docker": {
        "description": "Docker container build",
        "include_dev_deps": False,
        "create_dockerfile": True,
        "optimize_size": True
    },
    "standalone": {
        "description": "Standalone executable",
        "include_dev_deps": False,
        "bundle_python": True,
        "single_file": True
    }
}

# Quality checks configuration
QUALITY_CHECKS = {
    "code_style": {
        "tool": "black",
        "config": {
            "line-length": 88,
            "target-version": ["py38", "py39", "py310", "py311"]
        }
    },
    "linting": {
        "tool": "flake8", 
        "config": {
            "max-line-length": 88,
            "ignore": ["E203", "W503"],
            "exclude": ["build", "dist", ".git", "__pycache__"]
        }
    },
    "type_checking": {
        "tool": "mypy",
        "config": {
            "python_version": "3.8",
            "strict": True,
            "ignore_missing_imports": True
        }
    },
    "testing": {
        "tool": "pytest",
        "config": {
            "testpaths": ["tests"],
            "python_files": "test_*.py",
            "python_classes": "Test*",
            "python_functions": "test_*"
        }
    }
}

# Docker configuration
DOCKER_CONFIG = {
    "base_image": "python:3.11-slim",
    "working_dir": "/app",
    "expose_ports": [8082],
    "health_check": {
        "test": ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8082/health')"],
        "interval": "30s",
        "timeout": "10s", 
        "retries": 3
    },
    "labels": {
        "maintainer": "EMO Options Bot Team",
        "version": VERSION,
        "description": DESCRIPTION
    }
}

# Deployment configuration
DEPLOYMENT_CONFIG = {
    "systemd_service": {
        "name": "emo-options-bot",
        "description": "EMO Options Bot Trading System",
        "user": "emo",
        "group": "emo",
        "working_directory": "/opt/emo-options-bot",
        "environment_file": "/opt/emo-options-bot/.env"
    },
    "nginx_config": {
        "server_name": "emo-bot.local",
        "proxy_pass": "http://localhost:8082",
        "ssl_enabled": False
    },
    "backup_schedule": {
        "frequency": "daily",
        "retention_days": 30,
        "backup_location": "/backups/emo-options-bot"
    }
}

# Security configuration
SECURITY_CONFIG = {
    "file_permissions": {
        "scripts": "755",
        "configs": "644", 
        "secrets": "600",
        "data": "755"
    },
    "user_requirements": {
        "min_uid": 1000,
        "no_root": True,
        "group_membership": ["trading", "monitoring"]
    },
    "network_security": {
        "bind_localhost_only": True,
        "require_authentication": False,  # Will be added in future
        "rate_limiting": {
            "enabled": True,
            "requests_per_minute": 60
        }
    }
}

# Monitoring and logging
MONITORING_CONFIG = {
    "log_rotation": {
        "max_size": "100MB",
        "backup_count": 5,
        "compression": True
    },
    "metrics_collection": {
        "enabled": True,
        "interval_seconds": 60,
        "retention_days": 90
    },
    "alerting": {
        "enabled": False,  # Will be implemented
        "channels": ["email", "webhook"],
        "thresholds": {
            "error_rate": 0.05,
            "response_time_ms": 5000,
            "disk_usage_percent": 90
        }
    }
}

# Feature flags for conditional builds
FEATURE_FLAGS = {
    "institutional_integration": True,
    "ops_database": True,
    "health_monitoring": True,
    "web_interface": True,
    "cli_tools": True,
    "backup_restore": True,
    "performance_monitoring": True,
    "advanced_analytics": False,  # Future feature
    "multi_broker_support": False  # Future feature
}

def get_config(environment: str = "development") -> dict:
    """Get configuration for specific environment."""
    return {
        "project": {
            "name": PROJECT_NAME,
            "version": VERSION,
            "description": DESCRIPTION
        },
        "environment": ENVIRONMENTS.get(environment, ENVIRONMENTS["development"]),
        "dependencies": DEPENDENCIES,
        "features": FEATURE_FLAGS,
        "security": SECURITY_CONFIG,
        "monitoring": MONITORING_CONFIG
    }

def get_build_config(target: str = "local") -> dict:
    """Get build configuration for specific target."""
    return {
        "target": BUILD_TARGETS.get(target, BUILD_TARGETS["local"]),
        "package_structure": PACKAGE_STRUCTURE,
        "quality_checks": QUALITY_CHECKS,
        "docker": DOCKER_CONFIG if target == "docker" else None
    }