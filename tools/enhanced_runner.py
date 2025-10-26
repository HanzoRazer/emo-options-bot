"""
Enhanced Runner with Strategy Signals Integration
Combines existing EMO data collection with new signals framework.
"""

import sys
import csv
import json
from pathlib import Path
from typing import Dict, Any, List
import datetime as dt

# Ensure src is on path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from src.strategies.signals import StrategyManager, IronCondor, PutCreditSpread
from src.web.enhanced_dashboard import EnhancedDashboard

# LLM routing imports
import os
try:
    from llm.plan_router import route_plan
except Exception:
    route_plan = None

# Paths
DATA_DIR = ROOT / "data"
OPS_DIR = ROOT / "ops"
SIGNALS_CSV = OPS_DIR / "signals.csv"
ML_JSON = DATA_DIR / "ml_outlook.json"

# LLM routing configuration
ENABLE_LLM_ROUTING = True   # discover + route LLM plans
LLM_PLANS_DIR = ROOT / "ops" / "llm_plans"  # drop *.json plans here
LLM_PLANS_DIR.mkdir(parents=True, exist_ok=True)

class EnhancedRunner:
    """Enhanced runner that integrates signals with existing infrastructure."""
    
    def __init__(self):
        self.strategy_manager = StrategyManager(SIGNALS_CSV)
        self.dashboard = EnhancedDashboard()
        
    def setup_strategies(self):
        """Setup and configure signal-based strategies."""
        print("[Runner] Setting up strategy signals...")
        
        # Register strategies with configuration
        self.strategy_manager.register("IronCondor", config={"min_ivr": 0.25})
        self.strategy_manager.register("PutCreditSpread", config={"min_ivr": 0.15})
        
        # Warm up strategies
        self.strategy_manager.warmup()
        
    def collect_market_data(self) -> List[Dict[str, Any]]:
        """
        Collect market data for strategy evaluation.
        
        This simulates/adapts data from existing EMO data sources.
        In a real implementation, this would read from your existing CSV files.
        """
        symbols = ["SPY", "QQQ", "AAPL", "MSFT"]
        market_data = []
        
        for symbol in symbols:
            # Mock data - replace with actual data collection
            md = {
                "symbol": symbol,
                "ivr": self._get_iv_rank(symbol),
                "trend": self._get_trend(symbol),
                "current_price": self._get_current_price(symbol),
                "volume": self._get_volume(symbol)
            }
            market_data.append(md)
            
        return market_data
    
    def _get_iv_rank(self, symbol: str) -> float:
        """Get IV rank for symbol (mock implementation)."""
        # In real implementation, read from iv_history.csv or database
        import random
        base_ivr = {
            "SPY": 0.30,
            "QQQ": 0.35, 
            "AAPL": 0.40,
            "MSFT": 0.25
        }.get(symbol, 0.30)
        
        # Add some randomness
        return max(0.0, min(1.0, base_ivr + random.uniform(-0.15, 0.15)))
    
    def _get_trend(self, symbol: str) -> str:
        """Get trend for symbol (mock implementation)."""
        # In real implementation, analyze recent price data
        import random
        trends = ["up", "down", "sideways", "mixed"]
        weights = [0.3, 0.2, 0.3, 0.2]  # Slightly bullish bias
        return random.choices(trends, weights=weights)[0]
    
    def _process_llm_queue(self):
        """Process LLM plans from the queue directory."""
        if not ENABLE_LLM_ROUTING or route_plan is None:
            return
        pending = sorted(LLM_PLANS_DIR.glob("*.json"))
        if not pending:
            return
        print(f"🧠 Found {len(pending)} LLM plan(s) to process...")
        for f in pending:
            try:
                plan = json.loads(f.read_text(encoding="utf-8"))
                res = route_plan(plan)  # obeys EMO_ORDER_MODE / EMO_BROKER
                print("  →", res)
                # move processed plan
                processed = f.with_suffix(".processed.json")
                f.rename(processed)
            except Exception as e:
                print(f"  ⚠️ LLM plan error {f.name}: {e}")
    
    def _get_current_price(self, symbol: str) -> float:
        """Get current price for symbol (mock implementation)."""
        # Mock prices - in real implementation, get from market data
        return {
            "SPY": 450.0,
            "QQQ": 380.0,
            "AAPL": 175.0,
            "MSFT": 330.0
        }.get(symbol, 100.0)
    
    def _get_volume(self, symbol: str) -> int:
        """Get volume for symbol (mock implementation)."""
        # Mock volumes
        return {
            "SPY": 50000000,
            "QQQ": 30000000,
            "AAPL": 40000000,
            "MSFT": 25000000
        }.get(symbol, 1000000)
    
    def create_mock_ml_outlook(self):
        """Create mock ML outlook data for dashboard demonstration."""
        ml_data = {
            "prediction": "slightly_bullish",
            "confidence": 0.67,
            "models": ["LSTM", "RandomForest", "XGBoost"],
            "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
            "notes": "Market showing mild bullish signals with moderate confidence"
        }
        
        # Ensure data directory exists
        DATA_DIR.mkdir(exist_ok=True)
        
        # Write ML outlook
        ML_JSON.write_text(json.dumps(ml_data, indent=2), encoding="utf-8")
        print(f"[Runner] Created mock ML outlook: {ML_JSON}")
    
    def run_cycle(self) -> Dict[str, Any]:
        """Run one complete cycle of data collection and strategy evaluation."""
        print(f"\n[Runner] Starting cycle at {dt.datetime.now()}")
        
        # Ensure directories exist
        OPS_DIR.mkdir(exist_ok=True)
        DATA_DIR.mkdir(exist_ok=True)
        
        # Create mock ML outlook for dashboard
        self.create_mock_ml_outlook()
        
        # Collect market data
        market_data = self.collect_market_data()
        print(f"[Runner] Collected data for {len(market_data)} symbols")
        
        # Run strategy evaluation
        signals = self.strategy_manager.run_once(market_data)
        
        # Process LLM plans queue
        try:
            self._process_llm_queue()
        except Exception as e:
            print(f"⚠️ LLM routing error: {e}")
        
        # Generate dashboard
        dashboard_file = self.dashboard.build_dashboard()
        
        # Return cycle summary
        result = {
            "timestamp": dt.datetime.now().isoformat(),
            "symbols_processed": len(market_data),
            "signals_generated": len(signals),
            "dashboard_updated": str(dashboard_file),
            "signals": [
                {
                    "symbol": s.symbol,
                    "strategy": s.strategy,
                    "action": s.action,
                    "confidence": s.confidence
                }
                for s in signals
            ]
        }
        
        print(f"[Runner] Cycle complete: {len(signals)} signals generated")
        return result
    
    def run_continuous(self, cycles: int = 5, delay: int = 30):
        """Run multiple cycles with delay between them."""
        import time
        
        print(f"[Runner] Starting {cycles} cycles with {delay}s delays...")
        
        results = []
        for i in range(cycles):
            print(f"\n{'='*50}")
            print(f"CYCLE {i+1}/{cycles}")
            print(f"{'='*50}")
            
            result = self.run_cycle()
            results.append(result)
            
            if i < cycles - 1:  # Don't delay after last cycle
                print(f"[Runner] Waiting {delay} seconds...")
                time.sleep(delay)
        
        # Save results summary
        summary_file = DATA_DIR / "runner_summary.json"
        summary = {
            "total_cycles": len(results),
            "total_signals": sum(len(r["signals"]) for r in results),
            "cycles": results
        }
        
        summary_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"\n[Runner] All cycles complete. Summary saved to {summary_file}")
        
        return summary


def main():
    """Main entry point for enhanced runner."""
    runner = EnhancedRunner()
    
    # Setup strategies
    runner.setup_strategies()
    
    # Run a single cycle by default
    try:
        result = runner.run_cycle()
        
        print(f"\n{'='*50}")
        print("RUNNER SUMMARY")
        print(f"{'='*50}")
        print(f"✅ Symbols processed: {result['symbols_processed']}")
        print(f"✅ Signals generated: {result['signals_generated']}")
        print(f"✅ Dashboard updated: {result['dashboard_updated']}")
        
        if result['signals']:
            print(f"\n📊 Generated Signals:")
            for signal in result['signals']:
                action_emoji = {"enter": "🟢", "exit": "🔴", "hold": "🟡"}.get(signal['action'], "⚪")
                print(f"  {action_emoji} {signal['symbol']} - {signal['strategy']}: {signal['action'].upper()} (conf: {signal['confidence']:.2f})")
        
        print(f"\n🎯 View dashboard at: file://{Path(result['dashboard_updated']).resolve()}")
        print(f"📄 Strategy signals saved to: {SIGNALS_CSV}")
        
    except Exception as e:
        print(f"❌ Runner failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())