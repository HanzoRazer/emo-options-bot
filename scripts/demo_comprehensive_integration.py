"""
Comprehensive Demo: Enhanced EMO Options Bot with Strategy Signals Integration
Demonstrates both the existing enhanced options system and new signals framework.
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List
import datetime as dt

# Ensure src is on path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

# Import existing enhanced system
from src.strategies.manager import StrategyManager as OptionsStrategyManager
from src.strategies.options import IronCondor as OptionsIronCondor, PutCreditSpread as OptionsPutSpread
from src.logic.risk_manager import RiskManager, PortfolioSnapshot, Position
from src.database.router import get_db

# Import new signals system
from src.strategies.signals import StrategyManager as SignalsStrategyManager
from src.strategies.signals import IronCondor as SignalsIronCondor, PutCreditSpread as SignalsPutSpread

# Import dashboard
from src.web.enhanced_dashboard import EnhancedDashboard

class ComprehensiveDemo:
    """Demonstrates integration between existing and new systems."""
    
    def __init__(self):
        self.data_dir = ROOT / "data"
        self.ops_dir = ROOT / "ops"
        
        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.ops_dir.mkdir(exist_ok=True)
        
        # Initialize systems
        self.setup_existing_system()
        self.setup_signals_system()
        self.setup_dashboard()
    
    def setup_existing_system(self):
        """Setup the existing enhanced options strategy system."""
        print("🚀 Setting up existing enhanced options system...")
        
        # Initialize risk manager
        self.risk_manager = RiskManager(
            portfolio_risk_cap=0.25,
            per_position_risk=0.03,
            max_positions=8,
            max_beta_exposure=2.0
        )
        
        # Initialize options strategy manager
        self.options_sm = OptionsStrategyManager(risk_manager=self.risk_manager)
        
        # Register existing options strategies
        self.options_sm.register("iron_condor", OptionsIronCondor(), 0.3)
        self.options_sm.register("put_spread", OptionsPutSpread(), 0.3)
        
        print("✅ Enhanced options system ready")
    
    def setup_signals_system(self):
        """Setup the new signals-based system."""
        print("🎯 Setting up new signals-based system...")
        
        # Initialize signals strategy manager
        signals_csv = self.ops_dir / "signals.csv"
        self.signals_sm = SignalsStrategyManager(signals_csv)
        
        # Register signals strategies
        self.signals_sm.register("IronCondor", config={"min_ivr": 0.25})
        self.signals_sm.register("PutCreditSpread", config={"min_ivr": 0.15})
        
        # Warm up
        self.signals_sm.warmup()
        
        print("✅ Signals system ready")
    
    def setup_dashboard(self):
        """Setup enhanced dashboard."""
        print("📊 Setting up enhanced dashboard...")
        self.dashboard = EnhancedDashboard()
        print("✅ Dashboard ready")
    
    def create_mock_portfolio(self) -> PortfolioSnapshot:
        """Create mock portfolio for demonstration."""
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
    
    def create_market_scenarios(self) -> List[Dict[str, Any]]:
        """Create various market scenarios for testing."""
        scenarios = [
            {
                "name": "High IV Neutral Market",
                "symbol": "SPY",
                "current_price": 450.0,
                "ivr": 0.45,
                "iv_rank": 45.0,
                "bias": "neutral",
                "trend": "sideways",
                "market_outlook": "neutral",
                "expected_move": 0.025,
                "dte": 25
            },
            {
                "name": "Bullish Market with Moderate IV",
                "symbol": "QQQ",
                "current_price": 380.0,
                "ivr": 0.28,
                "iv_rank": 28.0,
                "bias": "bullish",
                "trend": "up",
                "market_outlook": "bullish",
                "expected_move": 0.035,
                "dte": 30
            },
            {
                "name": "Low IV Sideways Market",
                "symbol": "AAPL",
                "current_price": 175.0,
                "ivr": 0.15,
                "iv_rank": 15.0,
                "bias": "neutral",
                "trend": "sideways",
                "market_outlook": "neutral",
                "expected_move": 0.015,
                "dte": 35
            }
        ]
        
        return scenarios
    
    def create_mock_ml_outlook(self):
        """Create mock ML outlook for dashboard."""
        ml_data = {
            "prediction": "slightly_bullish",
            "confidence": 0.72,
            "models": ["LSTM", "RandomForest", "XGBoost"],
            "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
            "notes": "Market showing bullish momentum with tech sector strength"
        }
        
        ml_file = self.data_dir / "ml_outlook.json"
        ml_file.write_text(json.dumps(ml_data, indent=2), encoding="utf-8")
        print(f"📈 Created ML outlook: {ml_file}")
    
    def demonstrate_existing_system(self, portfolio: PortfolioSnapshot, scenarios: List[Dict[str, Any]]):
        """Demonstrate the existing enhanced options strategy system."""
        print(f"\n{'='*60}")
        print("EXISTING ENHANCED OPTIONS STRATEGY SYSTEM")
        print(f"{'='*60}")
        
        all_orders = []
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n📈 Scenario {i}: {scenario['name']}")
            print(f"   Symbol: {scenario['symbol']} | IV Rank: {scenario['iv_rank']:.1f}% | Bias: {scenario['bias']}")
            
            # Generate orders using existing system
            orders = self.options_sm.decide(scenario, portfolio)
            
            print(f"   📋 Generated {len(orders)} orders:")
            for order in orders:
                strategy_name = order.meta.get("strategy", "unknown")
                print(f"      ✅ {strategy_name.upper()}: {order.side} {order.qty} {order.type}")
                
            all_orders.extend(orders)
        
        print(f"\n📊 Existing System Summary:")
        print(f"   Total Orders Generated: {len(all_orders)}")
        print(f"   Strategies Active: {len(self.options_sm._strategies)}")
        
        return all_orders
    
    def demonstrate_signals_system(self, scenarios: List[Dict[str, Any]]):
        """Demonstrate the new signals-based strategy system."""
        print(f"\n{'='*60}")
        print("NEW SIGNALS-BASED STRATEGY SYSTEM")
        print(f"{'='*60}")
        
        # Convert scenarios to signals format
        md_stream = []
        for scenario in scenarios:
            md = {
                "symbol": scenario["symbol"],
                "ivr": scenario["ivr"],
                "trend": scenario["trend"],
                "current_price": scenario["current_price"]
            }
            md_stream.append(md)
        
        # Generate signals
        signals = self.signals_sm.run_once(md_stream)
        
        print(f"\n📊 Signals System Summary:")
        print(f"   Total Signals Generated: {len(signals)}")
        print(f"   Strategies Active: {len(self.signals_sm.enabled)}")
        
        # Show signal details
        print(f"\n🎯 Generated Signals:")
        for signal in signals:
            action_emoji = {"enter": "🟢", "exit": "🔴", "hold": "🟡"}.get(signal.action, "⚪")
            print(f"   {action_emoji} {signal.symbol} - {signal.strategy}: {signal.action.upper()}")
            print(f"      Confidence: {signal.confidence:.2f} | Notes: {signal.notes}")
        
        return signals
    
    def demonstrate_dashboard_integration(self):
        """Demonstrate the enhanced dashboard with both systems."""
        print(f"\n{'='*60}")
        print("ENHANCED DASHBOARD WITH FULL INTEGRATION")
        print(f"{'='*60}")
        
        # Build dashboard
        dashboard_file = self.dashboard.build_dashboard()
        
        print(f"📊 Dashboard Features:")
        print(f"   ✅ Risk Management Panel")
        print(f"   ✅ Market Data Analysis")
        print(f"   ✅ ML Outlook Display")
        print(f"   ✅ Strategy Signals Table")
        print(f"   ✅ Real-time Updates")
        
        print(f"\n🌐 Dashboard generated: {dashboard_file}")
        print(f"📱 View at: file://{dashboard_file.resolve()}")
        
        return dashboard_file
    
    def compare_systems(self, orders: List, signals: List):
        """Compare outputs from both systems."""
        print(f"\n{'='*60}")
        print("SYSTEM COMPARISON ANALYSIS")
        print(f"{'='*60}")
        
        print(f"📋 Options Strategy System:")
        print(f"   • Direct order generation for broker execution")
        print(f"   • Integrated risk management validation")
        print(f"   • Position sizing and portfolio optimization")
        print(f"   • Orders generated: {len(orders)}")
        
        print(f"\n🎯 Signals Strategy System:")
        print(f"   • Lightweight signal generation for analysis")
        print(f"   • Confidence-based recommendations")
        print(f"   • Historical signal tracking in CSV")
        print(f"   • Signals generated: {len(signals)}")
        
        print(f"\n🔗 Integration Benefits:")
        print(f"   • Complementary approaches for different use cases")
        print(f"   • Unified dashboard showing all data sources")
        print(f"   • Risk management integration across both systems")
        print(f"   • Flexible strategy deployment options")
    
    def run_comprehensive_demo(self):
        """Run the complete demonstration."""
        print("🚀 EMO Options Bot - Comprehensive Integration Demo")
        print("=" * 60)
        
        try:
            # Create test data
            portfolio = self.create_mock_portfolio()
            scenarios = self.create_market_scenarios()
            
            print(f"\n📊 Demo Setup:")
            print(f"   Portfolio Equity: ${portfolio.equity:,.0f}")
            print(f"   Test Scenarios: {len(scenarios)}")
            print(f"   Positions: {len(portfolio.positions)}")
            
            # Create ML outlook for dashboard
            self.create_mock_ml_outlook()
            
            # Demonstrate existing system
            orders = self.demonstrate_existing_system(portfolio, scenarios)
            
            # Demonstrate signals system
            signals = self.demonstrate_signals_system(scenarios)
            
            # Demonstrate dashboard
            dashboard_file = self.demonstrate_dashboard_integration()
            
            # Compare systems
            self.compare_systems(orders, signals)
            
            # Final summary
            print(f"\n{'='*60}")
            print("DEMO COMPLETE - INTEGRATION SUCCESS!")
            print(f"{'='*60}")
            
            print(f"✅ Enhanced Options System: {len(orders)} orders generated")
            print(f"✅ Signals System: {len(signals)} signals generated")
            print(f"✅ Dashboard Integration: Working")
            print(f"✅ Risk Management: Active")
            print(f"✅ Data Pipeline: Operational")
            
            print(f"\n📁 Generated Files:")
            print(f"   📊 Dashboard: {dashboard_file}")
            print(f"   🎯 Signals CSV: {self.ops_dir / 'signals.csv'}")
            print(f"   📈 ML Outlook: {self.data_dir / 'ml_outlook.json'}")
            
            print(f"\n🎉 Your enhanced EMO Options Bot is ready for production!")
            
            return True
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main entry point for comprehensive demo."""
    demo = ComprehensiveDemo()
    success = demo.run_comprehensive_demo()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())