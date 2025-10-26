from __future__ import annotations
import os
from typing import Dict, Any

class SafeSubmitter:
    """
    Safety-first broker submission router.
    - order_mode in {'stage', 'paper', 'live'}
    - broker in {'alpaca', 'mock'}
    """
    def __init__(self, broker: str = "alpaca", order_mode: str = None):
        self.broker = broker.lower()
        self.order_mode = (order_mode or os.getenv("EMO_ORDER_MODE", "stage")).lower()

        if self.order_mode not in {"stage", "paper", "live"}:
            raise ValueError(f"Invalid EMO_ORDER_MODE: {self.order_mode}")

        if self.broker == "alpaca":
            try:
                from exec.alpaca_broker import AlpacaBroker
            except Exception as e:
                raise RuntimeError(f"AlpacaBroker not available: {e}")
            self.client = AlpacaBroker(paper=(self.order_mode != "live"))
        else:
            self.client = None  # Extend if you add more brokers

    def submit_strategy(self, staged_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert staged multi-leg payload to broker orders. For spreads/condors, 
        submit legs one by one (basic version). Enhance as needed to use OTO/OTOCO.
        """
        if self.order_mode == "stage":
            return {"warning": "order_mode=stage — not submitting", "payload": staged_payload}

        if self.order_mode == "live":
            # HARD GUARD — require explicit consent
            if os.getenv("EMO_LIVE_CONFIRM") != "I_UNDERSTAND_THE_RISK":
                raise PermissionError("Live trading blocked. Set EMO_LIVE_CONFIRM=I_UNDERSTAND_THE_RISK to allow.")

        legs = staged_payload.get("legs", [])
        symbol = staged_payload.get("symbol", "")

        results = []
        for leg in legs:
            # Example: translate to a synthetic order
            # Real implementation should use a proper options order API
            res = self._submit_leg(symbol, leg)
            results.append(res)

        return {"submitted": True, "legs": results, "mode": self.order_mode, "broker": self.broker}

    def _submit_leg(self, symbol: str, leg: Dict[str, Any]) -> Dict[str, Any]:
        side = leg.get("action")  # buy / sell
        qty = int(leg.get("quantity", 1))
        # NOTE: This is a placeholder — use your broker's options API for real multi-leg orders.
        # For now we just submit a stock placeholder (or skip real submission if not supported).
        try:
            # Example: submit a tiny "marker" order in paper mode or just log.
            # self.client.submit_order(symbol, side=side, qty=1, type="market")
            return {"symbol": symbol, "side": side, "qty": qty, "status": "ACK (placeholder)"}
        except Exception as e:
            return {"symbol": symbol, "side": side, "qty": qty, "error": str(e)}