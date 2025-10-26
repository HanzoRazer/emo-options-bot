"""
Enhanced Live Data Ingestion System
Multi-source data ingestion with error handling, rate limiting, and monitoring.
Supports Alpaca, Interactive Brokers, and other data providers.
"""
import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any, Tuple
import threading
import queue
import asyncio
from dataclasses import dataclass
from enum import Enum

import requests
import pandas as pd
import sqlalchemy as sa
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.database.enhanced_router import DBRouter

logger = logging.getLogger(__name__)

class DataProvider(Enum):
    """Supported data providers"""
    ALPACA = "alpaca"
    MOCK = "mock"
    IB = "interactive_brokers"  # Future implementation
    TD = "td_ameritrade"        # Future implementation

@dataclass
class IngestionConfig:
    """Configuration for data ingestion"""
    provider: DataProvider
    symbols: List[str]
    timeframes: List[str] = None
    batch_size: int = 1000
    rate_limit_per_minute: int = 200
    retry_attempts: int = 3
    timeout_seconds: int = 30
    lookback_hours: int = 24
    enable_options: bool = False
    enable_greeks: bool = False

class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, max_calls: int, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self.lock = threading.Lock()
    
    def acquire(self) -> bool:
        """Acquire rate limit slot"""
        with self.lock:
            now = time.time()
            
            # Remove old calls outside time window
            self.calls = [call_time for call_time in self.calls 
                         if now - call_time < self.time_window]
            
            if len(self.calls) < self.max_calls:
                self.calls.append(now)
                return True
            
            return False
    
    def wait_time(self) -> float:
        """Get time to wait before next call"""
        with self.lock:
            if not self.calls:
                return 0
            
            oldest_call = min(self.calls)
            wait_time = self.time_window - (time.time() - oldest_call)
            return max(0, wait_time)

class BaseDataProvider:
    """Base class for data providers"""
    
    def __init__(self, config: IngestionConfig):
        self.config = config
        self.rate_limiter = RateLimiter(config.rate_limit_per_minute)
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.config.retry_attempts,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def fetch_bars(self, symbol: str, start_time: datetime, timeframe: str = "1Min") -> pd.DataFrame:
        """Fetch price bars - to be implemented by subclasses"""
        raise NotImplementedError
    
    def fetch_options_chain(self, symbol: str) -> pd.DataFrame:
        """Fetch options chain - to be implemented by subclasses"""
        raise NotImplementedError

class AlpacaProvider(BaseDataProvider):
    """Alpaca Markets data provider"""
    
    def __init__(self, config: IngestionConfig):
        super().__init__(config)
        
        self.api_url = os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets/v2")
        self.key_id = os.getenv("ALPACA_KEY_ID")
        self.secret_key = os.getenv("ALPACA_SECRET_KEY")
        
        if not self.key_id or not self.secret_key:
            raise ValueError("ALPACA_KEY_ID and ALPACA_SECRET_KEY required")
        
        self.headers = {
            "APCA-API-KEY-ID": self.key_id,
            "APCA-API-SECRET-KEY": self.secret_key
        }
    
    def fetch_bars(self, symbol: str, start_time: datetime, timeframe: str = "1Min") -> pd.DataFrame:
        """Fetch price bars from Alpaca"""
        # Rate limiting
        while not self.rate_limiter.acquire():
            wait_time = self.rate_limiter.wait_time()
            logger.info(f"Rate limit reached, waiting {wait_time:.1f}s")
            time.sleep(wait_time + 0.1)
        
        try:
            url = f"{self.api_url}/stocks/{symbol}/bars"
            params = {
                "timeframe": timeframe,
                "start": start_time.isoformat() + "Z",
                "limit": self.config.batch_size,
                "adjustment": "all",
                "feed": "iex"
            }
            
            response = self.session.get(
                url, 
                headers=self.headers, 
                params=params, 
                timeout=self.config.timeout_seconds
            )
            response.raise_for_status()
            
            data = response.json()
            bars = data.get("bars", [])
            
            if not bars:
                logger.debug(f"No bars returned for {symbol}")
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(bars)
            
            # Normalize columns
            df["ts"] = pd.to_datetime(df["t"], utc=True)
            df["symbol"] = symbol
            df["timeframe"] = timeframe
            df = df.rename(columns={
                "o": "open", "h": "high", "l": "low", 
                "c": "close", "v": "volume", "n": "trade_count", "vw": "vwap"
            })
            
            # Select and order columns
            columns = ["ts", "symbol", "open", "high", "low", "close", "volume", "timeframe"]
            if "trade_count" in df.columns:
                columns.append("trade_count")
            if "vwap" in df.columns:
                columns.append("vwap")
            
            df = df[columns].sort_values("ts")
            
            logger.debug(f"Fetched {len(df)} bars for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch bars for {symbol}: {e}")
            return pd.DataFrame()

class MockProvider(BaseDataProvider):
    """Mock data provider for testing"""
    
    def fetch_bars(self, symbol: str, start_time: datetime, timeframe: str = "1Min") -> pd.DataFrame:
        """Generate mock price bars"""
        logger.debug(f"Generating mock bars for {symbol}")
        
        # Generate mock data
        periods = 60  # 1 hour of minute bars
        timestamps = pd.date_range(
            start=start_time, 
            periods=periods, 
            freq="1Min",
            tz=timezone.utc
        )
        
        # Simple random walk for prices
        import numpy as np
        np.random.seed(hash(symbol) % 2**32)  # Deterministic based on symbol
        
        base_price = {"SPY": 450, "QQQ": 380, "AAPL": 175}.get(symbol, 100)
        
        returns = np.random.normal(0, 0.0005, periods)  # 0.05% std dev
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Generate OHLC from prices
        data = []
        for i, (ts, close) in enumerate(zip(timestamps, prices)):
            # Mock intraday movement
            high = close * (1 + abs(np.random.normal(0, 0.001)))
            low = close * (1 - abs(np.random.normal(0, 0.001)))
            open_price = prices[i-1] if i > 0 else close
            volume = int(np.random.normal(1000000, 200000))
            
            data.append({
                "ts": ts,
                "symbol": symbol,
                "open": open_price,
                "high": max(open_price, high, close),
                "low": min(open_price, low, close),
                "close": close,
                "volume": max(volume, 1000),
                "timeframe": timeframe
            })
        
        df = pd.DataFrame(data)
        return df

class DataIngestionEngine:
    """Main data ingestion engine"""
    
    def __init__(self, config: IngestionConfig):
        self.config = config
        self.provider = self._create_provider()
        self.stats = {
            "total_symbols": len(config.symbols),
            "successful_ingestions": 0,
            "failed_ingestions": 0,
            "total_rows_inserted": 0,
            "start_time": None,
            "last_run_time": None
        }
    
    def _create_provider(self) -> BaseDataProvider:
        """Create appropriate data provider"""
        if self.config.provider == DataProvider.ALPACA:
            return AlpacaProvider(self.config)
        elif self.config.provider == DataProvider.MOCK:
            return MockProvider(self.config)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    def run_ingestion(self) -> Dict[str, Any]:
        """Run single ingestion cycle"""
        self.stats["start_time"] = datetime.now(timezone.utc)
        
        logger.info(f"Starting ingestion for {len(self.config.symbols)} symbols")
        
        # Calculate lookback time
        start_time = datetime.now(timezone.utc) - timedelta(hours=self.config.lookback_hours)
        
        results = []
        total_rows = 0
        
        for symbol in self.config.symbols:
            try:
                logger.debug(f"Processing {symbol}")
                
                # Fetch timeframes
                timeframes = self.config.timeframes or ["1Min"]
                
                for timeframe in timeframes:
                    df = self.provider.fetch_bars(symbol, start_time, timeframe)
                    
                    if not df.empty:
                        rows_inserted = self._upsert_bars(df)
                        total_rows += rows_inserted
                        
                        results.append({
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "rows": rows_inserted,
                            "success": True
                        })
                        
                        logger.info(f"✅ {symbol} ({timeframe}): +{rows_inserted} rows")
                    else:
                        results.append({
                            "symbol": symbol,
                            "timeframe": timeframe,
                            "rows": 0,
                            "success": True,
                            "note": "No new data"
                        })
                
                self.stats["successful_ingestions"] += 1
                
            except Exception as e:
                logger.error(f"❌ {symbol}: {e}")
                results.append({
                    "symbol": symbol,
                    "success": False,
                    "error": str(e)
                })
                self.stats["failed_ingestions"] += 1
        
        self.stats["total_rows_inserted"] += total_rows
        self.stats["last_run_time"] = datetime.now(timezone.utc)
        
        duration = (self.stats["last_run_time"] - self.stats["start_time"]).total_seconds()
        
        logger.info(f"✅ Ingestion complete: {total_rows} total rows in {duration:.1f}s")
        
        return {
            "success": True,
            "duration_seconds": duration,
            "total_rows": total_rows,
            "results": results,
            "stats": self.stats.copy()
        }
    
    def _upsert_bars(self, df: pd.DataFrame) -> int:
        """Upsert bars data to database"""
        if df.empty:
            return 0
        
        try:
            # Add created_at timestamp
            df["created_at"] = datetime.now(timezone.utc)
            
            # Use enhanced router's upsert capability
            return DBRouter.upsert_df(df, "bars", conflict_columns=["symbol", "ts", "timeframe"])
            
        except Exception as e:
            logger.error(f"Failed to upsert bars: {e}")
            raise
    
    def run_continuous(self, interval_minutes: int = 1):
        """Run continuous ingestion"""
        logger.info(f"Starting continuous ingestion (interval: {interval_minutes}min)")
        
        try:
            while True:
                try:
                    self.run_ingestion()
                except Exception as e:
                    logger.error(f"Ingestion cycle failed: {e}")
                
                logger.info(f"Waiting {interval_minutes} minutes until next cycle...")
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            logger.info("Continuous ingestion stopped by user")
    
    def get_status(self) -> Dict[str, Any]:
        """Get ingestion status"""
        return {
            "provider": self.config.provider.value,
            "symbols": self.config.symbols,
            "stats": self.stats,
            "database_status": DBRouter.get_status()
        }

def create_config_from_env() -> IngestionConfig:
    """Create ingestion config from environment variables"""
    provider_name = os.getenv("EMO_DATA_PROVIDER", "mock").lower()
    provider = DataProvider(provider_name)
    
    symbols = os.getenv("EMO_SYMBOLS", "SPY,QQQ,AAPL").split(",")
    symbols = [s.strip().upper() for s in symbols]
    
    timeframes = os.getenv("EMO_TIMEFRAMES", "1Min").split(",")
    timeframes = [tf.strip() for tf in timeframes]
    
    return IngestionConfig(
        provider=provider,
        symbols=symbols,
        timeframes=timeframes,
        batch_size=int(os.getenv("EMO_BATCH_SIZE", "1000")),
        rate_limit_per_minute=int(os.getenv("EMO_RATE_LIMIT", "200")),
        retry_attempts=int(os.getenv("EMO_RETRY_ATTEMPTS", "3")),
        timeout_seconds=int(os.getenv("EMO_TIMEOUT", "30")),
        lookback_hours=int(os.getenv("EMO_LOOKBACK_HOURS", "2")),
        enable_options=os.getenv("EMO_ENABLE_OPTIONS", "false").lower() == "true",
        enable_greeks=os.getenv("EMO_ENABLE_GREEKS", "false").lower() == "true"
    )

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="EMO Data Ingestion Engine")
    parser.add_argument("--provider", choices=[p.value for p in DataProvider], 
                       help="Data provider to use")
    parser.add_argument("--symbols", help="Comma-separated list of symbols")
    parser.add_argument("--continuous", action="store_true", 
                       help="Run continuous ingestion")
    parser.add_argument("--interval", type=int, default=1,
                       help="Interval in minutes for continuous mode")
    parser.add_argument("--status", action="store_true",
                       help="Show ingestion status")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize database
    try:
        DBRouter.init()
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)
    
    # Create config
    config = create_config_from_env()
    
    # Override with command line args
    if args.provider:
        config.provider = DataProvider(args.provider)
    if args.symbols:
        config.symbols = [s.strip().upper() for s in args.symbols.split(",")]
    
    # Create ingestion engine
    engine = DataIngestionEngine(config)
    
    try:
        if args.status:
            import json
            status = engine.get_status()
            print(json.dumps(status, indent=2, default=str))
            
        elif args.continuous:
            engine.run_continuous(args.interval)
            
        else:
            result = engine.run_ingestion()
            print(f"Ingestion completed: {result['total_rows']} rows in {result['duration_seconds']:.1f}s")
            
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()