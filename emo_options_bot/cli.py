"""Command-line interface for EMO Options Bot."""

import argparse
import sys
from typing import Optional
import json

from emo_options_bot import EMOOptionsBot
from emo_options_bot.core.config import Config


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="EMO Options Bot - AI-Powered Intelligent Trading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a trading command
  emo-bot process "Buy 1 AAPL call at $150 strike expiring in 30 days"
  
  # Get bot status
  emo-bot status
  
  # List staged strategies
  emo-bot list
  
  # Approve a strategy
  emo-bot approve STRAT_20241215120000000000
  
  # Interactive mode
  emo-bot interactive
        """
    )
    
    parser.add_argument(
        "command",
        choices=["process", "status", "list", "approve", "reject", "interactive"],
        help="Command to execute"
    )
    
    parser.add_argument(
        "args",
        nargs="*",
        help="Command arguments"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config.load(args.config) if args.config else Config.load()
    
    # Initialize bot
    bot = EMOOptionsBot(config)
    
    # Execute command
    if args.command == "process":
        if not args.args:
            print("Error: Trading command required")
            sys.exit(1)
        
        command = " ".join(args.args)
        result = bot.process_command(command)
        
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print_result(result)
    
    elif args.command == "status":
        status = bot.get_status()
        
        if args.json:
            print(json.dumps(status, indent=2, default=str))
        else:
            print_status(status)
    
    elif args.command == "list":
        strategies = bot.get_staged_strategies()
        
        if args.json:
            print(json.dumps(strategies, indent=2, default=str))
        else:
            print_strategies(strategies)
    
    elif args.command == "approve":
        if not args.args:
            print("Error: Strategy ID required")
            sys.exit(1)
        
        strategy_id = args.args[0]
        result = bot.approve_strategy(strategy_id)
        
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print_result(result)
    
    elif args.command == "reject":
        if not args.args:
            print("Error: Strategy ID required")
            sys.exit(1)
        
        strategy_id = args.args[0]
        reason = " ".join(args.args[1:]) if len(args.args) > 1 else ""
        result = bot.reject_strategy(strategy_id, reason)
        
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print_result(result)
    
    elif args.command == "interactive":
        run_interactive_mode(bot)


def print_result(result: dict):
    """Print command result in human-readable format."""
    if result.get("success"):
        print("\n✓ Success!")
        
        if "strategy_id" in result:
            print(f"  Strategy ID: {result['strategy_id']}")
        
        if "strategy" in result:
            strategy = result["strategy"]
            print(f"  Strategy: {strategy['name']}")
            print(f"  Type: {strategy['strategy_type']}")
            print(f"  Orders: {len(strategy['orders'])}")
        
        if "risk_assessment" in result:
            ra = result["risk_assessment"]
            print(f"\n  Risk Assessment:")
            print(f"    Approved: {ra['approved']}")
            print(f"    Risk Score: {ra['risk_score']:.1f}/100")
            print(f"    Max Loss: ${ra['max_loss']}")
            
            if ra.get("warnings"):
                print(f"    Warnings:")
                for warning in ra["warnings"]:
                    print(f"      - {warning}")
        
        if "next_steps" in result:
            print(f"\n  Next Steps: {result['next_steps']}")
        
        if "message" in result:
            print(f"\n  {result['message']}")
    else:
        print("\n✗ Failed!")
        print(f"  Error: {result.get('error', 'Unknown error')}")
        
        if "validation_errors" in result:
            print("  Validation Errors:")
            for error in result["validation_errors"]:
                print(f"    - {error}")
        
        if "risk_assessment" in result:
            ra = result["risk_assessment"]
            if ra.get("violations"):
                print("  Risk Violations:")
                for violation in ra["violations"]:
                    print(f"    - {violation}")


def print_status(status: dict):
    """Print bot status in human-readable format."""
    print("\n=== EMO Options Bot Status ===")
    print(f"Version: {status['bot_version']}")
    
    print("\nConfiguration:")
    for key, value in status['config'].items():
        print(f"  {key}: {value}")
    
    print("\nOrders:")
    for key, value in status['orders'].items():
        print(f"  {key}: {value}")
    
    print("\nPortfolio:")
    for key, value in status['portfolio'].items():
        print(f"  {key}: {value}")
    
    print(f"\nTotal Strategies: {status['strategies_count']}")


def print_strategies(strategies: list):
    """Print staged strategies in human-readable format."""
    if not strategies:
        print("\nNo staged strategies")
        return
    
    print(f"\n=== Staged Strategies ({len(strategies)}) ===\n")
    
    for strategy in strategies:
        print(f"ID: {strategy['id']}")
        print(f"Name: {strategy['name']}")
        print(f"Type: {strategy['strategy_type']}")
        print(f"Orders: {len(strategy['orders'])}")
        print(f"Max Risk: ${strategy['max_risk']}")
        print(f"Created: {strategy['created_at']}")
        print()


def run_interactive_mode(bot: EMOOptionsBot):
    """Run interactive mode."""
    print("\n=== EMO Options Bot - Interactive Mode ===")
    print("Enter trading commands in natural language.")
    print("Type 'status' to see bot status, 'list' to see staged strategies.")
    print("Type 'help' for more commands, 'exit' to quit.\n")
    
    while True:
        try:
            command = input("EMO> ").strip()
            
            if not command:
                continue
            
            if command.lower() in ["exit", "quit", "q"]:
                print("Goodbye!")
                break
            
            elif command.lower() == "help":
                print_help()
            
            elif command.lower() == "status":
                status = bot.get_status()
                print_status(status)
            
            elif command.lower() == "list":
                strategies = bot.get_staged_strategies()
                print_strategies(strategies)
            
            elif command.lower().startswith("approve "):
                strategy_id = command.split()[1]
                result = bot.approve_strategy(strategy_id)
                print_result(result)
            
            elif command.lower().startswith("reject "):
                parts = command.split(maxsplit=2)
                strategy_id = parts[1]
                reason = parts[2] if len(parts) > 2 else ""
                result = bot.reject_strategy(strategy_id, reason)
                print_result(result)
            
            else:
                # Treat as trading command
                result = bot.process_command(command)
                print_result(result)
        
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def print_help():
    """Print help message."""
    print("""
Available commands:
  - Enter any natural language trading command
  - status: Show bot status
  - list: List staged strategies
  - approve <strategy_id>: Approve a staged strategy
  - reject <strategy_id> [reason]: Reject a staged strategy
  - help: Show this help
  - exit/quit/q: Exit interactive mode

Example trading commands:
  - Buy 1 AAPL call at $150 strike expiring in 30 days
  - Sell 5 TSLA puts at $200 strike
  - Buy vertical spread on SPY
    """)


if __name__ == "__main__":
    main()
