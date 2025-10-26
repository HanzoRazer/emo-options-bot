"""LLM Orchestrator (Phase 3)
Safe to import without OpenAI: falls back to mock outputs."""
from __future__ import annotations
import os
from typing import Optional
from .schemas import MarketView

class Orchestrator:
    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or os.getenv("EMO_LLM_PROVIDER", "mock")
        self._openai = None
        if self.provider.lower() == "openai":
            try:
                import openai  # type: ignore
                openai.api_key = os.getenv("OPENAI_API_KEY","")
                self._openai = openai
            except Exception:
                self.provider = "mock"

    def analyze(self, natural_text: str) -> MarketView:
        # Very light mock "NLP": pick a symbol + outlook from text
        text = natural_text.lower()
        sym = "SPY"
        for s in ["SPY","QQQ","AAPL","MSFT","IWM","DIA"]:
            if s.lower() in text:
                sym = s
                break
        outlook = "neutral"
        if "sideways" in text or "range" in text:
            outlook = "range"
        elif "volatile" in text or "volatility" in text:
            outlook = "volatile"
        elif "bull" in text or "up" in text:
            outlook = "bullish"
        elif "bear" in text or "down" in text:
            outlook = "bearish"
        return MarketView(symbol=sym, outlook=outlook, horizon_days=7, confidence=0.55, notes="mock-llm")