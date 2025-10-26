#!/usr/bin/env python3
"""
Enhanced Live Market Data Logger
================================
Robust real-time market data collection system with:
- Alpaca API integration for live market data
- Database persistence with error handling
- Performance monitoring and metrics
- Integration with enhanced Phase 2 infrastructure

Features:
- Configurable symbol lists and timeframes
- Robust error handling and retry logic
- Rate limiting and API quota management
- Integration with enhanced database router
- Performance metrics and health monitoring
- Runner system integration hooks

Environment Variables:
  ALPACA_DATA_URL=https://data.alpaca.markets/v2  # Alpaca data API URL
  ALPACA_KEY_ID=your_key_id                      # Alpaca API key
  ALPACA_SECRET_KEY=your_secret                  # Alpaca secret key
  EMO_SYMBOLS=SPY,QQQ,AAPL                       # Comma-separated symbol list
  EMO_LIVE_LOGGER_ENABLED=1                      # Enable live logging
  EMO_LIVE_LOGGER_TIMEOUT=30                     # API request timeout
  EMO_LIVE_LOGGER_RETRY_COUNT=3                  # Retry attempts on failure
"""

import os
import requests
import datetime as dt
import time
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

# Setup robust logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add paths for imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

# Enhanced configuration integration
try:
    from utils.enhanced_config import Config
    config = Config()
    logger.info("✅ Enhanced configuration loaded")
except Exception:
    logger.warning("⚠️ Enhanced config not available, using fallback")
    class FallbackConfig:
        def get(self, key: str, default: str = None) -> str:
            return os.getenv(key, default)
        def as_bool(self, key: str, default: bool = False) -> bool:
            return os.getenv(key, "0").lower() in ("1", "true", "yes", "on")
        def as_int(self, key: str, default: int = 0) -> int:
            try:
                return int(self.get(key, str(default)))
            except (ValueError, TypeError):
                return default
    config = FallbackConfig()

# Database integration
try:
    from db.router import EnhancedDB as DB
    logger.info("✅ Enhanced database router loaded")
except Exception:
    logger.warning("⚠️ Enhanced database not available, using fallback")
    try:
        from db.router import DB
    except Exception as e:
        logger.error(f"❌ Database router not available: {e}")
        DB = None

# Configuration
ALPACA_DATA_URL = config.get("ALPACA_DATA_URL", "https://data.alpaca.markets/v2")
KEY = config.get("ALPACA_KEY_ID", "")
SEC = config.get("ALPACA_SECRET_KEY", "")
SYMBOLS = [s.strip().upper() for s in config.get("EMO_SYMBOLS", "SPY,QQQ").split(",") if s.strip()]
ENABLED = config.as_bool("EMO_LIVE_LOGGER_ENABLED", True)
TIMEOUT = config.as_int("EMO_LIVE_LOGGER_TIMEOUT", 30)
RETRY_COUNT = config.as_int("EMO_LIVE_LOGGER_RETRY_COUNT", 3)
RATE_LIMIT_DELAY = config.as_int("EMO_LIVE_LOGGER_RATE_LIMIT", 1)  # seconds between requests

# Performance tracking
_performance_metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "symbols_processed": 0,
    "bars_stored": 0,
    "last_run_time": None,
    "last_error": None,
    "start_time": time.time()
}

def _get_headers() -> Dict[str, str]:
    """Get authenticated headers for Alpaca API requests."""
    return {
        "APCA-API-KEY-ID": KEY,
        "APCA-API-SECRET-KEY": SEC,
        "Content-Type": "application/json",
        "User-Agent": "EMO-Live-Logger/1.0"
    }

def validate_credentials() -> bool:
    """Validate Alpaca API credentials."""
    if not KEY or not SEC:
        logger.error("❌ ALPACA credentials missing (ALPACA_KEY_ID / ALPACA_SECRET_KEY)")
        return False
    
    if len(KEY) < 10 or len(SEC) < 20:
        logger.warning("⚠️ ALPACA credentials appear to be in incorrect format")
        return False
    
    return True

def fetch_latest_bar(symbol: str, retry_count: int = None) -> Optional[Dict[str, Any]]:
    """
    Fetch latest 1-minute bar for a symbol with robust error handling.
    
    Args:
        symbol: Stock symbol to fetch
        retry_count: Number of retries (defaults to global RETRY_COUNT)
        
    Returns:
        Dictionary with bar data or None if failed
    """
    if retry_count is None:
        retry_count = RETRY_COUNT
    
    url = f"{ALPACA_DATA_URL}/stocks/{symbol}/bars"
    params = {
        "timeframe": "1Min", 
        "limit": 1,
        "asof": dt.datetime.now().isoformat()
    }
    
    for attempt in range(retry_count + 1):
        try:
            _performance_metrics["total_requests"] += 1
            
            logger.debug(f"📡 Fetching {symbol} data (attempt {attempt + 1}/{retry_count + 1})")
            
            response = requests.get(
                url, 
                headers=_get_headers(), 
                params=params, 
                timeout=TIMEOUT
            )
            
            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                logger.warning(f"⏱️ Rate limited for {symbol}, waiting {retry_after}s")
                time.sleep(retry_after)
                continue
            
            response.raise_for_status()
            data = response.json()
            
            # Parse response data
            bars = data.get("bars") or data.get("results") or []
            if not bars:
                logger.debug(f"ℹ️ No bars returned for {symbol}")
                return None
            
            bar = bars[-1]  # Get latest bar
            
            # Validate bar data
            required_fields = ["t", "o", "h", "l", "c", "v"]
            if not all(field in bar for field in required_fields):
                logger.warning(f"⚠️ Incomplete bar data for {symbol}: {bar}")
                return None
            
            # Format bar data
            formatted_bar = {
                "symbol": symbol,
                "ts": bar.get("t") or bar.get("timestamp") or bar.get("time"),
                "open": float(bar.get("o", 0)),
                "high": float(bar.get("h", 0)),
                "low": float(bar.get("l", 0)),
                "close": float(bar.get("c", 0)),
                "volume": int(bar.get("v", 0)),
                "data_source": "alpaca_live",
                "fetched_at": dt.datetime.now().isoformat()
            }
            
            _performance_metrics["successful_requests"] += 1
            logger.debug(f"✅ Successfully fetched {symbol}: {formatted_bar['close']} @ {formatted_bar['ts']}")
            
            return formatted_bar
            
        except requests.exceptions.Timeout:
            logger.warning(f"⏱️ Timeout fetching {symbol} (attempt {attempt + 1})")
            if attempt < retry_count:
                time.sleep(min(2 ** attempt, 10))  # Exponential backoff
            
        except requests.exceptions.RequestException as e:
            logger.error(f"🌐 Network error fetching {symbol}: {e}")
            if attempt < retry_count:
                time.sleep(min(2 ** attempt, 10))
            
        except (ValueError, KeyError, TypeError) as e:
            logger.error(f"📊 Data parsing error for {symbol}: {e}")
            break  # Don't retry on data errors
            
        except Exception as e:
            logger.error(f"❌ Unexpected error fetching {symbol}: {e}")
            if attempt < retry_count:
                time.sleep(min(2 ** attempt, 10))
    
    _performance_metrics["failed_requests"] += 1
    _performance_metrics["last_error"] = f"Failed to fetch {symbol} after {retry_count + 1} attempts"
    return None

def store_bars_to_database(bars: List[Dict[str, Any]]) -> int:
    """
    Store bars to database with error handling.
    
    Args:
        bars: List of bar dictionaries
        
    Returns:
        Number of bars successfully stored
    """
    if not bars:
        return 0
    
    if not DB:
        logger.error("❌ Database not available")
        return 0
    
    try:
        with DB() as db:
            if hasattr(db, 'upsert_bars'):
                # Use enhanced database method if available
                stored_count = db.upsert_bars(bars)
            else:
                # Fallback for legacy database
                stored_count = 0
                with db.cursor() as cursor:
                    for bar in bars:
                        try:
                            if db.kind == "sqlite":
                                cursor.execute("""
                                    INSERT OR REPLACE INTO bars(symbol, ts, open, high, low, close, volume, data_source)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                """, (bar["symbol"], bar["ts"], bar["open"], bar["high"], 
                                     bar["low"], bar["close"], bar["volume"], bar.get("data_source", "alpaca")))
                            else:
                                cursor.execute("""
                                    INSERT INTO bars(symbol, ts, open, high, low, close, volume, data_source)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                                    ON CONFLICT (symbol, ts) DO UPDATE SET
                                      open=EXCLUDED.open, high=EXCLUDED.high, low=EXCLUDED.low,
                                      close=EXCLUDED.close, volume=EXCLUDED.volume, data_source=EXCLUDED.data_source
                                """, (bar["symbol"], bar["ts"], bar["open"], bar["high"], 
                                     bar["low"], bar["close"], bar["volume"], bar.get("data_source", "alpaca")))
                            stored_count += 1
                        except Exception as e:
                            logger.error(f"❌ Failed to store bar for {bar['symbol']}: {e}")
                    
                    db.conn.commit()
            
            _performance_metrics["bars_stored"] += stored_count
            logger.info(f"💾 Stored {stored_count}/{len(bars)} bars to database")
            return stored_count
            
    except Exception as e:
        logger.error(f"❌ Database storage failed: {e}")
        return 0

def get_performance_metrics() -> Dict[str, Any]:
    """Get current performance metrics."""
    uptime = time.time() - _performance_metrics["start_time"]
    
    metrics = _performance_metrics.copy()
    metrics.update({
        "uptime_seconds": round(uptime, 2),
        "success_rate": round(_performance_metrics["successful_requests"] / max(_performance_metrics["total_requests"], 1) * 100, 2),
        "symbols_configured": len(SYMBOLS),
        "enabled": ENABLED
    })
    
    return metrics

def main_once() -> Dict[str, Any]:
    """
    Main execution function for live data collection.
    
    Returns:
        Dictionary with execution results and metrics
    """
    start_time = time.time()
    
    if not ENABLED:
        logger.info("ℹ️ Live logger disabled (EMO_LIVE_LOGGER_ENABLED=0)")
        return {"status": "disabled", "message": "Live logger disabled"}
    
    if not validate_credentials():
        return {"status": "error", "message": "Invalid credentials"}
    
    if not SYMBOLS:
        logger.warning("⚠️ No symbols configured for live logging")
        return {"status": "warning", "message": "No symbols configured"}
    
    logger.info(f"🚀 Starting live data collection for {len(SYMBOLS)} symbols: {', '.join(SYMBOLS)}")
    
    bars = []
    processed_symbols = []
    failed_symbols = []
    
    for i, symbol in enumerate(SYMBOLS):
        try:
            logger.debug(f"📊 Processing {symbol} ({i+1}/{len(SYMBOLS)})")
            
            bar = fetch_latest_bar(symbol)
            if bar:
                bars.append(bar)
                processed_symbols.append(symbol)
            else:
                failed_symbols.append(symbol)
            
            # Rate limiting between requests
            if i < len(SYMBOLS) - 1 and RATE_LIMIT_DELAY > 0:
                time.sleep(RATE_LIMIT_DELAY)
                
        except Exception as e:
            logger.error(f"❌ Error processing {symbol}: {e}")
            failed_symbols.append(symbol)
            _performance_metrics["last_error"] = str(e)
    
    _performance_metrics["symbols_processed"] += len(processed_symbols)
    
    # Store to database
    stored_count = 0
    if bars:
        stored_count = store_bars_to_database(bars)
    
    # Update metrics
    execution_time = time.time() - start_time
    _performance_metrics["last_run_time"] = dt.datetime.now().isoformat()
    
    # Prepare result
    result = {
        "status": "success" if bars else "warning",
        "execution_time": round(execution_time, 2),
        "symbols_processed": len(processed_symbols),
        "symbols_failed": len(failed_symbols),
        "bars_collected": len(bars),
        "bars_stored": stored_count,
        "processed_symbols": processed_symbols,
        "failed_symbols": failed_symbols,
        "performance_metrics": get_performance_metrics()
    }
    
    # Log summary
    if bars:
        logger.info(f"✅ Live logging completed: {len(bars)} bars collected, {stored_count} stored ({execution_time:.2f}s)")
    else:
        logger.warning(f"⚠️ Live logging completed with no data collected ({execution_time:.2f}s)")
    
    if failed_symbols:
        logger.warning(f"⚠️ Failed symbols: {', '.join(failed_symbols)}")
    
    return result

# Integration hooks for runner system
def get_latest_metrics() -> Dict[str, Any]:
    """Get latest performance metrics for integration with runner/health systems."""
    return get_performance_metrics()

def reset_metrics():
    """Reset performance metrics."""
    global _performance_metrics
    _performance_metrics = {
        "total_requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "symbols_processed": 0,
        "bars_stored": 0,
        "last_run_time": None,
        "last_error": None,
        "start_time": time.time()
    }
    logger.info("📊 Performance metrics reset")

def health_check() -> Dict[str, Any]:
    """Health check for integration with monitoring systems."""
    try:
        # Basic configuration check
        health = {
            "service": "live_logger",
            "status": "healthy",
            "enabled": ENABLED,
            "credentials_configured": bool(KEY and SEC),
            "symbols_count": len(SYMBOLS),
            "database_available": DB is not None,
            "last_run": _performance_metrics.get("last_run_time"),
            "uptime_seconds": time.time() - _performance_metrics["start_time"]
        }
        
        # Check for recent errors
        if _performance_metrics.get("last_error"):
            health["last_error"] = _performance_metrics["last_error"]
            health["status"] = "warning"
        
        # Check success rate
        if _performance_metrics["total_requests"] > 0:
            success_rate = _performance_metrics["successful_requests"] / _performance_metrics["total_requests"]
            if success_rate < 0.5:
                health["status"] = "error"
                health["error"] = f"Low success rate: {success_rate:.1%}"
        
        return health
        
    except Exception as e:
        return {
            "service": "live_logger",
            "status": "error",
            "error": str(e)
        }

def main():
    """CLI interface for live logger with enhanced options."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="EMO Enhanced Live Market Data Logger",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run once with default settings
  python data/live_logger.py
  
  # Run with specific symbols
  python data/live_logger.py --symbols SPY,QQQ,AAPL
  
  # Show performance metrics
  python data/live_logger.py --metrics
  
  # Health check
  python data/live_logger.py --health
  
  # Reset metrics
  python data/live_logger.py --reset-metrics
        """
    )
    
    parser.add_argument(
        "--symbols", 
        type=str, 
        help="Comma-separated list of symbols (overrides config)"
    )
    parser.add_argument(
        "--metrics", 
        action="store_true", 
        help="Show performance metrics and exit"
    )
    parser.add_argument(
        "--health", 
        action="store_true", 
        help="Show health status and exit"
    )
    parser.add_argument(
        "--reset-metrics", 
        action="store_true", 
        help="Reset performance metrics"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true", 
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="Fetch data but don't store to database"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle utility commands
    if args.metrics:
        metrics = get_performance_metrics()
        print("📊 Live Logger Performance Metrics:")
        print(json.dumps(metrics, indent=2))
        return 0
    
    if args.health:
        health = health_check()
        print("🏥 Live Logger Health Status:")
        print(json.dumps(health, indent=2))
        return 0 if health["status"] == "healthy" else 1
    
    if args.reset_metrics:
        reset_metrics()
        print("✅ Performance metrics reset")
        return 0
    
    # Override symbols if specified
    global SYMBOLS
    if args.symbols:
        SYMBOLS = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
        logger.info(f"🔄 Using CLI symbols: {', '.join(SYMBOLS)}")
    
    # Dry run mode
    if args.dry_run:
        logger.info("🔍 DRY RUN MODE: Data will be fetched but not stored")
        global DB
        DB = None
    
    try:
        # Run main collection
        result = main_once()
        
        # Print results
        print(f"\n📊 Execution Summary:")
        print(f"  Status: {result['status']}")
        print(f"  Execution Time: {result['execution_time']}s")
        print(f"  Symbols Processed: {result['symbols_processed']}")
        print(f"  Bars Collected: {result['bars_collected']}")
        print(f"  Bars Stored: {result['bars_stored']}")
        
        if result['failed_symbols']:
            print(f"  Failed Symbols: {', '.join(result['failed_symbols'])}")
        
        # Return appropriate exit code
        if result['status'] == "error":
            return 2
        elif result['status'] == "warning":
            return 1
        else:
            return 0
            
    except Exception as e:
        logger.error(f"❌ Live logger failed: {e}")
        return 3

if __name__ == "__main__":
    exit(main())