#!/usr/bin/env python3
"""
Enhanced Data Collector with Risk Management Integration
Collects market data and feeds it into risk management calculations.
"""

from __future__ import annotations
import os, sqlite3, time, json
from pathlib import Path
from typing import List, Dict, Any, Iterable, Tuple, Optional
import requests
from datetime import datetime, timezone
import pandas as pd

# Import risk management
import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.logic.risk_manager import RiskManager, PortfolioSnapshot, Position
from src.database.models import get_db_connection

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
DB = DATA / "emo.sqlite"

class EnhancedDataCollector:
    """Enhanced data collector with risk management integration."""
    
    def __init__(self):
        self.risk_manager = RiskManager()
        self._ensure_database()
    
    def _ensure_database(self):
        """Ensure database and tables exist."""
        DATA.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(DB) as conn:
            # Core market data tables (match existing schema)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bars (
                    symbol TEXT NOT NULL,
                    ts TEXT NOT NULL,
                    open REAL, high REAL, low REAL, close REAL,
                    volume INTEGER,
                    PRIMARY KEY(symbol, ts)
                )
            """)
            
            # Additional enhanced data table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS enhanced_bars (
                    symbol TEXT NOT NULL,
                    t      INTEGER NOT NULL,  -- epoch ms
                    o REAL, h REAL, l REAL, c REAL, v INTEGER,
                    tf TEXT NOT NULL,
                    PRIMARY KEY(symbol, t, tf)
                )
            """)
            
            # Risk metrics table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS risk_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    portfolio_heat REAL,
                    beta_exposure REAL,
                    num_positions INTEGER,
                    total_risk REAL,
                    equity REAL,
                    cash REAL,
                    violations TEXT,  -- JSON array of violations
                    warnings TEXT     -- JSON array of warnings
                )
            """)
            
            # Position snapshots table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS position_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    symbol TEXT NOT NULL,
                    qty REAL,
                    mark REAL,
                    value REAL,
                    max_loss REAL,
                    beta REAL,
                    sector TEXT
                )
            """)
            
            # Market regime indicators
            conn.execute("""
                CREATE TABLE IF NOT EXISTS market_regime (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    regime TEXT,  -- 'bull', 'bear', 'sideways', 'volatile'
                    vix_level REAL,
                    trend_strength REAL,
                    volatility_regime TEXT,
                    correlation_regime TEXT
                )
            """)
            
            # Create indexes
            conn.execute("CREATE INDEX IF NOT EXISTS ix_bars_symbol_ts ON bars(symbol,ts)")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_enhanced_bars_symbol_t_tf ON enhanced_bars(symbol,t,tf)")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_risk_metrics_timestamp ON risk_metrics(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_position_snapshots_timestamp ON position_snapshots(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_market_regime_timestamp ON market_regime(timestamp)")
    
    def _alpaca_headers(self) -> Dict[str, str]:
        """Get Alpaca API headers."""
        k = os.getenv("ALPACA_KEY_ID", "")
        s = os.getenv("ALPACA_SECRET_KEY", "")
        if not k or not s:
            raise RuntimeError("ALPACA_KEY_ID/ALPACA_SECRET_KEY not set")
        return {"APCA-API-KEY-ID": k, "APCA-API-SECRET-KEY": s}
    
    def _alpaca_data_url(self) -> str:
        """Get Alpaca data URL."""
        return os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets/v2").rstrip("/")
    
    def fetch_bars(self, symbol: str, timeframe: str = "1Min", limit: int = 1000) -> List[Dict[str, Any]]:
        """Fetch bars from Alpaca API."""
        url = f"{self._alpaca_data_url()}/stocks/{symbol}/bars"
        params = {"timeframe": timeframe, "limit": limit}
        
        try:
            r = requests.get(url, headers=self._alpaca_headers(), params=params, timeout=20)
            r.raise_for_status()
            js = r.json()
            return js.get("bars", [])
        except Exception as e:
            print(f"[collector] Error fetching {symbol}: {e}")
            return []
    
    def _rows_from_bars(self, symbol: str, timeframe: str, bars: List[Dict[str, Any]]) -> Iterable[Tuple]:
        """Convert bars to database rows."""
        for b in bars:
            # Handle timestamp conversion
            ts = b.get("t")
            if isinstance(ts, str):
                # ISO → epoch ms
                dtobj = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                ms = int(dtobj.timestamp() * 1000)
            else:
                # if epoch ns
                ms = int(ts / 1_000_000) if ts else int(time.time() * 1000)
            
            yield (
                symbol, ms,
                b.get("o"), b.get("h"), b.get("l"), b.get("c"),
                b.get("v"), timeframe
            )
    
    def ingest_market_data(self, symbols: List[str], timeframe: str = "1Min", limit: int = 1000) -> int:
        """Ingest market data with enhanced logging."""
        inserted = 0
        
        with sqlite3.connect(DB) as conn:
            for sym in symbols:
                try:
                    bars = self.fetch_bars(sym, timeframe=timeframe, limit=limit)
                    if bars:
                        rows = list(self._rows_from_bars(sym, timeframe, bars))
                        conn.executemany("""
                            INSERT OR REPLACE INTO enhanced_bars(symbol,t,o,h,l,c,v,tf)
                            VALUES (?,?,?,?,?,?,?,?)
                        """, rows)
                        inserted += len(rows)
                        print(f"[collector] {sym}: {len(rows)} {timeframe} bars")
                    else:
                        print(f"[collector] {sym}: No data received")
                        
                except Exception as e:
                    print(f"[collector] {sym} error: {e}")
        
        print(f"[collector] Total inserted: {inserted} bars")
        return inserted
    
    def calculate_market_regime(self) -> Dict[str, Any]:
        """Calculate current market regime indicators."""
        try:
            with sqlite3.connect(DB) as conn:
                # Get recent price data for SPY (market proxy)
                df = pd.read_sql_query("""
                    SELECT t, c FROM enhanced_bars 
                    WHERE symbol='SPY' AND tf='1Min' 
                    ORDER BY t DESC 
                    LIMIT 500
                """, conn)
                
                if df.empty:
                    return {"regime": "unknown", "vix_level": 0, "trend_strength": 0}
                
                df = df.sort_values('t').reset_index(drop=True)
                df['returns'] = df['c'].pct_change()
                
                # Calculate volatility (simplified VIX proxy)
                volatility = df['returns'].rolling(20).std() * 100
                current_vol = volatility.iloc[-1] if not volatility.empty else 0
                
                # Calculate trend strength
                ma_short = df['c'].rolling(10).mean()
                ma_long = df['c'].rolling(50).mean()
                trend_strength = ((ma_short.iloc[-1] - ma_long.iloc[-1]) / ma_long.iloc[-1] * 100) if len(ma_long.dropna()) > 0 else 0
                
                # Determine regime
                if current_vol > 25:
                    volatility_regime = "high"
                elif current_vol > 15:
                    volatility_regime = "medium"
                else:
                    volatility_regime = "low"
                
                if trend_strength > 2:
                    regime = "bull"
                elif trend_strength < -2:
                    regime = "bear"
                else:
                    regime = "sideways"
                
                regime_data = {
                    "regime": regime,
                    "vix_level": current_vol,
                    "trend_strength": abs(trend_strength),
                    "volatility_regime": volatility_regime,
                    "correlation_regime": "medium"  # Simplified
                }
                
                # Store in database
                timestamp = int(time.time() * 1000)
                conn.execute("""
                    INSERT INTO market_regime 
                    (timestamp, regime, vix_level, trend_strength, volatility_regime, correlation_regime)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (timestamp, regime, current_vol, abs(trend_strength), volatility_regime, "medium"))
                
                return regime_data
                
        except Exception as e:
            print(f"[collector] Market regime calculation error: {e}")
            return {"regime": "unknown", "vix_level": 0, "trend_strength": 0}
    
    def get_mock_portfolio(self) -> PortfolioSnapshot:
        """Get mock portfolio for demonstration."""
        try:
            with sqlite3.connect(DB) as conn:
                # Get latest prices
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT symbol, c FROM enhanced_bars 
                    WHERE tf='1Min' AND symbol IN ('SPY', 'QQQ', 'AAPL', 'MSFT')
                    AND t = (SELECT MAX(t) FROM enhanced_bars WHERE symbol=enhanced_bars.symbol AND tf='1Min')
                """)
                
                prices = dict(cursor.fetchall())
                
                # Create mock positions
                positions = []
                if 'SPY' in prices:
                    positions.append(Position(
                        symbol='SPY', qty=100, mark=prices['SPY'],
                        value=100 * prices['SPY'], max_loss=100 * prices['SPY'] * 0.12,
                        beta=1.0, sector='ETF'
                    ))
                
                if 'QQQ' in prices:
                    positions.append(Position(
                        symbol='QQQ', qty=50, mark=prices['QQQ'],
                        value=50 * prices['QQQ'], max_loss=50 * prices['QQQ'] * 0.15,
                        beta=1.2, sector='ETF'
                    ))
                
                if 'AAPL' in prices:
                    positions.append(Position(
                        symbol='AAPL', qty=25, mark=prices['AAPL'],
                        value=25 * prices['AAPL'], max_loss=25 * prices['AAPL'] * 0.18,
                        beta=1.3, sector='Technology'
                    ))
                
                return PortfolioSnapshot(
                    equity=50000.0,
                    cash=15000.0,
                    positions=positions
                )
                
        except Exception as e:
            print(f"[collector] Portfolio creation error: {e}")
            return PortfolioSnapshot(equity=50000.0, cash=15000.0, positions=[])
    
    def update_risk_metrics(self):
        """Update risk metrics in database."""
        try:
            portfolio = self.get_mock_portfolio()
            assessment = self.risk_manager.assess_portfolio(portfolio)
            
            # Calculate metrics
            total_risk = sum(pos.max_loss for pos in portfolio.positions)
            portfolio_heat = (total_risk / portfolio.equity * 100) if portfolio.equity > 0 else 0
            beta_exposure = sum(pos.value * pos.beta for pos in portfolio.positions) / portfolio.equity if portfolio.equity > 0 else 0
            
            timestamp = int(time.time() * 1000)
            
            with sqlite3.connect(DB) as conn:
                # Store risk metrics
                conn.execute("""
                    INSERT INTO risk_metrics 
                    (timestamp, portfolio_heat, beta_exposure, num_positions, total_risk, equity, cash, violations, warnings)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp, portfolio_heat, beta_exposure, len(portfolio.positions),
                    total_risk, portfolio.equity, portfolio.cash,
                    json.dumps(assessment.get("violations", [])),
                    json.dumps(assessment.get("warnings", []))
                ))
                
                # Store position snapshots
                for pos in portfolio.positions:
                    conn.execute("""
                        INSERT INTO position_snapshots 
                        (timestamp, symbol, qty, mark, value, max_loss, beta, sector)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (timestamp, pos.symbol, pos.qty, pos.mark, pos.value, pos.max_loss, pos.beta, pos.sector))
            
            print(f"[collector] Risk metrics updated - Heat: {portfolio_heat:.1f}%, Beta: {beta_exposure:.2f}")
            
        except Exception as e:
            print(f"[collector] Risk metrics update error: {e}")
    
    def generate_risk_summary(self) -> Dict[str, Any]:
        """Generate risk summary for external systems."""
        try:
            with sqlite3.connect(DB) as conn:
                # Get latest risk metrics
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT portfolio_heat, beta_exposure, num_positions, total_risk, equity, cash, violations, warnings
                    FROM risk_metrics 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                if not row:
                    return {"status": "no_data"}
                
                portfolio_heat, beta_exposure, num_positions, total_risk, equity, cash, violations_json, warnings_json = row
                
                violations = json.loads(violations_json) if violations_json else []
                warnings = json.loads(warnings_json) if warnings_json else []
                
                # Get market regime
                cursor.execute("""
                    SELECT regime, vix_level, trend_strength, volatility_regime
                    FROM market_regime 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                """)
                
                regime_row = cursor.fetchone()
                regime_data = {}
                if regime_row:
                    regime_data = {
                        "regime": regime_row[0],
                        "vix_level": regime_row[1],
                        "trend_strength": regime_row[2],
                        "volatility_regime": regime_row[3]
                    }
                
                return {
                    "status": "active",
                    "timestamp": datetime.now().isoformat(),
                    "portfolio": {
                        "heat_pct": portfolio_heat,
                        "beta_exposure": beta_exposure,
                        "num_positions": num_positions,
                        "total_risk": total_risk,
                        "equity": equity,
                        "cash": cash
                    },
                    "risk_status": {
                        "violations": violations,
                        "warnings": warnings,
                        "overall_status": "violation" if violations else "warning" if warnings else "healthy"
                    },
                    "market_regime": regime_data
                }
                
        except Exception as e:
            print(f"[collector] Risk summary error: {e}")
            return {"status": "error", "error": str(e)}
    
    def full_collection_cycle(self, symbols: List[str] = None):
        """Run a complete data collection and risk assessment cycle."""
        if symbols is None:
            symbols = ["SPY", "QQQ", "IWM", "DIA", "AAPL", "MSFT", "GOOGL", "AMZN"]
        
        print(f"[collector] Starting full collection cycle for {len(symbols)} symbols")
        
        # 1. Collect market data
        bars_inserted = self.ingest_market_data(symbols, timeframe="1Min", limit=500)
        
        # 2. Calculate market regime
        regime = self.calculate_market_regime()
        print(f"[collector] Market regime: {regime['regime']} (vol: {regime['vix_level']:.1f}%)")
        
        # 3. Update risk metrics
        self.update_risk_metrics()
        
        # 4. Generate risk summary
        summary = self.generate_risk_summary()
        
        # 5. Save summary to file for dashboard
        summary_file = DATA / "risk_summary.json"
        summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        
        print(f"[collector] Collection cycle complete - {bars_inserted} bars, status: {summary.get('risk_status', {}).get('overall_status', 'unknown')}")
        return summary

def main():
    """Main entry point for enhanced data collection."""
    collector = EnhancedDataCollector()
    
    # Run collection cycle
    symbols = os.getenv("SYMBOLS", "SPY,QQQ,IWM,DIA,AAPL,MSFT").split(",")
    summary = collector.full_collection_cycle([s.strip() for s in symbols])
    
    print("\n" + "="*50)
    print("RISK SUMMARY")
    print("="*50)
    print(f"Portfolio Heat: {summary.get('portfolio', {}).get('heat_pct', 0):.1f}%")
    print(f"Beta Exposure: {summary.get('portfolio', {}).get('beta_exposure', 0):.2f}")
    print(f"Positions: {summary.get('portfolio', {}).get('num_positions', 0)}")
    print(f"Status: {summary.get('risk_status', {}).get('overall_status', 'unknown').upper()}")
    
    violations = summary.get('risk_status', {}).get('violations', [])
    if violations:
        print("\nVIOLATIONS:")
        for v in violations:
            print(f"  ⚠️  {v}")
    
    warnings = summary.get('risk_status', {}).get('warnings', [])
    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  ⚡ {w}")

if __name__ == "__main__":
    main()