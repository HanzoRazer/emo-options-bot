"""
EMO Options Bot - Configuration Management
Centralized configuration and environment variable handling
"""

import os
from pathlib import Path
from typing import Dict, Any, List

# Project paths
ROOT = Path(__file__).resolve().parents[2]  # src/utils/ -> project root
DATA_DIR = ROOT / "data"
SCRIPTS_DIR = ROOT / "scripts"
TESTS_DIR = ROOT / "tests"

# Default configuration
DEFAULT_CONFIG = {
    # Environment
    "EMO_ENV": "dev",
    
    # Database
    "SQLITE_BARS_PATH": str(DATA_DIR / "emo.sqlite"),
    "SQLITE_ANALYSIS_PATH": str(DATA_DIR / "describer.db"),
    
    # ML Outlook
    "ML_OUTLOOK_PATH": str(DATA_DIR / "ml_outlook.json"),
    
    # Alpaca API
    "ALPACA_DATA_URL": "https://data.alpaca.markets/v2",
    "ALPACA_KEY_ID": "",
    "ALPACA_SECRET_KEY": "",
    
    # Symbols
    "EMO_SYMBOLS": "SPY,QQQ",
    
    # Web Dashboard
    "DASHBOARD_HOST": "localhost",
    "DASHBOARD_PORT": 8083,
    "DASHBOARD_AUTO_REFRESH": 30,
    
    # PostgreSQL (production)
    "EMO_PG_DSN": "",
}

def load_environment() -> Dict[str, str]:
    """
    Load environment variables with defaults
    
    Returns:
        Dictionary of configuration values
    """
    config = {}
    
    for key, default_value in DEFAULT_CONFIG.items():
        config[key] = os.getenv(key, str(default_value))
    
    return config

def get_config(key: str, default: Any = None) -> Any:
    """
    Get a single configuration value
    
    Args:
        key: Configuration key
        default: Default value if key not found
        
    Returns:
        Configuration value
    """
    return os.getenv(key, default or DEFAULT_CONFIG.get(key))

def get_symbols() -> List[str]:
    """
    Get list of symbols to analyze
    
    Returns:
        List of uppercase symbol strings
    """
    symbols_str = get_config("EMO_SYMBOLS", "SPY,QQQ")
    return [s.strip().upper() for s in symbols_str.split(",") if s.strip()]

def get_database_path(db_type: str = "bars") -> Path:
    """
    Get database file path
    
    Args:
        db_type: "bars" for market data, "analysis" for analysis results
        
    Returns:
        Path to database file
    """
    if db_type == "bars":
        return Path(get_config("SQLITE_BARS_PATH"))
    else:
        return Path(get_config("SQLITE_ANALYSIS_PATH"))

def ensure_data_directories():
    """Ensure all required data directories exist"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    TESTS_DIR.mkdir(parents=True, exist_ok=True)

def get_project_info() -> Dict[str, Any]:
    """
    Get project information and paths
    
    Returns:
        Dictionary with project metadata
    """
    return {
        "name": "EMO Options Bot",
        "version": "1.0.0",
        "root_dir": str(ROOT),
        "data_dir": str(DATA_DIR),
        "scripts_dir": str(SCRIPTS_DIR),
        "tests_dir": str(TESTS_DIR),
        "environment": get_config("EMO_ENV"),
        "symbols": get_symbols()
    }