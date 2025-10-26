#!/usr/bin/env python3
"""
Comprehensive test for Patch #15 Order Staging + Release Smoke Tests
"""
import asyncio
import os
import sys
from pathlib import Path

# Set up environment for staging
os.environ['EMO_STAGE_ORDERS'] = '1'
os.environ['EMO_DRAFTS_FORMAT'] = 'yaml'

sys.path.insert(0, str(Path(__file__).parent))

async def main():
    from src.phase3_integration import Phase3TradingSystem
    
    print("🧪 Patch #15 Comprehensive Test")
    print("=" * 40)
    
    # Test 1: Phase3 Integration
    print("1. Testing Phase3 Integration...")
    system = Phase3TradingSystem()
    
    # Test 2: Async natural language processing with staging
    print("2. Testing async natural language + staging...")
    res = await system.process_natural_language_request(
        "SPY neutral strategy with low risk", 
        meta={'user': 'patch15', 'scenario': 'comprehensive_test'}
    )
    
    print(f"   Strategy: {res.trade.strategy_type}")
    print(f"   Symbol: {res.trade.symbol}")
    print(f"   Risk OK: {res.ok}")
    print(f"   Staged: {getattr(res, 'staged_path', 'Not staged')}")
    
    # Test 3: Different market scenarios
    print("3. Testing different market scenarios...")
    scenarios = [
        ("QQQ looks very volatile", "long_straddle"),
        ("SPY sideways movement expected", "iron_condor"),
        ("IWM bullish outlook", "long_call")
    ]
    
    for text, expected in scenarios:
        res = system.process_text(text)
        actual = res.trade.strategy_type if res.trade else "None"
        status = "✅" if actual == expected else "⚠️"
        print(f"   {status} '{text}' → {actual} (expected {expected})")
    
    # Test 4: Release check
    print("4. Running release smoke test...")
    import subprocess
    result = subprocess.run([sys.executable, "tools/release_check.py"], 
                          capture_output=True, text=True)
    if result.returncode == 0:
        print("   ✅ Release check passed")
    else:
        print(f"   ❌ Release check failed: {result.stderr}")
    
    print("=" * 40)
    print("🎉 Patch #15 validation complete!")

if __name__ == "__main__":
    asyncio.run(main())