"""
Integration utilities for signals framework with existing EMO infrastructure.
These functions can be added to existing runners and data collection scripts.
"""

import csv
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import datetime as dt

# Get the root directory
ROOT = Path(__file__).resolve().parent.parent


def setup_signals_integration(signals_csv_path: Optional[Path] = None) -> 'StrategyManager':
    """
    Setup signals integration for existing runners.
    
    Usage in existing runners:
        from tools.integration_utils import setup_signals_integration, run_signals_cycle
        
        # In main() setup:
        strat_mgr = setup_signals_integration()
        
        # In each data collection cycle:
        signals = run_signals_cycle(strat_mgr, md_stream)
    """
    import sys
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "src"))
    
    from src.strategies.signals import StrategyManager
    
    # Default path
    if signals_csv_path is None:
        signals_csv_path = ROOT / "ops" / "signals.csv"
    
    # Create StrategyManager
    strat_mgr = StrategyManager(signals_csv_path)
    
    # Register strategies with default config (can be made configurable later)
    strat_mgr.register("IronCondor", config={"min_ivr": 0.25})
    strat_mgr.register("PutCreditSpread", config={"min_ivr": 0.15})
    
    # Warm up
    strat_mgr.warmup()
    
    return strat_mgr


def run_signals_cycle(strategy_manager: 'StrategyManager', md_stream: List[Dict[str, Any]]) -> List['Signal']:
    """
    Run strategy signals evaluation cycle.
    
    Args:
        strategy_manager: Initialized StrategyManager
        md_stream: List of market data dicts with keys like:
                  - symbol: str
                  - ivr: float (0-1)
                  - trend: str ("up", "down", "sideways", "mixed")
                  - Optional: price, volume, etc.
    
    Returns:
        List of generated Signal objects
    """
    signals = strategy_manager.run_once(md_stream)
    
    if signals:
        print(f"🟢 Strategy signals: {len(signals)} (written to {strategy_manager.out_csv})")
    
    return signals


def _safe_read_latest_float(csv_path: Path, symbol: str, col: str) -> float:
    """
    Safely read latest float value from CSV file for a symbol.
    
    Helper function for adapting existing data sources to signals framework.
    """
    try:
        if not csv_path.exists():
            return float("nan")
        
        with open(csv_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        
        # Find latest row for symbol
        for row in reversed(rows):
            if row.get("symbol") == symbol and row.get(col):
                return float(row[col])
                
    except Exception:
        pass
    
    return float("nan")


def _infer_trend(csv_path: Path, symbol: str) -> str:
    """
    Infer trend from price data in CSV file.
    
    Simple trend heuristic using last few closes.
    Replace with your existing indicators later.
    """
    try:
        if not csv_path.exists():
            return "mixed"
        
        closes = []
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("symbol") == symbol and row.get("close"):
                    closes.append(float(row["close"]))
        
        if len(closes) < 8:
            return "mixed"
        
        # Simple trend detection on last 8 closes
        recent = closes[-8:]
        up_moves = sum(1 for i in range(1, len(recent)) if recent[i] > recent[i-1])
        
        if up_moves >= 6:
            return "up"
        elif up_moves <= 2:
            return "down"
        else:
            return "sideways"
            
    except Exception:
        return "mixed"


def _symbols() -> List[str]:
    """Get default symbols list."""
    return ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]


def create_md_stream_from_existing_data(symbols: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Create market data stream from existing EMO data files.
    
    This adapts your existing data collection to the signals framework.
    Modify the file paths and data extraction logic to match your setup.
    """
    if symbols is None:
        symbols = _symbols()
    
    md_stream = []
    
    for symbol in symbols:
        # Adapt these paths to your existing data structure
        iv_file = ROOT / "ops" / "iv_history.csv"
        price_file = ROOT / "ops" / "describer_log_v2.csv"  # or wherever your price data is
        
        # Extract data using helper functions
        ivr = _safe_read_latest_float(iv_file, symbol, "ivr")
        trend = _infer_trend(price_file, symbol)
        
        # Create market data dict for signals framework
        md = {
            "symbol": symbol,
            "ivr": ivr if not float("nan") else 0.25,  # Default if no data
            "trend": trend
        }
        
        # Add optional fields if available
        current_price = _safe_read_latest_float(price_file, symbol, "close")
        if not float("nan"):
            md["current_price"] = current_price
        
        md_stream.append(md)
    
    return md_stream


def add_signals_to_existing_runner(runner_code: str = "") -> str:
    """
    Generate code snippet to add to existing runners.
    
    Returns Python code that can be inserted into existing runner scripts.
    """
    
    integration_code = '''
# --- Enhanced EMO with Strategy Signals Integration ---
# Add near the top of your runner script, after imports:

from pathlib import Path
from tools.integration_utils import setup_signals_integration, run_signals_cycle, create_md_stream_from_existing_data

ROOT = Path(__file__).resolve().parent  # Adjust as needed
SIGNALS_CSV = ROOT / "ops" / "signals.csv"

# --- In your main() setup, after printing config ---
print("[Runner] Setting up strategy signals integration...")
strat_mgr = setup_signals_integration(SIGNALS_CSV)

# --- Inside each data collection cycle, after your existing data collection ---
# Option 1: Use existing data files
md_stream = create_md_stream_from_existing_data()

# Option 2: Create md_stream manually from your existing data collection
# md_stream = []
# for symbol in your_symbols:
#     md_stream.append({
#         "symbol": symbol,
#         "ivr": your_iv_data[symbol],  # 0.0 to 1.0
#         "trend": your_trend_analysis[symbol]  # "up", "down", "sideways", "mixed"
#     })

# Generate and save signals
signals = run_signals_cycle(strat_mgr, md_stream)

# Optionally log signal details
if signals:
    for signal in signals:
        action_emoji = {"enter": "🟢", "exit": "🔴", "hold": "🟡"}.get(signal.action, "⚪")
        print(f"  {action_emoji} {signal.symbol} - {signal.strategy}: {signal.action.upper()} (conf: {signal.confidence:.2f})")

# --- To enhance your dashboard (if you have one) ---
# Add this where you generate/update your dashboard:
from src.web.enhanced_dashboard import EnhancedDashboard

dashboard = EnhancedDashboard()
dashboard_file = dashboard.build_dashboard()
print(f"📊 Enhanced dashboard updated: {dashboard_file}")

# --- End Integration Code ---
'''
    
    return integration_code


def create_mock_ml_outlook(output_path: Optional[Path] = None) -> Path:
    """Create mock ML outlook for dashboard testing."""
    if output_path is None:
        output_path = ROOT / "data" / "ml_outlook.json"
    
    # Ensure directory exists
    output_path.parent.mkdir(exist_ok=True)
    
    # Create mock ML data
    ml_data = {
        "prediction": "slightly_bullish",
        "confidence": 0.67,
        "models": ["LSTM", "RandomForest"],
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "notes": "Mock ML outlook for dashboard testing"
    }
    
    # Write to file
    output_path.write_text(json.dumps(ml_data, indent=2), encoding="utf-8")
    
    return output_path


if __name__ == "__main__":
    # Demo of integration utilities
    print("🔧 EMO Strategy Signals Integration Utilities")
    print("=" * 50)
    
    # Show integration code
    print("\n📋 Code to add to existing runners:")
    print("-" * 40)
    print(add_signals_to_existing_runner())
    
    # Create mock ML outlook
    ml_file = create_mock_ml_outlook()
    print(f"\n✅ Created mock ML outlook: {ml_file}")
    
    # Demo signals setup
    print(f"\n🎯 Demo: Setting up signals integration...")
    strat_mgr = setup_signals_integration()
    
    # Demo market data
    md_stream = create_md_stream_from_existing_data(["SPY", "QQQ"])
    print(f"📊 Created market data for {len(md_stream)} symbols")
    
    # Demo signals generation
    signals = run_signals_cycle(strat_mgr, md_stream)
    print(f"🚀 Generated {len(signals)} signals")
    
    print(f"\n✅ Integration utilities ready for use!")