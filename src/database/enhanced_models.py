#!/usr/bin/env python3
"""
EMO Options Bot - Enhanced SQLAlchemy Models
============================================
Institutional-grade database models using SQLAlchemy 2.0+:
- Staged orders with comprehensive workflow tracking
- Market events optimized for time-series analysis
- Strategy performance and risk metrics
- System health monitoring and metrics
- Execution tracking with audit trails

Features:
- Modern SQLAlchemy 2.0+ with typing support
- Optimized indexes for performance queries
- JSON metadata for flexible data storage
- Multi-environment support with audit trails
- TimescaleDB optimization for time-series data
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, DateTime, JSON, Index, Text, Boolean, ForeignKey
from sqlalchemy.sql import func

Base = declarative_base()

class StagedOrder(Base):
    """
    Enhanced staged order model for comprehensive order management.
    Tracks orders from creation through review to execution or cancellation.
    Integrates with file-based YAML/JSON drafts for hybrid storage approach.
    """
    __tablename__ = "staged_orders"

    # Primary key and identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True, nullable=True)
    
    # Core order details
    symbol: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)  # "buy" | "sell" | "short"
    qty: Mapped[float] = mapped_column(Float, nullable=False)
    order_type: Mapped[str] = mapped_column(String(16), nullable=False, default="market")  # market, limit, stop
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # limit/stop price
    
    # Strategy and metadata
    strategy: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 0.0-1.0 confidence score
    risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # calculated risk metric
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # flexible metadata storage
    
    # File system integration
    filepath: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)  # path to YAML/JSON draft
    checksum: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)  # file integrity check
    
    # Status and workflow
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="draft", index=True)
    # Status values: draft, pending_review, approved, rejected, executed, cancelled, expired
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps and audit trail
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    
    # Environment and source tracking
    environment: Mapped[str] = mapped_column(String(16), nullable=False, default="dev", index=True)
    source: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # strategy source, manual, etc.
    
    __table_args__ = (
        Index("ix_staged_orders_symbol_created", "symbol", "created_at"),
        Index("ix_staged_orders_status_expires", "status", "expires_at"),
        Index("ix_staged_orders_strategy_confidence", "strategy", "confidence"),
        Index("ix_staged_orders_env_status", "environment", "status"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side,
            "qty": self.qty,
            "order_type": self.order_type,
            "price": self.price,
            "strategy": self.strategy,
            "confidence": self.confidence,
            "risk_score": self.risk_score,
            "meta": self.meta,
            "filepath": self.filepath,
            "status": self.status,
            "reviewed_by": self.reviewed_by,
            "review_notes": self.review_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "environment": self.environment,
            "source": self.source
        }

class MarketEvent(Base):
    """
    Enhanced market event model for time-series data storage.
    Optimized for TimescaleDB hypertables in production environments.
    Stores market shocks, IV updates, breadth indicators, and system events.
    """
    __tablename__ = "market_events"

    # Primary key and timing
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    
    # Event classification
    name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    # Event names: shock_update, iv_snapshot, breadth_scan, strategy_signal, etc.
    category: Mapped[str] = mapped_column(String(32), index=True, nullable=False, default="market")
    # Categories: market, strategy, system, alert, performance
    
    # Content and metadata
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # event data
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # human-readable summary
    level: Mapped[str] = mapped_column(String(16), nullable=False, default="info")
    # Levels: debug, info, warning, error, critical
    
    # Source and context
    source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    # Source: live_logger, runner, strategy_engine, etc.
    session_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    
    # Metrics and performance
    duration_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # event processing time
    memory_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # memory usage
    cpu_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # CPU usage
    
    # Environment tracking
    environment: Mapped[str] = mapped_column(String(16), nullable=False, default="dev", index=True)
    
    __table_args__ = (
        Index("ix_market_events_name_ts", "name", "ts"),
        Index("ix_market_events_category_level", "category", "level"),
        Index("ix_market_events_source_ts", "source", "ts"),
        Index("ix_market_events_session_ts", "session_id", "ts"),
        Index("ix_market_events_env_category", "environment", "category"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "ts": self.ts.isoformat() if self.ts else None,
            "name": self.name,
            "category": self.category,
            "payload": self.payload,
            "summary": self.summary,
            "level": self.level,
            "source": self.source,
            "session_id": self.session_id,
            "correlation_id": self.correlation_id,
            "duration_ms": self.duration_ms,
            "memory_mb": self.memory_mb,
            "cpu_percent": self.cpu_percent,
            "environment": self.environment
        }

class ExecutedOrder(Base):
    """
    Historical record of executed orders for performance analysis.
    Links back to staged orders and tracks actual execution details.
    """
    __tablename__ = "executed_orders"
    
    # Primary key and linking
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    staged_order_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('staged_orders.id'), nullable=True, index=True)
    broker_order_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True, nullable=True)
    
    # Execution details
    symbol: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    side: Mapped[str] = mapped_column(String(8), nullable=False)
    qty_requested: Mapped[float] = mapped_column(Float, nullable=False)
    qty_filled: Mapped[float] = mapped_column(Float, nullable=False)
    price_requested: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    price_filled: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Strategy and performance
    strategy: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    execution_cost: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # slippage + fees
    market_impact: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # price impact
    
    # Status and timing
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    # Status: filled, partially_filled, cancelled, rejected
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    latency_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # order latency
    
    # Environment and metadata
    environment: Mapped[str] = mapped_column(String(16), nullable=False, default="dev", index=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    __table_args__ = (
        Index("ix_executed_orders_symbol_executed", "symbol", "executed_at"),
        Index("ix_executed_orders_strategy_status", "strategy", "status"),
        Index("ix_executed_orders_env_executed", "environment", "executed_at"),
    )

class StrategyPerformance(Base):
    """
    Strategy performance metrics and analysis tracking.
    Aggregated statistics for strategy evaluation and optimization.
    """
    __tablename__ = "strategy_performance"
    
    # Primary key and identification
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_name: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, index=True, nullable=False)
    
    # Performance metrics
    total_trades: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    winning_trades: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    losing_trades: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_pnl: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    avg_win: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_loss: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_drawdown: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Risk metrics
    var_95: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Value at Risk
    max_position_size: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_holding_time: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # hours
    
    # Environment and metadata
    environment: Mapped[str] = mapped_column(String(16), nullable=False, default="dev", index=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    
    __table_args__ = (
        Index("ix_strategy_performance_name_period", "strategy_name", "period_start", "period_end"),
        Index("ix_strategy_performance_env_created", "environment", "created_at"),
    )

class SystemHealth(Base):
    """
    System health metrics and monitoring data storage.
    Tracks component health, performance metrics, and system events.
    """
    __tablename__ = "system_health"
    
    # Primary key and timing
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ts: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    
    # Component identification
    component: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    # Components: runner, live_logger, database, health_monitor, etc.
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    # Status: healthy, warning, error, offline
    
    # Health metrics
    cpu_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    memory_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    disk_gb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    response_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    throughput: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Version and configuration
    version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    config_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Environment and metadata
    environment: Mapped[str] = mapped_column(String(16), nullable=False, default="dev", index=True)
    meta: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    __table_args__ = (
        Index("ix_system_health_component_ts", "component", "ts"),
        Index("ix_system_health_status_ts", "status", "ts"),
        Index("ix_system_health_env_component", "environment", "component"),
    )

def get_metadata():
    """
    Export SQLAlchemy metadata for migration tooling and schema management.
    Used by migration system for table creation and schema updates.
    """
    return Base.metadata

def create_session_factory(engine):
    """
    Create SQLAlchemy session factory for database operations.
    Returns configured sessionmaker for consistent session management.
    """
    from sqlalchemy.orm import sessionmaker
    return sessionmaker(bind=engine, expire_on_commit=False)

def health_check_models() -> Dict[str, Any]:
    """
    Perform health check on database models and return status.
    Validates model definitions and metadata consistency.
    """
    try:
        metadata = get_metadata()
        tables = list(metadata.tables.keys())
        
        # Check for required tables
        required_tables = ["staged_orders", "market_events", "executed_orders", "strategy_performance", "system_health"]
        missing_tables = [table for table in required_tables if table not in tables]
        
        # Check for required indexes
        total_indexes = sum(len(table.indexes) for table in metadata.tables.values())
        
        return {
            "status": "healthy" if not missing_tables else "error",
            "tables_defined": len(tables),
            "tables_list": tables,
            "missing_tables": missing_tables,
            "total_indexes": total_indexes,
            "models_available": [
                "StagedOrder", "MarketEvent", "ExecutedOrder", 
                "StrategyPerformance", "SystemHealth"
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "models_available": []
        }

# Export key classes and functions for external use
__all__ = [
    "Base", 
    "StagedOrder", 
    "MarketEvent", 
    "ExecutedOrder", 
    "StrategyPerformance", 
    "SystemHealth",
    "get_metadata", 
    "create_session_factory", 
    "health_check_models"
]