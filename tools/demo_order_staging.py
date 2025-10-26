#!/usr/bin/env python3
"""
Demo script for the Order Staging System
Tests various order staging scenarios and multi-language support.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from exec.stage_order import StageOrderClient, stage_market_order, stage_limit_order, get_staging_stats
from i18n.lang import get_supported_languages

def demo_staging_disabled():
    """Demo when staging is disabled."""
    print("🚫 STAGING DISABLED DEMO")
    print("=" * 50)
    
    # Ensure staging is disabled
    os.environ.pop("EMO_STAGE_ORDERS", None)
    
    client = StageOrderClient()
    result = client.stage_order("SPY", "buy", 100, "market")
    
    print(f"Result: {result}")
    print("✅ Staging disabled demo completed\n")

def demo_staging_enabled():
    """Demo when staging is enabled."""
    print("✅ STAGING ENABLED DEMO")
    print("=" * 50)
    
    # Enable staging
    os.environ["EMO_STAGE_ORDERS"] = "1"
    
    client = StageOrderClient()
    
    # Test various order types
    orders = [
        {"symbol": "SPY", "side": "buy", "qty": 100, "order_type": "market", "strategy": "momentum"},
        {"symbol": "QQQ", "side": "sell", "qty": 50, "order_type": "limit", "limit_price": 350.00, "strategy": "profit_taking"},
        {"symbol": "AAPL", "side": "buy", "qty": 25, "order_type": "limit", "limit_price": 150.00, "strategy": "iron_condor"},
    ]
    
    staged_files = []
    for order in orders:
        print(f"\n📋 Staging {order['symbol']} {order['side']} order...")
        result = client.stage_order(**order)
        if result:
            staged_files.append(result)
    
    print(f"\n📊 Staged {len(staged_files)} orders")
    print("✅ Staging enabled demo completed\n")
    
    return staged_files

def demo_validation_errors():
    """Demo validation error handling."""
    print("❌ VALIDATION ERRORS DEMO")
    print("=" * 50)
    
    os.environ["EMO_STAGE_ORDERS"] = "1"
    client = StageOrderClient()
    
    # Test various invalid inputs
    invalid_orders = [
        {"symbol": "", "side": "buy", "qty": 100, "order_type": "market"},  # Empty symbol
        {"symbol": "SPY", "side": "invalid", "qty": 100, "order_type": "market"},  # Invalid side
        {"symbol": "SPY", "side": "buy", "qty": -10, "order_type": "market"},  # Negative quantity
        {"symbol": "SPY", "side": "buy", "qty": 100, "order_type": "invalid"},  # Invalid order type
        {"symbol": "SPY", "side": "buy", "qty": 100, "order_type": "limit"},  # Missing limit price
    ]
    
    for i, order in enumerate(invalid_orders, 1):
        print(f"\n{i}. Testing invalid order: {order}")
        result = client.stage_order(**order)
        print(f"   Result: {'❌ Rejected' if result is None else '✅ Accepted'}")
    
    print("\n✅ Validation demo completed\n")

def demo_multilingual_support():
    """Demo multi-language support."""
    print("🌍 MULTILINGUAL SUPPORT DEMO")
    print("=" * 50)
    
    os.environ["EMO_STAGE_ORDERS"] = "1"
    
    languages = get_supported_languages()
    print(f"Supported languages: {', '.join(languages)}")
    
    for lang in languages:
        print(f"\n--- Testing in {lang.upper()} ---")
        os.environ["EMO_LANG"] = lang
        
        client = StageOrderClient()
        # Test with a valid order
        result = client.stage_order("MSFT", "buy", 10, "market", strategy="test")
        
        # Test with invalid order to see error messages
        client.stage_order("", "invalid", -5, "badtype")
    
    print("\n✅ Multilingual demo completed\n")

def demo_convenience_functions():
    """Demo convenience functions."""
    print("🛠️  CONVENIENCE FUNCTIONS DEMO")
    print("=" * 50)
    
    os.environ["EMO_STAGE_ORDERS"] = "1"
    
    # Test convenience functions
    print("📋 Staging market order...")
    market_result = stage_market_order("TSLA", "buy", 5, strategy="breakout")
    
    print("\n📋 Staging limit order...")
    limit_result = stage_limit_order("NVDA", "sell", 2, 500.00, strategy="profit_taking")
    
    print(f"\nMarket order result: {market_result}")
    print(f"Limit order result: {limit_result}")
    
    print("\n✅ Convenience functions demo completed\n")

def demo_file_management():
    """Demo file management features."""
    print("📁 FILE MANAGEMENT DEMO")
    print("=" * 50)
    
    os.environ["EMO_STAGE_ORDERS"] = "1"
    client = StageOrderClient()
    
    # Get statistics
    stats = client.get_stats()
    print("📊 Current Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # List draft files
    drafts = client.list_drafts()
    print(f"\n📄 Found {len(drafts)} draft files:")
    for draft in drafts[:5]:  # Show first 5
        print(f"   • {draft.name}")
    
    # Load and display a draft
    if drafts:
        print(f"\n📖 Loading draft: {drafts[0].name}")
        data = client.load_draft(drafts[0])
        if data:
            print(f"   Symbol: {data.get('symbol')}")
            print(f"   Side: {data.get('side')}")
            print(f"   Quantity: {data.get('qty')}")
            print(f"   Status: {data.get('status')}")
    
    print("\n✅ File management demo completed\n")

def demo_global_stats():
    """Demo global statistics function."""
    print("📈 GLOBAL STATISTICS DEMO")
    print("=" * 50)
    
    os.environ["EMO_STAGE_ORDERS"] = "1"
    
    stats = get_staging_stats()
    print("📊 Global Staging Statistics:")
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for subkey, subvalue in value.items():
                print(f"      {subkey}: {subvalue}")
        else:
            print(f"   {key}: {value}")
    
    print("\n✅ Global statistics demo completed\n")

def main():
    """Run all staging demos."""
    print("🚀 EMO OPTIONS BOT - ORDER STAGING SYSTEM DEMO")
    print("=" * 80)
    print("Testing order staging functionality with multi-language support")
    print("=" * 80)
    
    try:
        # Run all demos
        demo_staging_disabled()
        demo_staging_enabled()
        demo_validation_errors()
        demo_multilingual_support()
        demo_convenience_functions()
        demo_file_management()
        demo_global_stats()
        
        print("=" * 80)
        print("🎉 ALL STAGING DEMOS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("\nKey Features Demonstrated:")
        print("✅ Order staging with safety controls")
        print("✅ Multi-language support (EN/ES/FR)")
        print("✅ Input validation and error handling")
        print("✅ File integrity with signatures")
        print("✅ Convenient staging functions")
        print("✅ Statistics and management tools")
        print("✅ YAML and JSON format support")
        
        print(f"\nTo enable staging: set EMO_STAGE_ORDERS=1")
        print(f"To set language: set EMO_LANG=en|es|fr")
        
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()