from __future__ import annotations
import json
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from .base import Strategy, Order

# Import risk management
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from src.logic.risk_manager import RiskManager, OrderIntent, PortfolioSnapshot

class StrategyManager:
    def __init__(self, risk_manager: Optional[RiskManager] = None):
        self._strategies: Dict[str, Strategy] = {}
        self._alloc: Dict[str, float] = {}  # weights 0..1 per strategy
        self.risk_manager = risk_manager or RiskManager()
        self.order_history: List[Dict[str, Any]] = []
        
    def register(self, name: str, strat: Strategy, weight: float = 1.0):
        """Register a strategy with allocation weight."""
        self._strategies[name] = strat
        self._alloc[name] = weight
        print(f"[StrategyManager] Registered {name} with weight {weight}")

    def names(self) -> List[str]:
        """Get list of registered strategy names."""
        return list(self._strategies.keys())
    
    def get_strategy(self, name: str) -> Optional[Strategy]:
        """Get strategy by name."""
        return self._strategies.get(name)

    def decide(self, snapshot: Dict[str, Any], portfolio: Optional[PortfolioSnapshot] = None) -> List[Order]:
        """
        Fan-out to strategies with risk management integration.
        snapshot: {'symbol':'SPY', 'ivr':..., 'shock':..., ...}
        portfolio: Current portfolio for risk assessment
        """
        all_orders: List[Order] = []
        
        # Generate orders from all strategies
        for name, strat in self._strategies.items():
            try:
                if not strat.validate_snapshot(snapshot):
                    print(f"[StrategyManager] {name}: Invalid snapshot, skipping")
                    continue
                    
                weight = self._alloc.get(name, 1.0)
                strategy_orders = strat.generate(snapshot)
                
                # Apply allocation weight
                for order in strategy_orders:
                    if hasattr(order, "qty") and isinstance(order.qty, int) and order.qty > 0:
                        order.qty = max(1, int(round(order.qty * weight)))
                    
                    # Add strategy metadata
                    if not order.meta:
                        order.meta = {}
                    order.meta["strategy"] = name
                    order.meta["weight"] = weight
                    order.meta["generated_at"] = datetime.now().isoformat()
                    
                    all_orders.append(order)
                    
                print(f"[StrategyManager] {name}: Generated {len(strategy_orders)} orders")
                
            except Exception as e:
                print(f"[StrategyManager] Error in strategy {name}: {e}")
                continue
        
        # Apply risk management if portfolio provided
        if portfolio is not None:
            filtered_orders = self._apply_risk_management(all_orders, portfolio)
            print(f"[StrategyManager] Risk filtering: {len(all_orders)} -> {len(filtered_orders)} orders")
            return filtered_orders
        
        return all_orders
    
    def _apply_risk_management(self, orders: List[Order], portfolio: PortfolioSnapshot) -> List[Order]:
        """Apply risk management to filter orders."""
        approved_orders = []
        
        for order in orders:
            # Convert Order to OrderIntent for risk validation
            order_intent = OrderIntent(
                symbol=order.symbol,
                side=order.side,
                est_max_loss=self._estimate_max_loss(order),
                est_value=self._estimate_order_value(order),
                beta=order.meta.get("beta", 1.0) if order.meta else 1.0
            )
            
            # Validate with risk manager
            success, violations = self.risk_manager.validate_order(order_intent, portfolio)
            
            if success:
                approved_orders.append(order)
                self._log_order("APPROVED", order, [])
            else:
                self._log_order("REJECTED", order, violations)
                print(f"[StrategyManager] REJECTED {order.symbol} {order.side}: {'; '.join(violations)}")
        
        return approved_orders
    
    def _estimate_max_loss(self, order: Order) -> float:
        """Estimate maximum loss for an order."""
        # Simple estimation - in practice this would be more sophisticated
        base_value = self._estimate_order_value(order)
        
        if order.type in ["iron_condor_open", "put_credit_spread_open"]:
            # Credit spreads: max loss is usually the width minus credit
            width = order.meta.get("width", 5) if order.meta else 5
            return float(width * order.qty * 100 * 0.8)  # Assume 80% of width as max loss
        elif order.type in ["long_straddle_open", "covered_call_open"]:
            # Debit strategies: max loss is premium paid
            return base_value * 0.5  # Assume 50% loss potential
        else:
            # Default: assume 20% max loss
            return base_value * 0.2
    
    def _estimate_order_value(self, order: Order) -> float:
        """Estimate notional value of an order."""
        # Simple estimation - in practice would use current market prices
        if order.type.endswith("_open"):
            # Options trades: assume $500 per contract
            return float(order.qty * 500)
        else:
            # Stock trades: assume $100 per share (would use actual price)
            return float(order.qty * 100)
    
    def _log_order(self, status: str, order: Order, violations: List[str]) -> None:
        """Log order decision for audit trail."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "order": order.to_dict(),
            "violations": violations
        }
        self.order_history.append(log_entry)
    
    def get_strategy_performance(self) -> Dict[str, Any]:
        """Get performance summary for all strategies."""
        performance = {}
        for name, strategy in self._strategies.items():
            performance[name] = strategy.get_performance_summary()
        return performance
    
    def get_order_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent order history."""
        return self.order_history[-limit:]
    
    def save_to_database(self, db_connection) -> None:
        """Save strategy orders and performance to database."""
        try:
            # Save recent orders
            for log_entry in self.order_history[-50:]:  # Last 50 orders
                order = log_entry["order"]
                db_connection.execute("""
                    INSERT OR REPLACE INTO strategy_orders 
                    (ts, symbol, strategy, side, qty, order_type, status, meta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_entry["timestamp"],
                    order["symbol"],
                    order.get("meta", {}).get("strategy", "unknown"),
                    order["side"],
                    order["qty"],
                    order["type"],
                    log_entry["status"].lower(),
                    json.dumps(order.get("meta", {}))
                ))
            
            # Save strategy performance
            for name, perf in self.get_strategy_performance().items():
                db_connection.execute("""
                    INSERT OR REPLACE INTO strategy_performance
                    (strategy, symbol, period_start, period_end, total_pnl, win_rate, trades_count, meta)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name,
                    "ALL",  # Aggregate across all symbols
                    datetime.now().date().isoformat(),
                    datetime.now().date().isoformat(),
                    perf["total_pnl"],
                    perf["win_rate"],
                    perf["total_trades"],
                    json.dumps(perf)
                ))
                
            print("[StrategyManager] Saved to database successfully")
            
        except Exception as e:
            print(f"[StrategyManager] Database save error: {e}")
    
    def generate_report(self) -> str:
        """Generate a summary report."""
        report = []
        report.append("=== STRATEGY MANAGER REPORT ===")
        report.append(f"Registered Strategies: {len(self._strategies)}")
        
        for name, strategy in self._strategies.items():
            weight = self._alloc.get(name, 1.0)
            perf = strategy.get_performance_summary()
            report.append(f"\n{name.upper()} (Weight: {weight:.1%})")
            report.append(f"  Trades: {perf['total_trades']}")
            report.append(f"  Win Rate: {perf['win_rate']:.1%}")
            report.append(f"  Total PnL: ${perf['total_pnl']:.2f}")
        
        recent_orders = len([o for o in self.order_history if o["status"] == "APPROVED"])
        rejected_orders = len([o for o in self.order_history if o["status"] == "REJECTED"])
        
        report.append(f"\nRecent Orders: {recent_orders} approved, {rejected_orders} rejected")
        report.append("=" * 35)
        
        return "\n".join(report)