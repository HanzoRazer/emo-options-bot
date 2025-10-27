"""
Example 3: Risk Management - Custom Configuration

This example demonstrates custom risk configuration and management.
"""

from emo_options_bot import EMOOptionsBot
from emo_options_bot.core.config import Config, RiskConfig, TradingConfig
from decimal import Decimal


def main():
    print("Configuring Custom Risk Parameters...")
    
    # Create custom configuration
    config = Config(
        risk=RiskConfig(
            max_position_size=5000.0,      # Max $5k per position
            max_portfolio_exposure=20000.0, # Max $20k total exposure
            max_loss_per_trade=500.0,       # Max $500 loss per trade
            max_loss_per_day=2000.0,        # Max $2k loss per day
            enable_risk_checks=True
        ),
        trading=TradingConfig(
            enable_paper_trading=True,
            require_manual_approval=True,
            max_orders_per_day=20
        )
    )
    
    print(f"  Max Position Size: ${config.risk.max_position_size}")
    print(f"  Max Portfolio Exposure: ${config.risk.max_portfolio_exposure}")
    print(f"  Max Loss Per Trade: ${config.risk.max_loss_per_trade}")
    print(f"  Max Loss Per Day: ${config.risk.max_loss_per_day}")
    
    # Initialize bot with custom config
    bot = EMOOptionsBot(config)
    
    # Test with a trade within limits
    print("\n--- Test 1: Trade Within Limits ---")
    result1 = bot.process_command("Buy 1 AAPL call at $150")
    
    if result1["success"]:
        risk = result1['risk_assessment']
        print(f"✓ Trade approved")
        print(f"  Risk Score: {risk['risk_score']:.1f}/100")
        print(f"  Max Loss: ${risk['max_loss']}")
    else:
        print(f"✗ Trade rejected: {result1['error']}")
    
    # Test with a trade that exceeds limits
    print("\n--- Test 2: Trade Exceeding Limits ---")
    result2 = bot.process_command("Buy 100 TSLA call at $250")
    
    if result2["success"]:
        print(f"✓ Trade approved (unexpected)")
    else:
        print(f"✗ Trade rejected (expected)")
        if 'risk_assessment' in result2:
            violations = result2['risk_assessment']['violations']
            print(f"  Violations:")
            for violation in violations:
                print(f"    - {violation}")
    
    # Get portfolio summary
    print("\n--- Portfolio Summary ---")
    summary = bot.get_portfolio_summary()
    print(f"  Cash: ${summary['cash']:.2f}")
    print(f"  Total Value: ${summary['total_value']:.2f}")
    print(f"  Positions: {summary['positions_count']}")
    print(f"  Daily P&L: ${summary['daily_pnl']:.2f}")
    
    # Get bot status
    print("\n--- Bot Status ---")
    status = bot.get_status()
    print(f"  Version: {status['bot_version']}")
    print(f"  Paper Trading: {status['config']['paper_trading']}")
    print(f"  Staged Orders: {status['orders']['total_staged']}")
    print(f"  Total Strategies: {status['strategies_count']}")


if __name__ == "__main__":
    main()
