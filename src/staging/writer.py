# src/staging/writer.py
"""
Enhanced Trade Staging Writer with Production Features
Comprehensive trade plan staging with validation and metadata
"""
from __future__ import annotations
import os
import json
import time
import uuid
import pathlib
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

# Configuration
DEFAULT_DIR = pathlib.Path(os.getenv("EMO_STAGING_DIR", "ops/staged_orders"))
BACKUP_DIR = pathlib.Path(os.getenv("EMO_BACKUP_DIR", "ops/staged_orders/backup"))

@dataclass
class StagingMetadata:
    """Enhanced metadata for staged trades"""
    created_utc: float
    created_iso: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    source: str = "emo_bot"
    risk_level: str = "UNKNOWN"
    auto_approved: bool = False
    requires_review: bool = True
    estimated_margin: Optional[float] = None
    max_loss: Optional[float] = None
    confidence_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

def ensure_dir(p: pathlib.Path) -> None:
    """
    Ensure directory exists with proper error handling
    
    Args:
        p: Path to create
    """
    try:
        p.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {p}")
    except Exception as e:
        logger.error(f"Failed to create directory {p}: {e}")
        raise

def validate_trade_plan(trade_plan: Dict[str, Any]) -> List[str]:
    """
    Validate trade plan structure and data
    
    Args:
        trade_plan: Trade plan dictionary
    
    Returns:
        List of validation errors (empty if valid)
    """
    errors = []
    
    try:
        # Required fields
        required_fields = ["symbol", "strategy", "legs"]
        for field in required_fields:
            if field not in trade_plan:
                errors.append(f"Missing required field: {field}")
        
        # Validate symbol
        symbol = trade_plan.get("symbol", "")
        if not symbol or not isinstance(symbol, str) or len(symbol) < 1:
            errors.append("Invalid symbol")
        
        # Validate strategy
        strategy = trade_plan.get("strategy", "")
        valid_strategies = [
            "iron_condor", "put_credit_spread", "call_credit_spread",
            "protective_put", "covered_call", "long_call", "long_put",
            "straddle", "strangle", "butterfly", "calendar_spread", "custom"
        ]
        if strategy not in valid_strategies:
            errors.append(f"Unknown strategy: {strategy}")
        
        # Validate legs
        legs = trade_plan.get("legs", [])
        if not isinstance(legs, list) or len(legs) == 0:
            errors.append("No legs in trade plan")
        
        for i, leg in enumerate(legs):
            if not isinstance(leg, dict):
                errors.append(f"Leg {i} is not a dictionary")
                continue
            
            # Required leg fields
            leg_required = ["right", "strike", "qty", "price"]
            for field in leg_required:
                if field not in leg:
                    errors.append(f"Leg {i} missing field: {field}")
            
            # Validate leg values
            if leg.get("right") not in ("call", "put"):
                errors.append(f"Leg {i} invalid right: {leg.get('right')}")
            
            try:
                strike = float(leg.get("strike", 0))
                if strike <= 0:
                    errors.append(f"Leg {i} invalid strike: {strike}")
            except (ValueError, TypeError):
                errors.append(f"Leg {i} strike not numeric")
            
            try:
                qty = int(leg.get("qty", 0))
                if qty == 0:
                    errors.append(f"Leg {i} quantity is zero")
            except (ValueError, TypeError):
                errors.append(f"Leg {i} quantity not numeric")
            
            try:
                price = float(leg.get("price", 0))
                if price < 0:
                    errors.append(f"Leg {i} negative price: {price}")
            except (ValueError, TypeError):
                errors.append(f"Leg {i} price not numeric")
        
        # Validate risk data if present
        risk_data = trade_plan.get("risk", {})
        if isinstance(risk_data, dict):
            for field in ["max_loss", "max_gain"]:
                value = risk_data.get(field)
                if value is not None:
                    try:
                        float_val = float(value)
                        if float_val < 0:
                            errors.append(f"Risk {field} cannot be negative: {float_val}")
                    except (ValueError, TypeError):
                        errors.append(f"Risk {field} not numeric: {value}")
        
    except Exception as e:
        errors.append(f"Validation error: {str(e)}")
    
    return errors

def calculate_trade_metadata(trade_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate enhanced metadata for trade plan
    
    Args:
        trade_plan: Trade plan dictionary
    
    Returns:
        Dictionary with calculated metadata
    """
    try:
        metadata = {}
        
        # Basic statistics
        legs = trade_plan.get("legs", [])
        metadata["leg_count"] = len(legs)
        
        if legs:
            strikes = [float(leg.get("strike", 0)) for leg in legs if leg.get("strike")]
            if strikes:
                metadata["strike_range"] = {
                    "min": min(strikes),
                    "max": max(strikes),
                    "width": max(strikes) - min(strikes) if len(strikes) > 1 else 0
                }
        
        # Risk metrics from risk data
        risk_data = trade_plan.get("risk", {})
        if isinstance(risk_data, dict):
            metadata["max_loss"] = risk_data.get("max_loss")
            metadata["max_gain"] = risk_data.get("max_gain")
            metadata["credit"] = risk_data.get("credit")
            metadata["margin_estimate"] = risk_data.get("margin_estimate")
            
            # Calculate risk/reward ratio
            max_loss = risk_data.get("max_loss", 0)
            max_gain = risk_data.get("max_gain", 0)
            if max_loss and max_loss > 0:
                metadata["risk_reward_ratio"] = max_gain / max_loss
            
            # Risk level classification
            if max_loss:
                if max_loss <= 500:
                    metadata["risk_level"] = "LOW"
                elif max_loss <= 2000:
                    metadata["risk_level"] = "MEDIUM"
                elif max_loss <= 5000:
                    metadata["risk_level"] = "HIGH"
                else:
                    metadata["risk_level"] = "VERY_HIGH"
        
        # Strategy complexity
        strategy = trade_plan.get("strategy", "")
        complexity_map = {
            "long_call": 1, "long_put": 1,
            "covered_call": 2, "protective_put": 2,
            "put_credit_spread": 2, "call_credit_spread": 2,
            "straddle": 3, "strangle": 3,
            "iron_condor": 4, "butterfly": 4,
            "calendar_spread": 5
        }
        metadata["complexity"] = complexity_map.get(strategy, 3)
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error calculating trade metadata: {e}")
        return {"error": str(e)}

def stage_trade(
    trade_plan: Dict[str, Any], 
    meta: Optional[Dict[str, Any]] = None,
    validate: bool = True,
    backup: bool = True
) -> pathlib.Path:
    """
    Enhanced trade staging with validation and metadata
    
    Args:
        trade_plan: Trade plan dictionary
        meta: Additional metadata
        validate: Whether to validate trade plan
        backup: Whether to create backup copy
    
    Returns:
        Path to staged trade file
    
    Raises:
        ValueError: If validation fails
        IOError: If file operations fail
    """
    try:
        # Validate trade plan if requested
        if validate:
            errors = validate_trade_plan(trade_plan)
            if errors:
                error_msg = f"Trade plan validation failed: {', '.join(errors)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        # Ensure staging directory exists
        ensure_dir(DEFAULT_DIR)
        if backup:
            ensure_dir(BACKUP_DIR)
        
        # Generate unique filename
        uid = uuid.uuid4().hex[:8]
        symbol = trade_plan.get("symbol", "UNKNOWN").replace("/", "_")
        timestamp = int(time.time())
        filename = f"{timestamp}_{symbol}_{uid}.json"
        filepath = DEFAULT_DIR / filename
        
        # Create enhanced metadata
        now = datetime.utcnow()
        staging_meta = StagingMetadata(
            created_utc=timestamp,
            created_iso=now.isoformat(),
            source=meta.get("source", "emo_bot") if meta else "emo_bot",
            user_id=meta.get("user_id") if meta else None,
            session_id=meta.get("session_id") if meta else None
        )
        
        # Calculate trade-specific metadata
        trade_metadata = calculate_trade_metadata(trade_plan)
        
        # Enhance staging metadata with trade info
        staging_meta.risk_level = trade_metadata.get("risk_level", "UNKNOWN")
        staging_meta.estimated_margin = trade_metadata.get("margin_estimate")
        staging_meta.max_loss = trade_metadata.get("max_loss")
        staging_meta.confidence_score = meta.get("confidence_score") if meta else None
        
        # Auto-approval logic
        if trade_metadata.get("risk_level") == "LOW" and trade_metadata.get("complexity", 5) <= 2:
            staging_meta.auto_approved = True
            staging_meta.requires_review = False
        
        # Create complete payload
        payload = {
            "trade_plan": trade_plan,
            "metadata": staging_meta.to_dict(),
            "trade_metadata": trade_metadata,
            "user_metadata": meta or {},
            "schema_version": 2,  # Enhanced version
            "validation_passed": validate,
            "filename": filename
        }
        
        # Write main file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        
        logger.info(f"Staged trade: {symbol} {trade_plan.get('strategy', 'unknown')} -> {filename}")
        
        # Create backup if requested
        if backup:
            backup_path = BACKUP_DIR / filename
            with open(backup_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)
            logger.debug(f"Created backup: {backup_path}")
        
        return filepath
        
    except Exception as e:
        logger.error(f"Error staging trade: {e}")
        raise

def load_staged_trade(filepath: pathlib.Path) -> Dict[str, Any]:
    """
    Load and validate staged trade
    
    Args:
        filepath: Path to staged trade file
    
    Returns:
        Complete trade payload
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is invalid
    """
    try:
        if not filepath.exists():
            raise FileNotFoundError(f"Staged trade file not found: {filepath}")
        
        with open(filepath, "r", encoding="utf-8") as f:
            payload = json.load(f)
        
        # Validate payload structure
        required_fields = ["trade_plan", "metadata", "schema_version"]
        for field in required_fields:
            if field not in payload:
                raise ValueError(f"Invalid staged trade: missing {field}")
        
        # Validate trade plan
        trade_plan = payload["trade_plan"]
        errors = validate_trade_plan(trade_plan)
        if errors:
            logger.warning(f"Loaded trade has validation issues: {', '.join(errors)}")
        
        logger.info(f"Loaded staged trade: {trade_plan.get('symbol')} {trade_plan.get('strategy')}")
        return payload
        
    except Exception as e:
        logger.error(f"Error loading staged trade {filepath}: {e}")
        raise

def list_staged_trades(pattern: str = "*.json") -> List[pathlib.Path]:
    """
    List all staged trades matching pattern
    
    Args:
        pattern: Glob pattern for files
    
    Returns:
        List of staged trade file paths
    """
    try:
        if not DEFAULT_DIR.exists():
            return []
        
        files = list(DEFAULT_DIR.glob(pattern))
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)  # Newest first
        
        logger.info(f"Found {len(files)} staged trades")
        return files
        
    except Exception as e:
        logger.error(f"Error listing staged trades: {e}")
        return []

def clean_old_trades(max_age_hours: int = 24) -> int:
    """
    Clean up old staged trades
    
    Args:
        max_age_hours: Maximum age in hours before cleanup
    
    Returns:
        Number of files cleaned up
    """
    try:
        if not DEFAULT_DIR.exists():
            return 0
        
        cutoff_time = time.time() - (max_age_hours * 3600)
        cleaned = 0
        
        for filepath in DEFAULT_DIR.glob("*.json"):
            try:
                if filepath.stat().st_mtime < cutoff_time:
                    filepath.unlink()
                    cleaned += 1
                    logger.debug(f"Cleaned old trade: {filepath.name}")
            except Exception as e:
                logger.warning(f"Failed to clean {filepath}: {e}")
        
        if cleaned > 0:
            logger.info(f"Cleaned {cleaned} old staged trades")
        
        return cleaned
        
    except Exception as e:
        logger.error(f"Error cleaning old trades: {e}")
        return 0

# Export main functions
__all__ = [
    "stage_trade",
    "load_staged_trade", 
    "list_staged_trades",
    "clean_old_trades",
    "ensure_dir",
    "validate_trade_plan",
    "StagingMetadata"
]