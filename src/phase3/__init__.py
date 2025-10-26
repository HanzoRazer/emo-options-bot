# src/phase3/__init__.py
"""
Phase 3 Integration Module
Enhanced orchestration with production-ready features

Phase 3 test harness package (mock LLM + fake market + adapters).
This package is intentionally dependency-light and will fall back to
internal shims if your real phase3 modules aren't present.

Auto-loader and integration helpers live here.
"""

from .hooks import (
    synthesize_and_stage,
    enhanced_synthesis_pipeline,
    OptionsChainIntegrator
)

__all__ = [
    "synthesize_and_stage",
    "enhanced_synthesis_pipeline", 
    "OptionsChainIntegrator"
]