from __future__ import annotations
import datetime as dt
import logging
from typing import Optional, Dict, Any, Union
from decimal import Decimal

# Setup logging
logger = logging.getLogger(__name__)

try:
    from sqlalchemy.orm import declarative_base, Mapped, mapped_column
    from sqlalchemy import String, Integer, DateTime, Text, Numeric, Index
    try:
        from sqlalchemy import JSON  # SQLAlchemy 2.x
    except Exception:
        JSON = Text  # Fallback: store JSON as text if driver lacks JSON
except Exception as e:
    logger.warning(f"SQLAlchemy not available: {e}")
    # Allow importing the module even if SQLAlchemy is missing
    declarative_base = lambda: None  # type: ignore
    Mapped = object  # type: ignore
    def mapped_column(*args, **kwargs):  # type: ignore
        return None
    String = Integer = DateTime = Text = Numeric = Index = object  # type: ignore
    JSON = Text  # type: ignore

Base = declarative_base() if callable(declarative_base) else None  # type: ignore

if Base:
    class StagedOrder(Base):  # type: ignore
        """
        Enhanced StagedOrder model with institutional features integration.
        
        Provides order staging functionality with:
        - SQLAlchemy 2.0+ compatibility
        - Comprehensive type hints
        - Integration with institutional monitoring
        - Enhanced metadata tracking
        - Audit trail capabilities
        """
        __tablename__ = "staged_orders"
        
        # Indexes for performance
        __table_args__ = (
            Index("idx_staged_orders_symbol", "symbol"),
            Index("idx_staged_orders_status", "status"),
            Index("idx_staged_orders_created_at", "created_at"),
            Index("idx_staged_orders_user", "user"),
            Index("idx_staged_orders_strategy", "strategy"),
        )

        # Primary key and timestamps
        id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
        created_at: Mapped[dt.datetime] = mapped_column(
            DateTime, 
            default=lambda: dt.datetime.now(dt.timezone.utc),
            index=True
        )
        updated_at: Mapped[Optional[dt.datetime]] = mapped_column(
            DateTime,
            default=None,
            onupdate=lambda: dt.datetime.now(dt.timezone.utc)
        )

        # Core order fields
        symbol: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
        side: Mapped[str] = mapped_column(String(8), nullable=False)  # 'buy' | 'sell'
        qty: Mapped[int] = mapped_column(Integer, nullable=False)
        order_type: Mapped[str] = mapped_column(String(16), default="market", nullable=False)
        
        # Enhanced fields for institutional use
        limit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
        stop_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
        time_in_force: Mapped[str] = mapped_column(String(16), default="DAY", nullable=False)
        
        # Strategy and user tracking
        strategy: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
        user: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
        
        # Enhanced metadata and tracking
        note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
        raw_file: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # path to YAML/JSON draft
        meta: Mapped[Optional[dict]] = mapped_column(JSON if JSON != Text else Text, nullable=True)
        
        # Workflow and status tracking
        status: Mapped[str] = mapped_column(String(16), default="staged", nullable=False, index=True)
        # Status values: staged|reviewed|approved|rejected|sent|executed|cancelled|failed
        
        # Institutional features
        risk_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
        compliance_flags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
        approval_required: Mapped[bool] = mapped_column(Integer, default=0, nullable=False)  # SQLite boolean
        approved_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
        approved_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)
        
        # Execution tracking
        sent_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)
        executed_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime, nullable=True)
        execution_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
        execution_qty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
        
        # Error tracking
        error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
        retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

        def as_dict(self) -> Dict[str, Any]:
            """
            Convert model instance to dictionary with proper type handling.
            
            Returns:
                Dictionary representation of the staged order
            """
            return {
                "id": self.id,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
                "symbol": self.symbol,
                "side": self.side,
                "qty": self.qty,
                "order_type": self.order_type,
                "limit_price": float(self.limit_price) if self.limit_price else None,
                "stop_price": float(self.stop_price) if self.stop_price else None,
                "time_in_force": self.time_in_force,
                "strategy": self.strategy,
                "user": self.user,
                "note": self.note,
                "raw_file": self.raw_file,
                "meta": self.meta,
                "status": self.status,
                "risk_score": float(self.risk_score) if self.risk_score else None,
                "compliance_flags": self.compliance_flags,
                "approval_required": bool(self.approval_required),
                "approved_by": self.approved_by,
                "approved_at": self.approved_at.isoformat() if self.approved_at else None,
                "sent_at": self.sent_at.isoformat() if self.sent_at else None,
                "executed_at": self.executed_at.isoformat() if self.executed_at else None,
                "execution_price": float(self.execution_price) if self.execution_price else None,
                "execution_qty": self.execution_qty,
                "error_message": self.error_message,
                "retry_count": self.retry_count,
            }
        
        def update_status(self, new_status: str, user: Optional[str] = None, note: Optional[str] = None):
            """
            Update order status with audit trail.
            
            Args:
                new_status: New status value
                user: User making the change
                note: Optional note about the change
            """
            old_status = self.status
            self.status = new_status
            self.updated_at = dt.datetime.now(dt.timezone.utc)
            
            # Add to metadata for audit trail
            if not self.meta:
                self.meta = {}
            
            if "status_history" not in self.meta:
                self.meta["status_history"] = []
            
            self.meta["status_history"].append({
                "from": old_status,
                "to": new_status,
                "timestamp": self.updated_at.isoformat(),
                "user": user,
                "note": note
            })
            
            logger.info(f"StagedOrder {self.id} status changed: {old_status} -> {new_status}")
        
        def calculate_risk_score(self) -> Decimal:
            """
            Calculate risk score for the order.
            
            Returns:
                Risk score (0-100, higher is riskier)
            """
            risk = Decimal('0')
            
            # Quantity risk
            if self.qty > 1000:
                risk += Decimal('20')
            elif self.qty > 500:
                risk += Decimal('10')
            
            # Order type risk
            if self.order_type == "market":
                risk += Decimal('15')
            elif "stop" in self.order_type.lower():
                risk += Decimal('10')
            
            # Symbol risk (basic heuristic)
            if len(self.symbol) > 5:  # Options typically longer
                risk += Decimal('25')
            
            # Time in force risk
            if self.time_in_force == "IOC":
                risk += Decimal('20')
            elif self.time_in_force == "FOK":
                risk += Decimal('25')
            
            # Cap at 100
            self.risk_score = min(risk, Decimal('100'))
            return self.risk_score
        
        def validate_compliance(self) -> list[str]:
            """
            Validate order for compliance issues.
            
            Returns:
                List of compliance issues (empty if compliant)
            """
            issues = []
            
            # Basic validation
            if not self.symbol:
                issues.append("Missing symbol")
            
            if self.qty <= 0:
                issues.append("Invalid quantity")
            
            if self.side not in ("buy", "sell"):
                issues.append("Invalid side")
            
            # Risk limits
            if self.qty > 10000:
                issues.append("Quantity exceeds limit (10,000)")
            
            # Store compliance flags
            self.compliance_flags = "; ".join(issues) if issues else None
            
            return issues
        
        def requires_approval(self) -> bool:
            """
            Determine if order requires manual approval.
            
            Returns:
                True if approval required, False otherwise
            """
            # High quantity orders
            if self.qty > 5000:
                self.approval_required = True
                return True
            
            # High risk orders
            if self.risk_score and self.risk_score > Decimal('50'):
                self.approval_required = True
                return True
            
            # Compliance issues
            if self.compliance_flags:
                self.approval_required = True
                return True
            
            self.approval_required = False
            return False
        
        def __repr__(self) -> str:
            return f"<StagedOrder(id={self.id}, symbol={self.symbol}, side={self.side}, qty={self.qty}, status={self.status})>"
        
        @classmethod
        def get_by_status(cls, session, status: str, limit: int = 100):
            """
            Get orders by status.
            
            Args:
                session: SQLAlchemy session
                status: Order status to filter by
                limit: Maximum number of orders to return
                
            Returns:
                List of StagedOrder instances
            """
            return session.query(cls).filter(cls.status == status).limit(limit).all()
        
        @classmethod
        def get_pending_approval(cls, session, limit: int = 100):
            """
            Get orders pending approval.
            
            Args:
                session: SQLAlchemy session
                limit: Maximum number of orders to return
                
            Returns:
                List of StagedOrder instances
            """
            return session.query(cls).filter(
                cls.approval_required == True,
                cls.approved_at == None,
                cls.status.in_(["staged", "reviewed"])
            ).limit(limit).all()

else:
    # Placeholder to avoid AttributeErrors if SQLAlchemy not installed
    logger.warning("SQLAlchemy not available - StagedOrder will be a placeholder class")
    
    class StagedOrder:  # type: ignore
        """Placeholder StagedOrder class when SQLAlchemy is not available."""
        
        def __init__(self, *args, **kwargs):
            logger.error("StagedOrder requires SQLAlchemy. Install with: pip install SQLAlchemy>=2.0")
            raise RuntimeError("SQLAlchemy required for StagedOrder functionality")
        
        @staticmethod
        def as_dict():
            return {}

# Export key classes
__all__ = [
    "Base",
    "StagedOrder"
]