from __future__ import annotations
import os
from typing import Dict, Any, List

class OptionsChainProvider:
    def get_option_chain(self, symbol: str) -> Dict[str, Any]:
        raise NotImplementedError

class AlpacaOptionsChain(OptionsChainProvider):
    """Stub: fetch from Alpaca options data when enabled/available."""
    def __init__(self):
        self.key = os.getenv("ALPACA_KEY_ID")
        self.secret = os.getenv("ALPACA_SECRET_KEY")
        self.base = os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets/v2")

    def get_option_chain(self, symbol: str) -> Dict[str, Any]:
        # TODO: Implement real Alpaca options chain when your plan supports it
        # Returning mock structure
        return {
            "provider": "alpaca",
            "symbol": symbol,
            "expirations": [],
            "calls": [],
            "puts": [],
            "note": "Alpaca options chain stub — integrate when API is enabled for your account."
        }

class PolygonOptionsChain(OptionsChainProvider):
    """Stub: Polygon.io options chain (requires POLYGON_API_KEY)"""
    def __init__(self):
        self.key = os.getenv("POLYGON_API_KEY")

    def get_option_chain(self, symbol: str) -> Dict[str, Any]:
        return {
            "provider": "polygon",
            "symbol": symbol,
            "expirations": [],
            "calls": [],
            "puts": [],
            "note": "Polygon options chain stub — wire real HTTP calls when ready."
        }

def get_provider(name: str = None) -> OptionsChainProvider:
    name = (name or os.getenv("EMO_OPTIONS_PROVIDER", "alpaca")).lower()
    if name == "polygon":
        return PolygonOptionsChain()
    return AlpacaOptionsChain()