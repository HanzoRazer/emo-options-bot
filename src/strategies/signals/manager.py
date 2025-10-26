"""
Strategy Manager for signals-based framework.
"""

from __future__ import annotations
import csv
import os
from pathlib import Path
from typing import Dict, Any, List, Iterable, Tuple, Callable, Optional
from datetime import datetime

from .base import BaseStrategy, Signal
from .iron_condor import IronCondor
from .put_credit_spread import PutCreditSpread


class StrategyManager:
    """
    Manages multiple signals-based strategies and handles signal output.
    
    This manager complements the existing options strategy system by providing
    a lightweight signals-based approach for strategy evaluation.
    """
    
    def __init__(self, out_csv: Path, registry: Dict[str, Callable[..., BaseStrategy]] | None = None):
        """
        Initialize the Strategy Manager.
        
        Args:
            out_csv: Path to CSV file for signal output
            registry: Optional custom strategy registry
        """
        self.out_csv = Path(out_csv)
        self.registry = registry or {
            "IronCondor": IronCondor,
            "PutCreditSpread": PutCreditSpread,
        }
        self.enabled: Dict[str, BaseStrategy] = {}
        self._last_run_time: Optional[datetime] = None
        self._total_signals_generated = 0

    def register(self, name: str, **kwargs) -> None:
        """
        Register and enable a strategy.
        
        Args:
            name: Strategy name (must be in registry)
            **kwargs: Strategy configuration parameters
            
        Raises:
            KeyError: If strategy name not found in registry
        """
        if name not in self.registry:
            available = ", ".join(self.registry.keys())
            raise KeyError(f"Unknown strategy: {name}. Available: {available}")
        
        self.enabled[name] = self.registry[name](**kwargs)
        print(f"[StrategyManager] Registered {name} with config: {kwargs}")

    def list_available_strategies(self) -> List[str]:
        """Get list of available strategy names."""
        return list(self.registry.keys())

    def list_enabled_strategies(self) -> List[str]:
        """Get list of currently enabled strategy names."""
        return list(self.enabled.keys())

    def warmup(self, **kwargs) -> None:
        """
        Warm up all enabled strategies.
        
        This should be called once before running strategy evaluation cycles.
        """
        print(f"[StrategyManager] Warming up {len(self.enabled)} strategies...")
        for strategy_name, strategy in self.enabled.items():
            try:
                strategy.warmup(**kwargs)
            except Exception as e:
                print(f"[StrategyManager] Warning: {strategy_name} warmup failed: {e}")

    def _ensure_header(self) -> None:
        """Ensure CSV file exists with proper header."""
        if not self.out_csv.exists():
            self.out_csv.parent.mkdir(parents=True, exist_ok=True)
            with open(self.out_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ts", "symbol", "strategy", "action", "confidence", "notes"])

    def write_signals(self, signals: Iterable[Signal]) -> int:
        """
        Write signals to CSV file.
        
        Args:
            signals: Iterable of Signal objects to write
            
        Returns:
            Number of signals written
        """
        self._ensure_header()
        
        signal_count = 0
        with open(self.out_csv, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for signal in signals:
                writer.writerow([
                    signal.ts, 
                    signal.symbol, 
                    signal.strategy, 
                    signal.action, 
                    f"{signal.confidence:.3f}", 
                    signal.notes
                ])
                signal_count += 1
        
        self._total_signals_generated += signal_count
        return signal_count

    def run_once(self, md_stream: Iterable[Dict[str, Any]]) -> List[Signal]:
        """
        Run one evaluation cycle across all enabled strategies.
        
        Args:
            md_stream: Iterable of market data dictionaries (one per symbol)
            
        Returns:
            List of all generated signals
        """
        all_signals: List[Signal] = []
        
        # Convert to list to allow multiple iterations
        market_data_list = list(md_stream)
        
        # Evaluate each strategy against each market data point
        for strategy_name, strategy in self.enabled.items():
            strategy_signals = []
            
            for md in market_data_list:
                try:
                    signals = strategy.evaluate(md)
                    strategy_signals.extend(signals)
                except Exception as e:
                    print(f"[StrategyManager] Error in {strategy_name}.evaluate(): {e}")
                    # Create an error signal for tracking
                    error_signal = Signal(
                        ts=Signal.now_iso(),
                        symbol=md.get("symbol", "UNKNOWN"),
                        strategy=strategy_name,
                        action="hold",
                        confidence=0.0,
                        notes=f"Evaluation error: {str(e)[:100]}"
                    )
                    strategy_signals.append(error_signal)
            
            all_signals.extend(strategy_signals)
            
            # Log strategy activity
            if strategy_signals:
                actions = [s.action for s in strategy_signals]
                enter_count = actions.count("enter")
                exit_count = actions.count("exit")
                hold_count = actions.count("hold")
                print(f"[StrategyManager] {strategy_name}: {enter_count} enter, {exit_count} exit, {hold_count} hold")

        # Write signals to CSV if any were generated
        if all_signals:
            written_count = self.write_signals(all_signals)
            print(f"[StrategyManager] Generated {len(all_signals)} signals, wrote {written_count} to {self.out_csv}")
        
        self._last_run_time = datetime.now()
        return all_signals

    def get_stats(self) -> Dict[str, Any]:
        """
        Get strategy manager statistics.
        
        Returns:
            Dictionary with manager statistics
        """
        stats = {
            "enabled_strategies": len(self.enabled),
            "available_strategies": len(self.registry),
            "total_signals_generated": self._total_signals_generated,
            "last_run_time": self._last_run_time.isoformat() if self._last_run_time else None,
            "output_file": str(self.out_csv),
            "output_file_exists": self.out_csv.exists()
        }
        
        # Add file stats if CSV exists
        if self.out_csv.exists():
            try:
                with open(self.out_csv, "r", encoding="utf-8") as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                    stats["total_rows_in_csv"] = len(rows) - 1  # Exclude header
            except Exception as e:
                stats["csv_read_error"] = str(e)
        
        return stats

    def read_recent_signals(self, limit: int = 50) -> List[Dict[str, str]]:
        """
        Read recent signals from CSV file.
        
        Args:
            limit: Maximum number of recent signals to return
            
        Returns:
            List of signal dictionaries (most recent first)
        """
        if not self.out_csv.exists():
            return []
        
        try:
            with open(self.out_csv, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Return most recent signals first
            return list(reversed(rows[-limit:]))
        
        except Exception as e:
            print(f"[StrategyManager] Error reading signals: {e}")
            return []

    def cleanup_old_signals(self, keep_days: int = 30) -> int:
        """
        Remove signals older than specified days.
        
        Args:
            keep_days: Number of days of signals to keep
            
        Returns:
            Number of rows removed
        """
        if not self.out_csv.exists():
            return 0
        
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            with open(self.out_csv, "r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Filter rows to keep only recent ones
            filtered_rows = []
            removed_count = 0
            
            for row in rows:
                try:
                    signal_time = datetime.fromisoformat(row["ts"].replace("Z", "+00:00"))
                    if signal_time >= cutoff_date:
                        filtered_rows.append(row)
                    else:
                        removed_count += 1
                except (ValueError, KeyError):
                    # Keep rows with unparseable timestamps
                    filtered_rows.append(row)
            
            # Write back filtered data
            if removed_count > 0:
                with open(self.out_csv, "w", newline="", encoding="utf-8") as f:
                    if filtered_rows:
                        fieldnames = filtered_rows[0].keys()
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(filtered_rows)
                    else:
                        # Write just the header if no rows remain
                        writer = csv.writer(f)
                        writer.writerow(["ts", "symbol", "strategy", "action", "confidence", "notes"])
            
            return removed_count
        
        except Exception as e:
            print(f"[StrategyManager] Error cleaning up old signals: {e}")
            return 0

    def __repr__(self) -> str:
        """String representation of the strategy manager."""
        return (f"StrategyManager(enabled={len(self.enabled)}, "
                f"available={len(self.registry)}, output='{self.out_csv}')")