#!/usr/bin/env python3
"""
Integration Utilities for EMO Options Bot Order Staging
Shows how to integrate staging into existing trading workflows.
"""

import os
import sys
import functools
from typing import Any, Dict, Optional, Callable
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# For demonstration - would be actual broker APIs in production
class MockBroker:
    """Mock broker API for demonstration purposes."""
    
    def submit_order(self, symbol: str, side: str, qty: float, order_type: str, 
                    limit_price: Optional[float] = None, **kwargs) -> Dict[str, Any]:
        """Simulate broker order submission."""
        print(f"🔗 MOCK BROKER: Submitting {side} {qty} {symbol} ({order_type})")
        if limit_price:
            print(f"   Limit Price: ${limit_price:.2f}")
        return {
            "order_id": "MOCK123456",
            "status": "SUBMITTED",
            "symbol": symbol,
            "side": side,
            "qty": qty
        }

# Create a mock broker instance
broker = MockBroker()

def staging_aware_order(func: Callable) -> Callable:
    """
    Decorator to make any order function staging-aware.
    
    If EMO_STAGE_ORDERS=1, orders are staged instead of executed.
    Otherwise, they are executed normally through the broker.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Check if staging is enabled
        stage_enabled = os.getenv("EMO_STAGE_ORDERS", "").strip() == "1"
        
        if stage_enabled:
            # Import here to avoid circular dependencies
            from exec.stage_order import StageOrderClient
            
            print("📋 STAGING MODE: Order will be staged, not executed")
            
            # Extract order parameters from function call
            # Handle both positional and keyword arguments
            if args:
                # Handle case where function is called with positional args
                if hasattr(args[0], '__dict__'):  # Skip 'self' parameter for methods
                    symbol = kwargs.get('symbol') or (args[1] if len(args) > 1 else None)
                    side = kwargs.get('side') or (args[2] if len(args) > 2 else 'buy')
                    qty = kwargs.get('qty') or (args[3] if len(args) > 3 else 1)
                else:
                    symbol = kwargs.get('symbol') or (args[0] if args else None)
                    side = kwargs.get('side') or (args[1] if len(args) > 1 else 'buy')
                    qty = kwargs.get('qty') or (args[2] if len(args) > 2 else 1)
            else:
                symbol = kwargs.get('symbol')
                side = kwargs.get('side', 'buy')
                qty = kwargs.get('qty', 1)
            
            order_type = kwargs.get('order_type', 'market')
            limit_price = kwargs.get('limit_price')
            
            # Add function metadata
            meta = kwargs.get('meta', {})
            meta.update({
                'original_function': func.__name__,
                'function_module': func.__module__,
                'staging_intercepted': True
            })
            
            # Stage the order
            try:
                client = StageOrderClient()
                result = client.stage_order(
                    symbol=str(symbol) if symbol else "UNKNOWN",
                    side=str(side) if side else "buy",
                    qty=float(qty) if qty else 1.0,
                    order_type=str(order_type),
                    limit_price=limit_price,
                    meta=meta
                )
                
                return {
                    'staged': True,
                    'staged_file': str(result) if result else None,
                    'original_function': func.__name__
                }
            except Exception as e:
                print(f"❌ Staging error: {e}")
                return {
                    'staged': True,
                    'staged_file': None,
                    'original_function': func.__name__,
                    'error': str(e)
                }
        else:
            # Execute normally
            print("🚀 EXECUTION MODE: Order will be executed via broker")
            return func(*args, **kwargs)
    
    return wrapper

# Example integration functions

@staging_aware_order
def buy_market_order(symbol: str, qty: float, **kwargs) -> Dict[str, Any]:
    """Buy market order - staging aware."""
    return broker.submit_order(symbol, "buy", qty, "market", **kwargs)

@staging_aware_order  
def sell_limit_order(symbol: str, qty: float, limit_price: float, **kwargs) -> Dict[str, Any]:
    """Sell limit order - staging aware."""
    return broker.submit_order(symbol, "sell", qty, "limit", limit_price=limit_price, **kwargs)

@staging_aware_order
def iron_condor_entry(symbol: str, contracts: int = 1, **kwargs) -> Dict[str, Any]:
    """Iron condor strategy entry - staging aware."""
    # Simplified iron condor implementation
    meta = kwargs.get('meta', {})
    meta.update({
        'strategy': 'iron_condor',
        'contracts': contracts,
        'complexity': 'multi_leg'
    })
    kwargs['meta'] = meta
    
    return broker.submit_order(
        symbol=symbol, 
        side="buy", 
        qty=contracts, 
        order_type="limit",
        limit_price=100.0,  # Simplified
        **kwargs
    )

class TradingWorkflow:
    """Example trading workflow class with staging integration."""
    
    def __init__(self, staging_enabled: Optional[bool] = None):
        self.staging_enabled = staging_enabled
        if staging_enabled is not None:
            os.environ["EMO_STAGE_ORDERS"] = "1" if staging_enabled else "0"
    
    def execute_strategy(self, strategy_name: str, symbol: str, **params) -> Dict[str, Any]:
        """Execute a trading strategy with automatic staging support."""
        print(f"🎯 Executing strategy: {strategy_name} on {symbol}")
        
        # Route to appropriate strategy function
        strategy_map = {
            'buy_and_hold': self._buy_and_hold,
            'iron_condor': self._iron_condor,
            'covered_call': self._covered_call,
        }
        
        strategy_func = strategy_map.get(strategy_name)
        if not strategy_func:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        return strategy_func(symbol, **params)
    
    @staging_aware_order
    def _buy_and_hold(self, symbol: str, qty: float = 100, **kwargs) -> Dict[str, Any]:
        """Simple buy and hold strategy."""
        return broker.submit_order(symbol, "buy", qty, "market", **kwargs)
    
    @staging_aware_order  
    def _iron_condor(self, symbol: str, contracts: int = 1, **kwargs) -> Dict[str, Any]:
        """Iron condor options strategy."""
        meta = kwargs.get('meta', {})
        meta.update({
            'strategy': 'iron_condor',
            'legs': 4,
            'contracts': contracts
        })
        kwargs['meta'] = meta
        
        # Simplified - would normally place 4 separate orders
        return broker.submit_order(symbol, "buy", contracts, "limit", limit_price=100.0, **kwargs)
    
    @staging_aware_order
    def _covered_call(self, symbol: str, shares: int = 100, **kwargs) -> Dict[str, Any]:
        """Covered call strategy."""
        meta = kwargs.get('meta', {})
        meta.update({
            'strategy': 'covered_call',
            'underlying_shares': shares
        })
        kwargs['meta'] = meta
        
        return broker.submit_order(symbol, "sell", shares//100, "limit", limit_price=50.0, **kwargs)

def demo_staging_integration():
    """Demonstrate staging integration with existing code."""
    print("🔗 STAGING INTEGRATION DEMO")
    print("=" * 60)
    
    print("\n1. Testing with STAGING DISABLED")
    print("-" * 40)
    os.environ.pop("EMO_STAGE_ORDERS", None)  # Disable staging
    
    result1 = buy_market_order("AAPL", 100)
    print(f"Result: {result1}")
    
    result2 = sell_limit_order("TSLA", 50, 250.00)
    print(f"Result: {result2}")
    
    print("\n2. Testing with STAGING ENABLED")
    print("-" * 40)
    os.environ["EMO_STAGE_ORDERS"] = "1"  # Enable staging
    
    result3 = buy_market_order("SPY", 200, meta={"note": "test buy"})
    print(f"Result: {result3}")
    
    result4 = iron_condor_entry("QQQ", contracts=2)
    print(f"Result: {result4}")
    
    print("\n3. Testing Trading Workflow")
    print("-" * 40)
    
    workflow = TradingWorkflow(staging_enabled=True)
    
    strategies = [
        ("buy_and_hold", "NVDA", {"qty": 25}),
        ("iron_condor", "MSFT", {"contracts": 3}),
        ("covered_call", "GOOG", {"shares": 100})
    ]
    
    for strategy, symbol, params in strategies:
        try:
            result = workflow.execute_strategy(strategy, symbol, **params)
            print(f"✅ {strategy} on {symbol}: {result.get('staged', 'executed')}")
        except Exception as e:
            print(f"❌ {strategy} on {symbol}: {e}")

def demo_conditional_staging():
    """Demonstrate conditional staging based on order size or risk."""
    print("\n4. Testing Conditional Staging")
    print("-" * 40)
    
    # Reset environment
    os.environ.pop("EMO_STAGE_ORDERS", None)
    
    def conditional_order(symbol: str, side: str, qty: float, **kwargs):
        """Order function that stages large orders automatically."""
        # Stage orders over $10,000 or more than 1000 shares
        price = kwargs.get('limit_price', 100.0)  # Estimate for market orders
        dollar_value = qty * price
        
        should_stage = (qty > 1000 or dollar_value > 10000)
        
        if should_stage:
            print(f"⚠️  Large order detected (${dollar_value:.2f}), forcing staging mode")
            original_env = os.environ.get("EMO_STAGE_ORDERS")
            os.environ["EMO_STAGE_ORDERS"] = "1"
            
            try:
                result = buy_market_order(symbol, qty, **kwargs)
                return result
            finally:
                # Restore original environment
                if original_env is None:
                    os.environ.pop("EMO_STAGE_ORDERS", None)
                else:
                    os.environ["EMO_STAGE_ORDERS"] = original_env
        else:
            return buy_market_order(symbol, qty, **kwargs)
    
    # Test small order (should execute)
    print("📋 Small order (50 shares):")
    result1 = conditional_order("AAPL", "buy", 50)
    print(f"   Result: {'Staged' if result1.get('staged') else 'Executed'}")
    
    # Test large order (should stage)  
    print("📋 Large order (2000 shares):")
    result2 = conditional_order("AAPL", "buy", 2000)
    print(f"   Result: {'Staged' if result2.get('staged') else 'Executed'}")

def main():
    """Run integration demos."""
    print("🚀 EMO OPTIONS BOT - STAGING INTEGRATION PATTERNS")
    print("=" * 80)
    
    try:
        demo_staging_integration()
        demo_conditional_staging()
        
        print("\n" + "=" * 80)
        print("🎉 INTEGRATION DEMOS COMPLETED")
        print("=" * 80)
        
        print("\nIntegration Patterns Demonstrated:")
        print("✅ Decorator-based staging integration")
        print("✅ Class-based workflow staging")
        print("✅ Conditional staging based on order size")
        print("✅ Metadata preservation through staging")
        print("✅ Environment-based staging control")
        print("✅ Backwards compatibility with existing code")
        
        print("\nProduction Integration Steps:")
        print("1. Add @staging_aware_order decorator to order functions")
        print("2. Set EMO_STAGE_ORDERS=1 for staging environments")
        print("3. Review staged orders before enabling execution")
        print("4. Gradually migrate existing order functions")
        
    except Exception as e:
        print(f"\n❌ Integration demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()