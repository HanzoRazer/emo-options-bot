# src/options/__init__.py
"""
Options chain and pricing module
Enhanced with production-ready features and fallback systems
"""

from .chain_providers import OptionsChainProvider, OptionQuote

# Enhanced providers are optional
try:
    from .enhanced_chain_providers import EnhancedOptionsChainProvider, OptionChainCache
    _HAS_ENHANCED = True
except ImportError:
    _HAS_ENHANCED = False
    # Provide fallback classes
    class EnhancedOptionsChainProvider:
        pass
    class OptionChainCache:
        pass

__all__ = [
    "OptionsChainProvider",
    "OptionQuote", 
    "EnhancedOptionsChainProvider",
    "OptionChainCache"
]