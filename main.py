#!/usr/bin/env python3
"""
EMO Options Bot - Main Application Entry Point
"""

import sys
import argparse
from pathlib import Path

# Add src to Python path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from src.web.dashboard import main as dashboard_main
from src.ml.outlook import main as outlook_main
from src.database.data_collector import collect_live_data
from src.utils.config import get_project_info, ensure_data_directories

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description="EMO Options Bot - ML-powered options trading analysis")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser("dashboard", help="Start web dashboard")
    dashboard_parser.add_argument("--host", default="localhost", help="Dashboard host")
    dashboard_parser.add_argument("--port", type=int, default=8083, help="Dashboard port")
    
    # ML outlook command
    outlook_parser = subparsers.add_parser("outlook", help="Generate ML outlook")
    outlook_parser.add_argument("--symbols", nargs="+", help="Symbols to analyze")
    
    # Data collection command
    data_parser = subparsers.add_parser("collect", help="Collect live market data")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Show project information")
    
    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Initialize project directories")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Ensure directories exist
    ensure_data_directories()
    
    if args.command == "dashboard":
        print("🚀 Starting EMO Options Bot Dashboard...")
        dashboard_main()
        
    elif args.command == "outlook":
        print("🧠 Generating ML Outlook...")
        outlook_main(args.symbols)
        
    elif args.command == "collect":
        print("📊 Collecting live market data...")
        try:
            count = collect_live_data()
            print(f"✅ Collected {count} bars")
        except Exception as e:
            print(f"❌ Error collecting data: {e}")
            
    elif args.command == "info":
        info = get_project_info()
        print("📊 EMO Options Bot - Project Information")
        print("=" * 50)
        for key, value in info.items():
            print(f"{key:15}: {value}")
            
    elif args.command == "setup":
        print("⚙️ Setting up EMO Options Bot...")
        ensure_data_directories()
        print(f"✅ Created data directories")
        print(f"   Data: {ROOT}/data/")
        print(f"   Scripts: {ROOT}/scripts/")
        print(f"   Tests: {ROOT}/tests/")

if __name__ == "__main__":
    main()