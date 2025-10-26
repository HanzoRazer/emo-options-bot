"""
Planner - Orchestrates Intent → Strategy Plan → Validation Pipeline
Main orchestrator for AI trading agent workflow.
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import json
from pathlib import Path

from .strategy_translator import StrategyTranslator
from .validator import TradingPlanValidator
from ..logic.risk_manager import PortfolioSnapshot

class TradingPlanner:
    """Orchestrates the complete planning workflow."""
    
    def __init__(self, data_dir: Path = None):
        """
        Initialize the trading planner.
        
        Args:
            data_dir: Directory for saving plans and artifacts
        """
        self.translator = StrategyTranslator()
        self.validator = TradingPlanValidator()
        self.data_dir = data_dir or Path("data/plans")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def build_and_validate(
        self, 
        intent: Dict[str, Any], 
        market_ctx: Dict[str, Any], 
        portfolio: Optional[PortfolioSnapshot] = None
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Complete workflow: Intent → Plan → Validation.
        
        Args:
            intent: Structured trading intent from NLU
            market_ctx: Current market conditions
            portfolio: Current portfolio for validation
            
        Returns:
            Tuple of (plan, validation_errors)
        """
        print(f"[Planner] Building plan for: {intent.get('user_goal', 'unknown goal')}")
        
        # Build strategy plan
        plan = self.translator.to_strategy_plan(intent, market_ctx)
        
        # Validate the plan
        errors = self.validator.validate_plan(plan, portfolio)
        
        # Update plan status based on validation
        if errors:
            plan["status"] = "rejected"
            plan["rejection_reasons"] = errors
            print(f"[Planner] Plan rejected: {len(errors)} validation errors")
        else:
            plan["status"] = "proposed"
            print(f"[Planner] Plan approved for review: {plan['strategy']} on {plan['symbol']}")
        
        # Save plan for audit trail
        self._save_plan(plan)
        
        return plan, errors
    
    def _save_plan(self, plan: Dict[str, Any]) -> Path:
        """Save plan to disk for audit trail."""
        try:
            # Create filename with timestamp and request ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            request_id = plan.get("request_id", "unknown")[:8]
            filename = f"plan_{timestamp}_{request_id}.json"
            
            plan_file = self.data_dir / filename
            
            # Add save metadata
            plan_with_meta = plan.copy()
            plan_with_meta["_saved_at"] = datetime.now().isoformat()
            plan_with_meta["_file_path"] = str(plan_file)
            
            # Save to file
            with open(plan_file, "w") as f:
                json.dump(plan_with_meta, f, indent=2)
            
            print(f"[Planner] Saved plan to: {plan_file}")
            return plan_file
            
        except Exception as e:
            print(f"[Planner] Error saving plan: {e}")
            return None
    
    def load_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Load a previously saved plan by ID."""
        try:
            # Find plan file by ID
            for plan_file in self.data_dir.glob("*.json"):
                if plan_id in plan_file.name:
                    with open(plan_file, "r") as f:
                        return json.load(f)
            
            print(f"[Planner] Plan not found: {plan_id}")
            return None
            
        except Exception as e:
            print(f"[Planner] Error loading plan {plan_id}: {e}")
            return None
    
    def get_recent_plans(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent plans for dashboard/review."""
        try:
            plans = []
            
            # Get all plan files sorted by modification time
            plan_files = sorted(
                self.data_dir.glob("*.json"),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            
            # Load the most recent plans
            for plan_file in plan_files[:limit]:
                try:
                    with open(plan_file, "r") as f:
                        plan = json.load(f)
                        plans.append(plan)
                except Exception as e:
                    print(f"[Planner] Error loading {plan_file}: {e}")
            
            return plans
            
        except Exception as e:
            print(f"[Planner] Error getting recent plans: {e}")
            return []
    
    def create_market_context(self, symbol: str = "SPY") -> Dict[str, Any]:
        """Create market context for planning (mock implementation)."""
        
        # In a real implementation, this would fetch live market data
        mock_contexts = {
            "SPY": {
                "current_price": 450.0,
                "iv_regime": "moderate",
                "iv_rank": 35.0,
                "trend": "neutral",
                "upcoming_event": False,
                "earnings_date": None,
                "portfolio_value": 100000,
                "next_monthly_expiry": "2025-11-15"
            },
            "QQQ": {
                "current_price": 380.0,
                "iv_regime": "moderate",
                "iv_rank": 32.0,
                "trend": "bullish",
                "upcoming_event": False,
                "earnings_date": None,
                "portfolio_value": 100000,
                "next_monthly_expiry": "2025-11-15"
            },
            "AAPL": {
                "current_price": 175.0,
                "iv_regime": "high",
                "iv_rank": 45.0,
                "trend": "neutral",
                "upcoming_event": True,
                "earnings_date": "2025-11-01",
                "portfolio_value": 100000,
                "next_monthly_expiry": "2025-11-15"
            }
        }
        
        return mock_contexts.get(symbol, mock_contexts["SPY"])
    
    def explain_plan(self, plan: Dict[str, Any]) -> str:
        """Generate human-readable explanation of the plan."""
        
        try:
            symbol = plan.get("symbol", "UNKNOWN")
            strategy = plan.get("strategy", "unknown")
            expiry = plan.get("expiry", "unknown")
            status = plan.get("status", "unknown")
            
            # Basic description
            description = f"Proposed {strategy.replace('_', ' ').title()} strategy on {symbol} expiring {expiry}."
            
            # Add risk information
            sizing = plan.get("sizing", {})
            max_risk = sizing.get("max_risk_per_trade", 0)
            contracts = sizing.get("contracts", 0)
            
            if max_risk > 0:
                description += f" Maximum risk: {max_risk:.1%} of portfolio"
            
            if contracts > 0:
                description += f" using {contracts} contract{'s' if contracts > 1 else ''}."
            
            # Add probability of profit
            pop = plan.get("probability_of_profit", 0)
            if pop > 0:
                description += f" Estimated probability of profit: {pop:.0%}."
            
            # Add status context
            if status == "rejected":
                reasons = plan.get("rejection_reasons", [])
                if reasons:
                    description += f" REJECTED due to: {'; '.join(reasons[:2])}."
            elif status == "proposed":
                description += " Ready for approval."
            
            return description
            
        except Exception as e:
            return f"Error explaining plan: {e}"
    
    def get_plan_summary(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of plan key details for UI display."""
        
        return {
            "request_id": plan.get("request_id"),
            "symbol": plan.get("symbol"),
            "strategy": plan.get("strategy", "").replace("_", " ").title(),
            "expiry": plan.get("expiry"),
            "status": plan.get("status"),
            "max_risk": plan.get("sizing", {}).get("max_risk_per_trade", 0),
            "contracts": plan.get("sizing", {}).get("contracts", 0),
            "probability_of_profit": plan.get("probability_of_profit", 0),
            "legs": len(plan.get("legs", [])),
            "created_at": plan.get("created_at"),
            "explanation": self.explain_plan(plan),
            "has_errors": plan.get("status") == "rejected",
            "error_count": len(plan.get("rejection_reasons", []))
        }


# Convenience functions for backward compatibility
def build_and_validate(
    intent: Dict[str, Any], 
    market_ctx: Dict[str, Any], 
    portfolio: Optional[PortfolioSnapshot] = None
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Build and validate a trading plan from intent.
    
    Args:
        intent: Trading intent from NLU
        market_ctx: Market conditions
        portfolio: Current portfolio
        
    Returns:
        Tuple of (plan, errors)
    """
    planner = TradingPlanner()
    return planner.build_and_validate(intent, market_ctx, portfolio)