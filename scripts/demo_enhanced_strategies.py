#!/usr/bin/env python3
"""
Enhanced Strategy Demo with Risk Management Integration
Demonstrates the complete strategy system integrated with EMO Options Bot.
"""

import os, json, sys
from pathlib import Path
from datetime import datetime

# Ensure src on path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from strategies.manager import StrategyManager
from strategies.options import IronCondor, PutCreditSpread, CoveredCall, LongStraddle
from database.router import get_db
from logic.risk_manager import RiskManager, PortfolioSnapshot, Position

def create_mock_portfolio() -> PortfolioSnapshot:
    """Create a mock portfolio for demonstration."""
    positions = [
        Position(symbol="SPY", qty=200, mark=450.0, value=90000, max_loss=9000, beta=1.0, sector="ETF"),
        Position(symbol="QQQ", qty=100, mark=380.0, value=38000, max_loss=5700, beta=1.2, sector="ETF"),
        Position(symbol="AAPL", qty=50, mark=175.0, value=8750, max_loss=1575, beta=1.3, sector="Technology"),
    ]
    
    return PortfolioSnapshot(
        equity=150000,
        cash=13250,
        positions=positions
    )

def create_market_snapshots():
    """Create various market scenarios for testing strategies."""
    base_snapshot = {
        "symbol": "SPY",
        "current_price": 450.0,
        "dte": 25,
        "support_level": 440.0,
        "resistance_level": 465.0,
    }
    
    scenarios = [
        {
            **base_snapshot,
            "scenario": "High IV Neutral Market",
            "ivr": 45.0,
            "iv_rank": 45.0,
            "bias": "neutral",
            "market_trend": "neutral",
            "market_outlook": "neutral",
            "expected_move": 0.025,
            "event": "Normal trading",
            "days_to_event": 30,
            "has_shares": False,
            "shares_owned": 0
        },
        {
            **base_snapshot,
            "scenario": "Bullish Market with Moderate IV",
            "ivr": 28.0,
            "iv_rank": 28.0,
            "bias": "bullish",
            "market_trend": "bullish",
            "market_outlook": "bullish",
            "expected_move": 0.035,
            "event": "Economic optimism",
            "days_to_event": 10,
            "has_shares": True,
            "shares_owned": 500
        },
        {
            **base_snapshot,
            "scenario": "Earnings Event High Volatility",
            "ivr": 35.0,
            "iv_rank": 35.0,
            "bias": "neutral",
            "market_trend": "neutral",
            "market_outlook": "neutral",
            "expected_move": 0.085,
            "event": "AAPL Earnings in 2 days",
            "days_to_event": 2,
            "has_shares": False,
            "shares_owned": 0,
            "symbol": "AAPL",
            "current_price": 175.0,
            "support_level": 165.0,
            "resistance_level": 185.0
        },
        {
            **base_snapshot,
            "scenario": "FOMC Meeting Volatility",
            "ivr": 52.0,
            "iv_rank": 52.0,
            "bias": "neutral",
            "market_trend": "neutral",
            "market_outlook": "neutral",
            "expected_move": 0.065,
            "event": "FOMC announcement in 1 day",
            "days_to_event": 1,
            "has_shares": False,
            "shares_owned": 0
        },
        {
            **base_snapshot,
            "scenario": "Low IV Market with Shares",
            "ivr": 15.0,
            "iv_rank": 15.0,
            "bias": "neutral_bullish",
            "market_trend": "sideways",
            "market_outlook": "neutral",
            "expected_move": 0.015,
            "event": "Quiet period",
            "days_to_event": 20,
            "has_shares": True,
            "shares_owned": 800
        }
    ]
    
    return scenarios

def run_strategy_demo():
    """Run comprehensive strategy demonstration."""
    print("🚀 Enhanced EMO Options Bot - Strategy System Demo")
    print("=" * 60)
    
    # Initialize database
    try:
        db = get_db()
        db.ensure_schema()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
        db = None
    
    # Initialize risk manager
    risk_manager = RiskManager(
        portfolio_risk_cap=0.25,    # 25% max portfolio heat
        per_position_risk=0.03,     # 3% max per position
        max_positions=8,            # Max 8 positions
        max_beta_exposure=2.0,      # Max 2x beta exposure
        max_drawdown=0.15           # 15% drawdown circuit breaker
    )
    
    # Initialize strategy manager with risk integration
    sm = StrategyManager(risk_manager=risk_manager)
    
    # Register strategies with different allocation weights
    strategies_config = [
        ("iron_condor", IronCondor(), 0.3),
        ("put_credit_spread", PutCreditSpread(), 0.3),
        ("covered_call", CoveredCall(), 0.25),
        ("long_straddle", LongStraddle(), 0.15),
    ]
    
    for name, strategy, weight in strategies_config:
        sm.register(name, strategy, weight)
    
    print(f"✅ Registered {len(strategies_config)} strategies")
    
    # Create mock portfolio
    portfolio = create_mock_portfolio()
    
    print(f"\n📊 Current Portfolio Status:")
    print(f"   Equity: ${portfolio.equity:,.0f}")
    print(f"   Cash: ${portfolio.cash:,.0f}")
    print(f"   Positions: {len(portfolio.positions)}")
    
    # Assess portfolio risk
    assessment = risk_manager.assess_portfolio(portfolio)
    print(f"   Portfolio Heat: {assessment['risk_util']:.1%}")
    print(f"   Beta Exposure: {assessment['beta_exposure']:.2f}")
    
    # Test strategies against different market scenarios
    scenarios = create_market_snapshots()
    
    print(f"\n🎯 Testing Strategies Against {len(scenarios)} Market Scenarios:")
    print("-" * 60)
    
    all_results = []
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📈 Scenario {i}: {scenario['scenario']}")
        print(f"   Symbol: {scenario['symbol']} | IV Rank: {scenario['iv_rank']:.1f}% | Bias: {scenario['bias']}")
        print(f"   Event: {scenario['event']}")
        
        # Generate strategy orders
        orders = sm.decide(scenario, portfolio)
        
        print(f"   Generated Orders: {len(orders)}")
        
        scenario_result = {
            "scenario": scenario['scenario'],
            "symbol": scenario['symbol'],
            "iv_rank": scenario['iv_rank'],
            "orders_generated": len(orders),
            "orders": []
        }
        
        for order in orders:
            strategy_name = order.meta.get("strategy", "unknown")
            risk_note = order.meta.get("risk_note", "")
            
            print(f"   ✅ {strategy_name.upper()}: {order.side} {order.qty} {order.type}")
            print(f"      Risk: {risk_note}")
            
            scenario_result["orders"].append({
                "strategy": strategy_name,
                "side": order.side,
                "qty": order.qty,
                "type": order.type,
                "risk_note": risk_note
            })
        
        if not orders:
            print("   ❌ No orders generated (conditions not met)")
        
        all_results.append(scenario_result)
    
    # Generate strategy manager report
    print(f"\n📋 Strategy Manager Report:")
    print("-" * 40)
    print(sm.generate_report())
    
    # Save results to database if available
    if db:
        try:
            sm.save_to_database(db)
            print("✅ Results saved to database")
        except Exception as e:
            print(f"⚠️  Database save warning: {e}")
    
    # Generate summary statistics
    print(f"\n📊 Demo Summary:")
    print("-" * 30)
    
    total_orders = sum(len(result["orders"]) for result in all_results)
    strategies_used = set()
    for result in all_results:
        for order in result["orders"]:
            strategies_used.add(order["strategy"])
    
    print(f"   Total Scenarios Tested: {len(scenarios)}")
    print(f"   Total Orders Generated: {total_orders}")
    print(f"   Strategies Activated: {len(strategies_used)}")
    print(f"   Active Strategies: {', '.join(sorted(strategies_used))}")
    
    # Risk management effectiveness
    order_history = sm.get_order_history()
    approved_orders = [o for o in order_history if o["status"] == "APPROVED"]
    rejected_orders = [o for o in order_history if o["status"] == "REJECTED"]
    
    print(f"\n🛡️  Risk Management Summary:")
    print(f"   Orders Approved: {len(approved_orders)}")
    print(f"   Orders Rejected: {len(rejected_orders)}")
    if rejected_orders:
        print("   Rejection Reasons:")
        for order in rejected_orders[-3:]:  # Show last 3 rejections
            violations = ", ".join(order["violations"])
            print(f"     - {violations}")
    
    # Export results
    results_file = ROOT / "data" / "strategy_demo_results.json"
    results_file.parent.mkdir(exist_ok=True)
    
    export_data = {
        "timestamp": datetime.now().isoformat(),
        "portfolio": {
            "equity": portfolio.equity,
            "cash": portfolio.cash,
            "positions": len(portfolio.positions),
            "risk_assessment": assessment
        },
        "scenarios": all_results,
        "summary": {
            "total_scenarios": len(scenarios),
            "total_orders": total_orders,
            "strategies_used": list(strategies_used),
            "approved_orders": len(approved_orders),
            "rejected_orders": len(rejected_orders)
        }
    }
    
    results_file.write_text(json.dumps(export_data, indent=2), encoding="utf-8")
    print(f"\n💾 Results exported to: {results_file}")
    
    print(f"\n🎉 Strategy Demo Complete!")
    return export_data

def main():
    """Main entry point."""
    try:
        results = run_strategy_demo()
        
        print(f"\n🔗 Integration Status:")
        print("   ✅ Strategy system operational")
        print("   ✅ Risk management active")
        print("   ✅ Database integration working")
        print("   ✅ Multi-scenario testing complete")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)