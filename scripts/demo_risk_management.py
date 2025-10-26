#!/usr/bin/env python3
"""
EMO Options Bot - Risk Management Demo
Demonstrates the professional risk management system in action
"""

import sys
import os
import time
from pathlib import Path

# Add src to Python path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

def risk_management_demo():
    """Comprehensive demonstration of risk management features"""
    
    from src.logic import RiskManager, PortfolioSnapshot, Position, OrderIntent
    from src.logic import equity_size_by_vol, credit_spread_contracts, correlation_scale
    from src.database.router import get_db, ensure_minimum_schema
    
    print("🛡️ EMO Options Bot - Professional Risk Management Demo")
    print("=" * 60)
    
    # Initialize risk manager with custom settings
    print("\n📋 Initializing Risk Manager...")
    risk_manager = RiskManager(
        portfolio_risk_cap=0.15,    # 15% max portfolio heat
        per_position_risk=0.025,    # 2.5% max per position  
        max_positions=8,            # Max 8 concurrent positions
        max_correlation=0.80,       # 80% correlation limit
        max_beta_exposure=2.0,      # 2x beta exposure limit
        max_drawdown=0.10,          # 10% drawdown circuit breaker
        min_equity=50_000.0         # $50k minimum equity
    )
    
    print(f"   ✅ Portfolio Risk Cap: 15%")
    print(f"   ✅ Per-Position Risk: 2.5%")
    print(f"   ✅ Max Positions: 8")
    print(f"   ✅ Max Drawdown: 10%")
    
    # Setup database
    print("\n🗄️ Initializing Database...")
    db = get_db()
    ensure_minimum_schema(db)
    
    # Simulate equity tracking
    print("\n📈 Tracking Equity Performance...")
    initial_equity = 100_000
    risk_manager.record_equity(initial_equity)
    
    # Simulate some market volatility
    equity_curve = [100_000, 102_000, 98_500, 103_200, 97_800, 105_000]
    for i, equity in enumerate(equity_curve):
        risk_manager.record_equity(equity, time.time() + i * 86400)
        
    current_drawdown = risk_manager.current_drawdown()
    print(f"   ✅ Current Equity: ${equity_curve[-1]:,.0f}")
    print(f"   ✅ Current Drawdown: {current_drawdown:.1%}")
    print(f"   ✅ Drawdown Breached: {risk_manager.drawdown_breached()}")
    
    # Build test portfolio
    print("\n💼 Building Test Portfolio...")
    portfolio = PortfolioSnapshot(
        equity=105_000,
        cash=45_000,
        positions=[
            Position(symbol="SPY", qty=50, mark=580, value=29_000, max_loss=1_450, beta=1.0, sector="Broad Market"),
            Position(symbol="QQQ", qty=30, mark=495, value=14_850, max_loss=950, beta=1.2, sector="Technology"),
            Position(symbol="IWM", qty=100, mark=220, value=22_000, max_loss=1_200, beta=1.1, sector="Small Cap"),
        ]
    )
    
    for pos in portfolio.positions:
        print(f"   📊 {pos.symbol}: {pos.qty} shares @ ${pos.mark:.2f}, "
              f"Risk: ${pos.max_loss:,.0f}, Beta: {pos.beta}")
    
    # Assess current portfolio
    print("\n🔍 Portfolio Risk Assessment...")
    assessment = risk_manager.assess_portfolio(portfolio)
    
    print(f"   💰 Equity: ${assessment['equity']:,.0f}")
    print(f"   🏦 Cash: ${portfolio.cash:,.0f}")
    print(f"   📈 Positions: {assessment['positions']}")
    print(f"   🔥 Risk Used: ${assessment['risk_used']:,.0f}")
    print(f"   🎯 Risk Cap: ${assessment['risk_cap']:,.0f}")
    print(f"   📊 Risk Utilization: {assessment['risk_util']:.1%}")
    print(f"   🔢 Beta Exposure: {assessment['beta_exposure']:.2f}")
    print(f"   📉 Drawdown: {assessment['drawdown']:.1%}")
    
    # Test position sizing
    print("\n📏 Position Sizing Examples...")
    
    # Example 1: Equity position sizing
    spy_prices = [580 + i*0.5 for i in range(30)]  # Simulate 30 days of prices
    spy_size = equity_size_by_vol(
        spy_prices, 
        equity=105_000, 
        per_position_risk=0.02
    )
    print(f"   📊 SPY Position Size (volatility-based): {spy_size} shares")
    
    # Example 2: Options spread sizing
    spread_size = credit_spread_contracts(
        credit_per_contract=2.50,
        width=10,
        equity=105_000,
        per_position_risk=0.02
    )
    print(f"   📊 Credit Spread Size: {spread_size} contracts")
    
    # Example 3: Correlation adjustment
    base_size = 200
    corr_adjusted = correlation_scale(base_size, avg_corr_to_book=0.85)
    print(f"   📊 Correlation Adjusted Size: {corr_adjusted} (from {base_size})")
    
    # Test order validation scenarios
    print("\n🎯 Order Validation Tests...")
    
    # Test 1: Valid order
    order1 = OrderIntent(
        symbol="AAPL",
        side="open",
        est_max_loss=1_800,
        est_value=25_000,
        correlation_hint=0.65,
        beta=1.3
    )
    
    ok1, reasons1 = risk_manager.validate_order(order1, portfolio)
    status1 = "✅ APPROVED" if ok1 else "❌ REJECTED"
    print(f"   {status1} AAPL Order: Risk ${order1.est_max_loss:,.0f}")
    if reasons1:
        for reason in reasons1:
            print(f"     • {reason}")
    
    # Test 2: High risk order (should fail)
    order2 = OrderIntent(
        symbol="TSLA",
        side="open",
        est_max_loss=3_500,  # Too much risk
        est_value=40_000,
        correlation_hint=0.90,  # Too correlated
        beta=2.5
    )
    
    ok2, reasons2 = risk_manager.validate_order(order2, portfolio)
    status2 = "✅ APPROVED" if ok2 else "❌ REJECTED"
    print(f"   {status2} TSLA Order: Risk ${order2.est_max_loss:,.0f}")
    if reasons2:
        for reason in reasons2:
            print(f"     • {reason}")
    
    # Test 3: High correlation order
    order3 = OrderIntent(
        symbol="VTI",
        side="open",
        est_max_loss=1_200,
        est_value=20_000,
        correlation_hint=0.95,  # Very high correlation to SPY
        beta=1.0
    )
    
    ok3, reasons3 = risk_manager.validate_order(order3, portfolio)
    status3 = "✅ APPROVED" if ok3 else "❌ REJECTED"
    print(f"   {status3} VTI Order: Risk ${order3.est_max_loss:,.0f}")
    if reasons3:
        for reason in reasons3:
            print(f"     • {reason}")
    
    # Store risk metrics in database
    print("\n💾 Storing Risk Metrics...")
    db.execute("""
    INSERT OR REPLACE INTO risk_metrics(
        ts, equity, positions_count, risk_used, risk_cap, 
        risk_util, beta_exposure, drawdown
    ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "2025-10-25T01:00:00Z",
        assessment['equity'],
        assessment['positions'],
        assessment['risk_used'],
        assessment['risk_cap'],
        assessment['risk_util'],
        assessment['beta_exposure'],
        assessment['drawdown']
    ))
    
    # Store position history
    for pos in portfolio.positions:
        db.execute("""
        INSERT OR REPLACE INTO position_history(
            ts, symbol, qty, mark, value, max_loss, beta, sector
        ) VALUES(?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "2025-10-25T01:00:00Z",
            pos.symbol,
            pos.qty,
            pos.mark,
            pos.value,
            pos.max_loss,
            pos.beta,
            pos.sector
        ))
    
    print("   ✅ Risk metrics stored")
    print("   ✅ Position history stored")
    
    # Query and display historical data
    print("\n📋 Historical Risk Data...")
    risk_history = db.query("SELECT ts, equity, risk_util, drawdown FROM risk_metrics ORDER BY ts DESC LIMIT 5")
    for row in risk_history:
        ts, equity, risk_util, drawdown = row
        print(f"   📅 {ts}: Equity ${equity:,.0f}, Risk {risk_util:.1%}, DD {drawdown:.1%}")
    
    db.close()
    
    print("\n" + "=" * 60)
    print("🎉 Risk Management Demo Complete!")
    print("🛡️ Professional risk controls are operational and ready for production")
    print("📊 Portfolio monitoring and position sizing systems active")
    print("🗄️ Risk metrics and position history being tracked in database")

if __name__ == "__main__":
    risk_management_demo()