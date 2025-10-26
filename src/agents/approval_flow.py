"""
Approval Flow - User Review and Approval for Trading Plans
Handles user confirmation, modifications, and execution approval.
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import json

class ApprovalAction(Enum):
    """Actions a user can take on a proposed plan."""
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    REQUEST_CHANGES = "request_changes"
    DEFER = "defer"

@dataclass
class ApprovalRequest:
    """Represents a plan awaiting user approval."""
    plan_id: str
    plan: Dict[str, Any]
    submitted_at: datetime
    user_goal: str
    risk_level: str
    explanation: str
    estimated_return: float
    max_loss: float
    probability_of_profit: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "plan_id": self.plan_id,
            "plan": self.plan,
            "submitted_at": self.submitted_at.isoformat(),
            "user_goal": self.user_goal,
            "risk_level": self.risk_level,
            "explanation": self.explanation,
            "estimated_return": self.estimated_return,
            "max_loss": self.max_loss,
            "probability_of_profit": self.probability_of_profit
        }

@dataclass
class ApprovalResponse:
    """User's response to an approval request."""
    plan_id: str
    action: ApprovalAction
    user_comments: str
    modifications: Optional[Dict[str, Any]] = None
    approved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "plan_id": self.plan_id,
            "action": self.action.value,
            "user_comments": self.user_comments,
            "modifications": self.modifications,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None
        }

class ApprovalFlow:
    """Manages the approval workflow for trading plans."""
    
    def __init__(self, approval_callback: Optional[Callable] = None):
        """
        Initialize approval flow.
        
        Args:
            approval_callback: Optional callback for plan approval events
        """
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.approval_history: List[ApprovalResponse] = []
        self.approval_callback = approval_callback
        
    def submit_for_approval(
        self, 
        plan: Dict[str, Any], 
        user_goal: str,
        explanation: str = ""
    ) -> ApprovalRequest:
        """
        Submit a plan for user approval.
        
        Args:
            plan: The trading plan to approve
            user_goal: Original user goal/intent
            explanation: Human-readable explanation
            
        Returns:
            ApprovalRequest object
        """
        # Generate unique plan ID
        plan_id = plan.get("request_id", f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        # Extract key metrics for approval display
        sizing = plan.get("sizing", {})
        risk_level = plan.get("risk_level", "unknown")
        
        # Create approval request
        approval_request = ApprovalRequest(
            plan_id=plan_id,
            plan=plan,
            submitted_at=datetime.now(),
            user_goal=user_goal,
            risk_level=risk_level,
            explanation=explanation,
            estimated_return=plan.get("estimated_return", 0.0),
            max_loss=sizing.get("max_risk_per_trade", 0.0),
            probability_of_profit=plan.get("probability_of_profit", 0.0)
        )
        
        # Store pending approval
        self.pending_approvals[plan_id] = approval_request
        
        print(f"[Approval] Plan {plan_id} submitted for approval")
        print(f"[Approval] Goal: {user_goal}")
        print(f"[Approval] Risk Level: {risk_level}")
        print(f"[Approval] Max Loss: {sizing.get('max_risk_per_trade', 0):.1%}")
        
        return approval_request
    
    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all plans awaiting approval."""
        return list(self.pending_approvals.values())
    
    def get_approval_request(self, plan_id: str) -> Optional[ApprovalRequest]:
        """Get specific approval request by plan ID."""
        return self.pending_approvals.get(plan_id)
    
    def process_approval(
        self, 
        plan_id: str, 
        action: ApprovalAction,
        user_comments: str = "",
        modifications: Optional[Dict[str, Any]] = None
    ) -> ApprovalResponse:
        """
        Process user's approval decision.
        
        Args:
            plan_id: Plan to respond to
            action: User's decision
            user_comments: User's feedback/comments
            modifications: Any requested changes
            
        Returns:
            ApprovalResponse object
        """
        if plan_id not in self.pending_approvals:
            raise ValueError(f"No pending approval for plan {plan_id}")
        
        # Create response
        response = ApprovalResponse(
            plan_id=plan_id,
            action=action,
            user_comments=user_comments,
            modifications=modifications,
            approved_at=datetime.now() if action == ApprovalAction.APPROVE else None
        )
        
        # Remove from pending if approved/rejected
        if action in [ApprovalAction.APPROVE, ApprovalAction.REJECT]:
            del self.pending_approvals[plan_id]
        
        # Store in history
        self.approval_history.append(response)
        
        # Execute callback if provided
        if self.approval_callback:
            try:
                self.approval_callback(response)
            except Exception as e:
                print(f"[Approval] Callback error: {e}")
        
        print(f"[Approval] Plan {plan_id} {action.value}: {user_comments}")
        
        return response
    
    def get_approval_summary(self, plan_id: str) -> Dict[str, Any]:
        """Get a summary for UI display."""
        request = self.get_approval_request(plan_id)
        if not request:
            return {"error": "Plan not found"}
        
        plan = request.plan
        
        return {
            "plan_id": plan_id,
            "status": "pending_approval",
            "submitted_at": request.submitted_at.isoformat(),
            "user_goal": request.user_goal,
            "strategy": plan.get("strategy", "").replace("_", " ").title(),
            "symbol": plan.get("symbol"),
            "expiry": plan.get("expiry"),
            "risk_level": request.risk_level,
            "max_loss_pct": request.max_loss,
            "estimated_return": request.estimated_return,
            "probability_of_profit": request.probability_of_profit,
            "explanation": request.explanation,
            "legs": len(plan.get("legs", [])),
            "contracts": plan.get("sizing", {}).get("contracts", 0),
            "requires_approval": True,
            "can_modify": True,
            "can_reject": True
        }
    
    def create_approval_ui_data(self, plan_id: str) -> Dict[str, Any]:
        """Create data structure for approval UI."""
        request = self.get_approval_request(plan_id)
        if not request:
            return {"error": "Plan not found"}
        
        plan = request.plan
        legs = plan.get("legs", [])
        
        # Create leg summaries for display
        leg_summaries = []
        for i, leg in enumerate(legs):
            leg_summaries.append({
                "leg_number": i + 1,
                "action": leg.get("action"),
                "option_type": leg.get("option_type"),
                "strike": leg.get("strike"),
                "expiry": leg.get("expiry"),
                "quantity": leg.get("quantity", 0),
                "side": "Buy" if leg.get("quantity", 0) > 0 else "Sell"
            })
        
        return {
            "approval_request": {
                "plan_id": plan_id,
                "user_goal": request.user_goal,
                "explanation": request.explanation,
                "submitted_at": request.submitted_at.isoformat()
            },
            "strategy_details": {
                "strategy": plan.get("strategy", "").replace("_", " ").title(),
                "symbol": plan.get("symbol"),
                "expiry": plan.get("expiry"),
                "legs": leg_summaries,
                "total_legs": len(legs)
            },
            "risk_metrics": {
                "risk_level": request.risk_level,
                "max_loss_pct": f"{request.max_loss:.1%}",
                "estimated_return": f"{request.estimated_return:.1%}",
                "probability_of_profit": f"{request.probability_of_profit:.0%}",
                "contracts": plan.get("sizing", {}).get("contracts", 0),
                "max_risk_dollars": plan.get("sizing", {}).get("max_risk_amount", 0)
            },
            "actions": [
                {"action": "approve", "label": "Approve & Execute", "style": "success"},
                {"action": "modify", "label": "Request Changes", "style": "warning"},
                {"action": "reject", "label": "Reject", "style": "danger"},
                {"action": "defer", "label": "Review Later", "style": "secondary"}
            ]
        }
    
    def auto_approve_if_criteria_met(self, plan_id: str) -> bool:
        """
        Check if plan meets auto-approval criteria.
        
        Returns:
            True if auto-approved, False if manual approval needed
        """
        request = self.get_approval_request(plan_id)
        if not request:
            return False
        
        plan = request.plan
        
        # Auto-approval criteria (very conservative)
        auto_approve_conditions = [
            request.risk_level == "low",
            request.max_loss <= 0.01,  # Max 1% portfolio risk
            plan.get("strategy") in ["covered_call", "put_credit_spread"],  # Safe strategies
            request.probability_of_profit >= 0.70,  # High probability
            plan.get("sizing", {}).get("contracts", 0) <= 1  # Single contract only
        ]
        
        if all(auto_approve_conditions):
            # Auto-approve
            self.process_approval(
                plan_id,
                ApprovalAction.APPROVE,
                "Auto-approved: meets conservative criteria",
                None
            )
            print(f"[Approval] Plan {plan_id} auto-approved")
            return True
        
        return False
    
    def get_approval_stats(self) -> Dict[str, Any]:
        """Get approval statistics for monitoring."""
        total_requests = len(self.approval_history) + len(self.pending_approvals)
        
        if total_requests == 0:
            return {"total_requests": 0}
        
        # Count by action
        action_counts = {}
        for response in self.approval_history:
            action = response.action.value
            action_counts[action] = action_counts.get(action, 0) + 1
        
        approval_rate = action_counts.get("approve", 0) / len(self.approval_history) if self.approval_history else 0
        
        return {
            "total_requests": total_requests,
            "pending": len(self.pending_approvals),
            "completed": len(self.approval_history),
            "approval_rate": approval_rate,
            "action_counts": action_counts,
            "avg_time_to_decision": "not_calculated"  # Could implement if needed
        }


# Global approval flow instance
_global_approval_flow = None

def get_approval_flow() -> ApprovalFlow:
    """Get the global approval flow instance."""
    global _global_approval_flow
    if _global_approval_flow is None:
        _global_approval_flow = ApprovalFlow()
    return _global_approval_flow