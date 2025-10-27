"""
Example 2: Advanced Usage - Vertical Spread Strategy

This example demonstrates creating and analyzing a vertical spread strategy.
"""

from emo_options_bot import EMOOptionsBot
from emo_options_bot.trading.strategy_engine import StrategyEngine
from emo_options_bot.risk.risk_manager import RiskManager
from emo_options_bot.core.models import OptionType
from decimal import Decimal
from datetime import datetime, timedelta


def main():
    print("Creating Vertical Spread Strategy...")
    
    # Initialize components
    engine = StrategyEngine()
    risk_manager = RiskManager()
    
    # Create a vertical spread
    strategy = engine.create_vertical_spread(
        underlying="SPY",
        option_type=OptionType.CALL,
        long_strike=Decimal("450"),
        short_strike=Decimal("455"),
        expiration=(datetime.now() + timedelta(days=30)).date(),
        quantity=2
    )
    
    print(f"\n✓ Strategy Created:")
    print(f"  Name: {strategy.name}")
    print(f"  Type: {strategy.strategy_type}")
    print(f"  Legs: {len(strategy.orders)}")
    print(f"  Max Risk: ${strategy.max_risk}")
    print(f"  Max Profit: ${strategy.max_profit}")
    
    # Validate strategy
    print("\nValidating strategy...")
    is_valid, errors = engine.validate_strategy(strategy)
    
    if is_valid:
        print("✓ Strategy is valid")
    else:
        print("✗ Strategy validation failed:")
        for error in errors:
            print(f"  - {error}")
        return
    
    # Analyze strategy
    print("\nAnalyzing strategy...")
    analysis = engine.analyze_strategy(strategy)
    
    print(f"  Strategy ID: {analysis['strategy_id']}")
    print(f"  Net Premium: ${analysis['net_premium']}")
    print(f"  Risk/Reward: {analysis['risk_reward_ratio']}")
    print(f"  Greeks: {analysis['Greeks']}")
    
    # Risk assessment
    print("\nPerforming risk assessment...")
    assessment = risk_manager.assess_strategy(strategy)
    
    print(f"  Approved: {assessment.approved}")
    print(f"  Risk Score: {assessment.risk_score:.1f}/100")
    print(f"  Max Loss: ${assessment.max_loss}")
    print(f"  Position Exposure: ${assessment.position_exposure}")
    print(f"  Portfolio Exposure: ${assessment.portfolio_exposure}")
    
    if assessment.warnings:
        print(f"  Warnings:")
        for warning in assessment.warnings:
            print(f"    - {warning}")
    
    if assessment.violations:
        print(f"  Violations:")
        for violation in assessment.violations:
            print(f"    - {violation}")
    
    # Use bot to stage the strategy
    print("\nStaging strategy with EMO Bot...")
    bot = EMOOptionsBot()
    
    from emo_options_bot.orders.order_stager import OrderStager
    stager = OrderStager()
    strategy_id = stager.stage_strategy(strategy, assessment)
    
    print(f"✓ Strategy staged: {strategy_id}")
    
    # Get staged strategies
    staged = stager.get_staged_strategies()
    print(f"\nTotal staged strategies: {len(staged)}")


if __name__ == "__main__":
    main()
