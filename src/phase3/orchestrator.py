from __future__ import annotations
import os
from typing import Dict, Any
from .schemas import AnalysisRequest


class MockLLM:
    """
    Deterministic fallback when no LLM key/provider is present.
    Very simple intent extraction:
      - mentions 'sideways' or 'range' -> neutral
      - mentions 'volatile' or 'big move' -> high-vol
      - mentions 'bear' or 'down' -> bearish
      - mentions 'bull' or 'up' -> bullish
    """
    def complete(self, req: AnalysisRequest) -> Dict[str, Any]:
        t = req.user_text.lower()
        if any(w in t for w in ["sideways", "range", "flat", "chop"]):
            view = "neutral"
        elif any(w in t for w in ["volatile", "big move", "spike", "swing"]):
            view = "high_vol"
        elif any(w in t for w in ["bear", "down", "sell-off", "dump"]):
            view = "bearish"
        elif any(w in t for w in ["bull", "up", "rally", "squeeze"]):
            view = "bullish"
        else:
            view = "neutral"
        return {
            "symbol": req.symbol,
            "horizon_days": req.horizon_days,
            "view": view,
            "confidence": 0.62,
            "notes": "MockLLM generated view"
        }


class LLMOrchestrator:
    """
    Pluggable LLM orchestrator. Uses Mock provider unless OPENAI_API_KEY is set
    (you can add a real OpenAI client later without changing callers).
    """
    def __init__(self):
        self.provider = "mock"
        self._mock = MockLLM()
        self._openai = None

        if os.getenv("OPENAI_API_KEY"):
            # Lazy: keep using mock until you wire the actual client
            # (Design leaves a stub for a real provider)
            self.provider = "mock-openai"  # becomes "openai" once you add real client

    def analyze(self, req: AnalysisRequest) -> Dict[str, Any]:
        # For now always call mock. Replace with real call when ready.
        return self._mock.complete(req)