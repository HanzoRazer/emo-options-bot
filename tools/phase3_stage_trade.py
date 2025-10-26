#!/usr/bin/env python3
"""
Phase 3 Trade Staging CLI
Stages validated trade plans for review and approval
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import shutil

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Try to import staging module, fall back to simple implementation
try:
    from staging.writer import stage_trade, StagingMetadata
    HAS_STAGING_MODULE = True
except ImportError:
    print("⚠️ Staging module not available, using simple file writing")
    HAS_STAGING_MODULE = False
    
    # Simple staging implementation
    class StagingMetadata:
        def __init__(self, staged_at, source_file, priority="normal", reviewer=None, notes="", risk_assessment="pending"):
            self.staged_at = staged_at
            self.source_file = source_file
            self.priority = priority
            self.reviewer = reviewer
            self.notes = notes
            self.risk_assessment = risk_assessment
    
    def stage_trade(plan, staging_dir):
        """Simple file-based staging"""
        staging_path = Path(staging_dir)
        staging_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        symbol = plan.get("symbol", "UNKNOWN")
        strategy = plan.get("strategy_type", "unknown")
        filename = f"staged_{symbol}_{strategy}_{timestamp}.json"
        
        file_path = staging_path / filename
        
        # Write the plan
        with open(file_path, 'w') as f:
            json.dump(plan, f, indent=2)
        
        return file_path

def parse_args():
    parser = argparse.ArgumentParser(description="Stage trade plans for review and approval")
    parser.add_argument("--from-plan", required=True, help="Path to validated trade plan JSON")
    parser.add_argument("--note", help="Additional notes for the staged trade")
    parser.add_argument("--priority", choices=["low", "normal", "high"], default="normal", help="Trade priority")
    parser.add_argument("--reviewer", help="Assigned reviewer (optional)")
    parser.add_argument("--auto-approve", action="store_true", help="Auto-approve if risk is low enough")
    parser.add_argument("--staging-dir", help="Override staging directory")
    return parser.parse_args()

def load_trade_plan(file_path: str) -> dict:
    """Load validated trade plan"""
    try:
        with open(file_path, 'r') as f:
            plan = json.load(f)
        return plan
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(1)

def enhance_plan_for_staging(plan: dict, note: str = None, priority: str = "normal", reviewer: str = None) -> dict:
    """Enhance plan with staging metadata"""
    
    # Create staging metadata
    metadata = StagingMetadata(
        staged_at=datetime.now(),
        source_file=str(Path(sys.argv[0]).name),
        priority=priority,
        reviewer=reviewer,
        notes=note or f"Staged {plan['strategy_type']} on {plan['symbol']}",
        risk_assessment="pending"
    )
    
    # Enhanced plan for staging
    enhanced_plan = plan.copy()
    enhanced_plan["staging"] = {
        "staged_at": metadata.staged_at.isoformat(),
        "source": metadata.source_file,
        "priority": metadata.priority,
        "reviewer": metadata.reviewer,
        "notes": metadata.notes,
        "status": "pending_review",
        "risk_assessment": metadata.risk_assessment,
        "staging_id": f"{plan['symbol']}_{plan['strategy_type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    }
    
    # Add execution metadata
    enhanced_plan["execution"] = {
        "status": "not_executed",
        "execution_method": "manual_review",
        "requires_approval": True,
        "estimated_execution_time": "2-5 minutes",
        "broker": "alpaca_paper"
    }
    
    return enhanced_plan

def assess_auto_approval(plan: dict) -> bool:
    """Determine if trade can be auto-approved based on risk"""
    
    # Check risk constraints
    constraints = plan.get("risk_constraints", {})
    max_loss = constraints.get("max_loss", float('inf'))
    risk_pct = constraints.get("max_trade_risk_pct", 1.0)
    
    # Auto-approve criteria (conservative)
    AUTO_APPROVE_MAX_LOSS = 500  # Max $500 loss
    AUTO_APPROVE_MAX_RISK_PCT = 0.01  # Max 1% portfolio risk
    
    if max_loss <= AUTO_APPROVE_MAX_LOSS and risk_pct <= AUTO_APPROVE_MAX_RISK_PCT:
        return True
    
    return False

def create_staging_summary(plan: dict) -> str:
    """Create human-readable staging summary"""
    
    summary = f"""
STAGED TRADE SUMMARY
==================

Strategy: {plan['strategy_type'].replace('_', ' ').title()}
Symbol: {plan['symbol']}
Expiration: {plan['expiration']}

Legs:"""
    
    for i, leg in enumerate(plan['legs'], 1):
        summary += f"\n  {i}. {leg['action'].title()} {leg['quantity']} {leg['instrument']} @ ${leg['strike']}"
    
    constraints = plan.get("risk_constraints", {})
    summary += f"""

Risk Profile:
  Max Loss: ${constraints.get('max_loss', 'N/A')}
  Risk %: {constraints.get('max_trade_risk_pct', 0)*100:.1f}%

Staging Info:
  Priority: {plan['staging']['priority']}
  Status: {plan['staging']['status']}
  Staged At: {plan['staging']['staged_at']}
  Notes: {plan['staging']['notes']}

"""
    
    if plan['staging']['status'] == 'auto_approved':
        summary += "STATUS: AUTO-APPROVED (Low Risk)\n"
    else:
        summary += "STATUS: PENDING MANUAL REVIEW\n"
    
    return summary

def main():
    args = parse_args()
    
    print(f"📋 Staging trade plan: {args.from_plan}")
    print(f"📝 Note: {args.note or 'None'}")
    print(f"⚡ Priority: {args.priority}")
    print()
    
    # Load trade plan
    plan = load_trade_plan(args.from_plan)
    
    # Enhance plan for staging
    enhanced_plan = enhance_plan_for_staging(
        plan, 
        note=args.note,
        priority=args.priority,
        reviewer=args.reviewer
    )
    
    # Check for auto-approval
    if args.auto_approve and assess_auto_approval(enhanced_plan):
        enhanced_plan["staging"]["status"] = "auto_approved"
        enhanced_plan["staging"]["risk_assessment"] = "low_risk_auto_approved"
        enhanced_plan["execution"]["requires_approval"] = False
        print("✅ Trade qualifies for auto-approval (low risk)")
    else:
        print("⏳ Trade requires manual review")
    
    # Stage the trade
    try:
        staging_dir = args.staging_dir or "ops/staged_orders"
        staged_path = stage_trade(enhanced_plan, staging_dir)
        print(f"📁 Staged to: {staged_path}")
        
        # Create summary file
        summary_path = staged_path.with_suffix('.summary.txt')
        summary = create_staging_summary(enhanced_plan)
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"📄 Summary: {summary_path}")
        
        # Create backup copy
        backup_dir = Path(staging_dir) / "backup"
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / f"backup_{staged_path.name}"
        shutil.copy2(staged_path, backup_path)
        
        print(f"💾 Backup: {backup_path}")
        
    except Exception as e:
        print(f"❌ Staging failed: {e}")
        return 1
    
    # Display summary
    print("\n" + "="*50)
    print(create_staging_summary(enhanced_plan))
    
    # Next steps
    print("NEXT STEPS:")
    if enhanced_plan["staging"]["status"] == "auto_approved":
        print("  ✅ Trade is auto-approved and ready for execution")
        print("  🚀 Execute with: python tools/execute_staged_trade.py")
    else:
        print("  👀 Review staged trade files")
        print("  ✅ Approve manually if acceptable")
        print("  🚀 Execute when ready")
    
    print(f"\nFiles created:")
    print(f"  📋 Plan: {staged_path}")
    print(f"  📄 Summary: {summary_path}")
    print(f"  💾 Backup: {backup_path}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())