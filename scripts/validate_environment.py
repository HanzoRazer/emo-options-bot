#!/usr/bin/env python3
"""
EMO Options Bot Environment Validation Script
Validates your environment configuration and API connectivity
"""

import os
import sys
from pathlib import Path
import importlib

def check_env_file():
    """Check if .env file exists and has required keys"""
    print("🔍 Checking environment configuration...")
    
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found")
        print("   Run: ./setup-env.ps1")
        return False
    
    # Try to load dotenv if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env file loaded with python-dotenv")
    except ImportError:
        print("⚠️ python-dotenv not installed, using OS environment")
        # Manually load .env file
        with open(".env", "r") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value
    
    # Check for required keys
    required_keys = [
        ("OPENAI_API_KEY", "OpenAI API key"),
        ("EMO_ENV", "Environment setting"),
        ("EMO_STAGING_DIR", "Staging directory"),
    ]
    
    optional_keys = [
        ("ANTHROPIC_API_KEY", "Anthropic API key"),
        ("ALPACA_KEY_ID", "Alpaca key ID"),
        ("ALPACA_SECRET_KEY", "Alpaca secret"),
        ("POLYGON_API_KEY", "Polygon API key"),
    ]
    
    has_ai_key = False
    for key, desc in required_keys:
        value = os.getenv(key, "").strip()
        if value and value != "":
            print(f"✅ {desc}: {'*' * 8}")
            if key == "OPENAI_API_KEY":
                has_ai_key = True
        else:
            print(f"❌ {desc}: Not set")
    
    # Check for at least one AI provider
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if anthropic_key and anthropic_key != "":
        print(f"✅ Anthropic API key: {'*' * 8}")
        has_ai_key = True
    
    if not has_ai_key:
        print("❌ No AI provider configured (need OPENAI_API_KEY or ANTHROPIC_API_KEY)")
        return False
    
    print("\n📋 Optional configuration:")
    for key, desc in optional_keys:
        value = os.getenv(key, "").strip()
        if value and value != "":
            print(f"✅ {desc}: {'*' * 8}")
        else:
            print(f"⚠️ {desc}: Not configured")
    
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    print("\n🔍 Checking Python dependencies...")
    
    required_packages = [
        ("yfinance", "Yahoo Finance data"),
        ("requests", "HTTP requests"),
        ("dataclasses", "Data structures"),
    ]
    
    optional_packages = [
        ("openai", "OpenAI API client"),
        ("anthropic", "Anthropic API client"),
        ("alpaca_trade_api", "Alpaca trading"),
        ("polygon", "Polygon market data"),
        ("python-dotenv", "Environment loading"),
    ]
    
    missing_required = []
    for package, desc in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {desc}: Available")
        except ImportError:
            print(f"❌ {desc}: Missing")
            missing_required.append(package)
    
    print("\n📋 Optional packages:")
    for package, desc in optional_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {desc}: Available")
        except ImportError:
            print(f"⚠️ {desc}: Not installed")
    
    if missing_required:
        print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
        print("Install with: pip install -r requirements-ml.txt")
        return False
    
    return True

def check_directories():
    """Check if required directories exist"""
    print("\n🔍 Checking directory structure...")
    
    required_dirs = [
        "ops/staged_orders",
        "ops/staged_orders/backup",
        "logs",
        "data",
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✅ Directory exists: {dir_path}")
        else:
            print(f"❌ Directory missing: {dir_path}")
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"\nCreating missing directories...")
        for dir_path in missing_dirs:
            try:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                print(f"✅ Created: {dir_path}")
            except Exception as e:
                print(f"❌ Failed to create {dir_path}: {e}")
                return False
    
    return True

def test_ai_connectivity():
    """Test AI provider connectivity"""
    print("\n🔍 Testing AI provider connectivity...")
    
    # Test OpenAI
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    if openai_key and openai_key != "":
        try:
            import openai
            client = openai.OpenAI(api_key=openai_key)
            # Simple test call
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            print("✅ OpenAI API: Connected")
        except Exception as e:
            print(f"❌ OpenAI API: {str(e)[:50]}...")
    
    # Test Anthropic
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    if anthropic_key and anthropic_key != "":
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=anthropic_key)
            # Simple test call
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=5,
                messages=[{"role": "user", "content": "Hello"}]
            )
            print("✅ Anthropic API: Connected")
        except Exception as e:
            print(f"❌ Anthropic API: {str(e)[:50]}...")

def test_market_data():
    """Test market data connectivity"""
    print("\n🔍 Testing market data connectivity...")
    
    # Test YFinance (free)
    try:
        import yfinance as yf
        ticker = yf.Ticker("SPY")
        info = ticker.info
        if 'regularMarketPrice' in info:
            print(f"✅ YFinance: SPY price ${info['regularMarketPrice']:.2f}")
        else:
            print("⚠️ YFinance: Connected but no price data")
    except Exception as e:
        print(f"❌ YFinance: {str(e)[:50]}...")
    
    # Test Alpaca (if configured)
    alpaca_key = os.getenv("ALPACA_KEY_ID", "").strip()
    alpaca_secret = os.getenv("ALPACA_SECRET_KEY", "").strip()
    if alpaca_key and alpaca_secret:
        try:
            import alpaca_trade_api as tradeapi
            api = tradeapi.REST(
                alpaca_key,
                alpaca_secret,
                os.getenv("ALPACA_API_BASE", "https://paper-api.alpaca.markets"),
                api_version='v2'
            )
            account = api.get_account()
            print(f"✅ Alpaca API: Connected (${account.cash} cash)")
        except Exception as e:
            print(f"❌ Alpaca API: {str(e)[:50]}...")

def main():
    """Main validation function"""
    print("🚀 EMO Options Bot Environment Validation")
    print("=" * 50)
    
    checks = [
        ("Environment File", check_env_file),
        ("Python Dependencies", check_dependencies),
        ("Directory Structure", check_directories),
    ]
    
    passed = 0
    for name, check_func in checks:
        try:
            if check_func():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            print()
    
    # Connectivity tests (non-blocking)
    print("🌐 Connectivity Tests (Optional)")
    print("-" * 30)
    try:
        test_ai_connectivity()
    except Exception as e:
        print(f"⚠️ AI connectivity test failed: {e}")
    
    try:
        test_market_data()
    except Exception as e:
        print(f"⚠️ Market data test failed: {e}")
    
    print("\n" + "=" * 50)
    if passed == len(checks):
        print("✅ Environment validation PASSED")
        print("🚀 Ready to run EMO Options Bot!")
        print("\nNext steps:")
        print("   python scripts/simple_options_demo.py")
        return 0
    else:
        print(f"❌ Environment validation FAILED ({passed}/{len(checks)} passed)")
        print("\nPlease fix the issues above and run again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())