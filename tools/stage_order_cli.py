#!/usr/bin/env python3
"""
Command-line interface for the EMO Options Bot Order Staging System
Provides easy command-line access to order staging functionality.
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from exec.stage_order import StageOrderClient, get_staging_stats
from i18n.lang import t, get_supported_languages

def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with internationalized help."""
    lang = os.getenv("EMO_LANG", "en")
    
    parser = argparse.ArgumentParser(
        description=t("cli_help", lang),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  # Stage a market order
  {sys.argv[0]} -s SPY --side buy --qty 100

  # Stage a limit order
  {sys.argv[0]} -s AAPL --side sell --qty 50 --type limit --limit 150.00

  # Stage with strategy and metadata
  {sys.argv[0]} -s QQQ --side buy --qty 25 --strategy iron_condor --format yaml

  # Use different language
  EMO_LANG=es {sys.argv[0]} -s TSLA --side buy --qty 10

Environment Variables:
  EMO_STAGE_ORDERS=1   Enable order staging (required)
  EMO_LANG=en|es|fr    Set language for messages
        """
    )
    
    # Required arguments (only when not using special commands)
    parser.add_argument(
        "-s", "--symbol", 
        help=t("cli_symbol_help", lang)
    )
    parser.add_argument(
        "--side", 
        choices=["buy", "sell"], 
        help=t("cli_side_help", lang)
    )
    parser.add_argument(
        "--qty", 
        type=float, 
        help=t("cli_qty_help", lang)
    )
    
    # Optional arguments
    parser.add_argument(
        "--type", 
        dest="order_type", 
        choices=["market", "limit"], 
        default="market",
        help=t("cli_type_help", lang)
    )
    parser.add_argument(
        "--limit", 
        dest="limit_price", 
        type=float,
        help=t("cli_limit_help", lang)
    )
    parser.add_argument(
        "--tif", 
        dest="time_in_force", 
        choices=["day", "gtc", "ioc", "fok"],
        default="day",
        help=t("cli_tif_help", lang)
    )
    parser.add_argument(
        "--strategy",
        help=t("cli_strategy_help", lang)
    )
    parser.add_argument(
        "--format", 
        choices=["yaml", "json"], 
        default="yaml",
        help=t("cli_format_help", lang)
    )
    parser.add_argument(
        "--lang", 
        choices=get_supported_languages(),
        default=lang,
        help=t("cli_lang_help", lang)
    )
    
    # Action arguments
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show staging statistics instead of staging an order"
    )
    parser.add_argument(
        "--list",
        action="store_true", 
        help="List all draft files"
    )
    parser.add_argument(
        "--cleanup",
        type=int,
        metavar="DAYS",
        help="Clean up draft files older than DAYS"
    )
    
    # Metadata arguments
    parser.add_argument(
        "--note",
        help="Add a note to the order metadata"
    )
    parser.add_argument(
        "--user",
        help="Specify the user creating the order"
    )
    
    return parser

def handle_stats_command(client: StageOrderClient, lang: str) -> None:
    """Handle the stats command."""
    stats = client.get_stats()
    
    print(f"📊 {t('staging_stats_title', lang, default='Order Staging Statistics')}")
    print("=" * 50)
    
    if not stats.get("enabled"):
        print(t("staging_disabled", lang))
        return
    
    print(f"📄 Total drafts: {stats['total_drafts']}")
    print(f"📋 YAML files: {stats['yaml_files']}")
    print(f"📋 JSON files: {stats['json_files']}")
    print(f"🌍 Language: {stats['language']}")
    print(f"📁 Directory: {stats['drafts_dir']}")
    
    if stats.get("by_symbol"):
        print(f"\n📈 By Symbol:")
        for symbol, count in sorted(stats["by_symbol"].items()):
            print(f"   {symbol}: {count}")
    
    if stats.get("by_side"):
        print(f"\n📊 By Side:")
        for side, count in stats["by_side"].items():
            print(f"   {side}: {count}")

def handle_list_command(client: StageOrderClient, lang: str) -> None:
    """Handle the list command."""
    drafts = client.list_drafts()
    
    print(f"📄 {t('draft_files_title', lang, default='Draft Order Files')}")
    print("=" * 50)
    
    if not drafts:
        print(t("no_drafts_found", lang, default="No draft files found"))
        return
    
    print(f"Found {len(drafts)} draft files:")
    for draft in sorted(drafts):
        try:
            data = client.load_draft(draft)
            if data:
                symbol = data.get("symbol", "?")
                side = data.get("side", "?")
                qty = data.get("qty", "?")
                status = data.get("status", "?")
                strategy = data.get("strategy", "")
                strategy_info = f" ({strategy})" if strategy else ""
                print(f"   📋 {draft.name}: {symbol} {side} {qty}{strategy_info} [{status}]")
            else:
                print(f"   ❌ {draft.name}: Failed to load")
        except Exception:
            print(f"   ⚠️  {draft.name}: Error loading")

def handle_cleanup_command(client: StageOrderClient, days: int, lang: str) -> None:
    """Handle the cleanup command."""
    print(f"🧹 {t('cleaning_old_drafts', lang, default='Cleaning drafts older than')} {days} {t('days', lang, default='days')}...")
    
    cleaned = client.clean_old_drafts(days)
    
    if cleaned > 0:
        print(f"✅ {t('cleaned_files', lang, default='Cleaned')} {cleaned} {t('files', lang, default='files')}")
    else:
        print(f"ℹ️  {t('no_files_to_clean', lang, default='No files to clean')}")

def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Set language from args if provided
    if args.lang:
        os.environ["EMO_LANG"] = args.lang
    
    lang = args.lang
    
    try:
        # Create client
        client = StageOrderClient(lang=lang)
        
        # Handle special commands
        if args.stats:
            handle_stats_command(client, lang)
            return
        
        if args.list:
            handle_list_command(client, lang)
            return
        
        if args.cleanup is not None:
            handle_cleanup_command(client, args.cleanup, lang)
            return
        
        # For order staging, require the essential arguments
        if not args.symbol or not args.side or args.qty is None:
            parser.error("Order staging requires --symbol, --side, and --qty arguments")
            return
        
        # Build metadata
        meta = {}
        if args.note:
            meta["note"] = args.note
        if args.user:
            meta["user"] = args.user
        
        # Add CLI metadata
        meta["created_via"] = "cli"
        meta["cli_version"] = "1.0.0"
        
        # Stage the order
        result = client.stage_order(
            symbol=args.symbol,
            side=args.side,
            qty=args.qty,
            order_type=args.order_type,
            time_in_force=args.time_in_force,
            limit_price=args.limit_price,
            strategy=args.strategy,
            meta=meta,
            out_format=args.format
        )
        
        if result:
            print(f"\n✅ {t('order_staged_successfully', lang, default='Order staged successfully')}")
            print(f"📄 {t('file_location', lang, default='File')}: {result}")
        else:
            print(f"\n❌ {t('order_staging_failed', lang, default='Order staging failed')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n👋 {t('operation_cancelled', lang, default='Operation cancelled by user')}")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ {t('unexpected_error', lang, default='Unexpected error')}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()