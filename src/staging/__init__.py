# src/staging/__init__.py
"""
Trade staging and order management module
Enhanced with production-ready features and validation
"""

from .writer import stage_trade, ensure_dir

# Enhanced staging is optional
try:
    from .enhanced_staging import EnhancedTradeStaging, StagingConfig
    _HAS_ENHANCED = True
except ImportError:
    _HAS_ENHANCED = False
    # Provide fallback classes
    class EnhancedTradeStaging:
        pass
    class StagingConfig:
        pass

__all__ = [
    "stage_trade", 
    "ensure_dir",
    "EnhancedTradeStaging",
    "StagingConfig"
]