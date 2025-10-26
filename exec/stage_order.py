"""
Order Staging System for EMO Options Bot
Provides safe "paper staging" for order management with multi-language support.
"""

from __future__ import annotations
import os, json, uuid, time, hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

try:
    import yaml  # type: ignore
    _HAS_YAML = True
except Exception:
    _HAS_YAML = False

# Root-resolved drafts folder (adjust if needed)
ROOT = Path(__file__).resolve().parents[1]
DRAFTS_DIR = ROOT / "ops" / "orders" / "drafts"
DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

STAGE_VAR = "EMO_STAGE_ORDERS"     # "1" → write drafts; anything else → no-op
LANG_VAR  = "EMO_LANG"             # e.g., "en", "es"

# Valid values for validation
VALID_SIDES = {"buy", "sell"}
VALID_ORDER_TYPES = {"market", "limit"}
VALID_TIME_IN_FORCE = {"day", "gtc", "ioc", "fok"}

# ---- i18n helpers ---------------------------------------------------------
from i18n.lang import t

def _now_iso() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()

def _digest(payload: Dict[str, Any]) -> str:
    """Generate SHA256 digest for order integrity."""
    h = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode())
    return h.hexdigest()[:16]

def _validate_order_params(symbol: str, side: str, qty: float, order_type: str, 
                          limit_price: Optional[float], lang: str) -> List[str]:
    """
    Validate order parameters and return list of errors.
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Validate symbol
    if not symbol or not symbol.strip():
        errors.append(t("invalid_symbol", lang, symbol=symbol))
    
    # Validate side
    if side.lower() not in VALID_SIDES:
        errors.append(t("invalid_side", lang, side=side))
    
    # Validate quantity
    if qty <= 0:
        errors.append(t("invalid_quantity", lang, qty=qty))
    
    # Validate order type
    if order_type.lower() not in VALID_ORDER_TYPES:
        errors.append(t("invalid_order_type", lang, order_type=order_type))
    
    # Validate limit price for limit orders
    if order_type.lower() == "limit" and (limit_price is None or limit_price <= 0):
        errors.append(t("missing_limit_price", lang))
    
    return errors

class StageOrderClient:
    """
    Safe "paper staging" client. If EMO_STAGE_ORDERS != "1", calls are a no-op.
    Otherwise writes signed order drafts to ops/orders/drafts.
    """
    
    def __init__(self, enabled: Optional[bool] = None, lang: Optional[str] = None):
        """
        Initialize the staging client.
        
        Args:
            enabled: Override the environment variable setting
            lang: Language for messages (defaults to EMO_LANG env var)
        """
        if enabled is None:
            enabled = os.getenv(STAGE_VAR, "").strip() == "1"
        self.enabled = enabled
        self.lang = (lang or os.getenv(LANG_VAR, "en")).lower()
        
        # Ensure drafts directory exists
        DRAFTS_DIR.mkdir(parents=True, exist_ok=True)

    def stage_order(self,
                    symbol: str,
                    side: str,              # "buy" | "sell"
                    qty: float,
                    order_type: str,        # "market" | "limit"
                    time_in_force: str = "day",
                    limit_price: Optional[float] = None,
                    strategy: Optional[str] = None,
                    meta: Optional[Dict[str, Any]] = None,
                    out_format: str = "yaml"  # "yaml" | "json"
                    ) -> Optional[Path]:
        """
        Write an order draft file OR do nothing if staging disabled.
        
        Args:
            symbol: Trading symbol (e.g., "SPY", "AAPL")
            side: Order side ("buy" or "sell")
            qty: Quantity to trade
            order_type: Order type ("market" or "limit")
            time_in_force: Time in force ("day", "gtc", "ioc", "fok")
            limit_price: Limit price (required for limit orders)
            strategy: Trading strategy name
            meta: Additional metadata
            out_format: Output format ("yaml" or "json")
            
        Returns:
            Path to created draft file, or None if staging disabled
        """
        if not self.enabled:
            print(t("staging_disabled", self.lang))
            return None

        try:
            # Validate parameters
            errors = _validate_order_params(symbol, side, qty, order_type, limit_price, self.lang)
            if errors:
                for error in errors:
                    print(error)
                return None

            # Normalize inputs
            symbol = symbol.upper().strip()
            side = side.lower().strip()
            order_type = order_type.lower().strip()
            time_in_force = time_in_force.lower().strip()

            # Create draft order
            draft: Dict[str, Any] = {
                "schema": "emo_order_draft/v1",
                "created_ts": _now_iso(),
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "order_type": order_type,
                "time_in_force": time_in_force,
                "limit_price": limit_price,
                "strategy": strategy,
                "meta": meta or {},
                "language": self.lang,
                "status": "DRAFT",  # DRAFT -> APPROVED -> EXECUTED (out of band flow)
                "created_by": "emo_stage_order_client",
                "version": "1.0.0"
            }

            # Add a signature so drafts are tamper-evident
            draft["signature"] = _digest(draft)

            # Generate filename
            ts = int(time.time())
            uid = uuid.uuid4().hex[:8]
            fname = f"{ts}_{symbol}_{side}_{uid}"
            
            # Write file based on format
            if out_format.lower() == "json" or not _HAS_YAML:
                if out_format.lower() == "yaml" and not _HAS_YAML:
                    print(t("yaml_missing", self.lang))
                    
                path = DRAFTS_DIR / f"{fname}.json"
                path.write_text(json.dumps(draft, indent=2, default=str), encoding="utf-8")
            else:
                path = DRAFTS_DIR / f"{fname}.yaml"
                import yaml  # local import to satisfy linters
                with open(path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(draft, f, sort_keys=False, allow_unicode=True)

            print(t("draft_written", self.lang, path=str(path)))
            print(t("order_staged", self.lang))
            return path
            
        except Exception as e:
            print(t("staging_error", self.lang, error=str(e)))
            return None

    def list_drafts(self) -> List[Path]:
        """
        List all draft order files.
        
        Returns:
            List of paths to draft files
        """
        if not self.enabled:
            return []
            
        return list(DRAFTS_DIR.glob("*.yaml")) + list(DRAFTS_DIR.glob("*.json"))

    def load_draft(self, path: Path) -> Optional[Dict[str, Any]]:
        """
        Load and validate a draft order file.
        
        Args:
            path: Path to draft file
            
        Returns:
            Draft order data if valid, None otherwise
        """
        try:
            if path.suffix == ".yaml" and _HAS_YAML:
                import yaml
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
            else:
                data = json.loads(path.read_text(encoding="utf-8"))
            
            # Validate signature
            stored_sig = data.pop("signature", None)
            calculated_sig = _digest(data)
            data["signature"] = stored_sig  # Restore for return
            
            if stored_sig != calculated_sig:
                print(f"⚠️  Warning: Draft {path.name} signature mismatch")
                
            return data
            
        except Exception as e:
            print(f"❌ Error loading draft {path.name}: {e}")
            return None

    def clean_old_drafts(self, days: int = 7) -> int:
        """
        Clean up draft files older than specified days.
        
        Args:
            days: Number of days to keep drafts
            
        Returns:
            Number of files cleaned up
        """
        if not self.enabled:
            return 0
            
        cutoff = time.time() - (days * 24 * 3600)
        cleaned = 0
        
        for draft_file in self.list_drafts():
            try:
                if draft_file.stat().st_mtime < cutoff:
                    draft_file.unlink()
                    cleaned += 1
            except Exception:
                pass  # Ignore errors during cleanup
                
        return cleaned

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about staged orders.
        
        Returns:
            Dictionary with statistics
        """
        if not self.enabled:
            return {"enabled": False}
            
        drafts = self.list_drafts()
        stats = {
            "enabled": True,
            "total_drafts": len(drafts),
            "yaml_files": len([f for f in drafts if f.suffix == ".yaml"]),
            "json_files": len([f for f in drafts if f.suffix == ".json"]),
            "drafts_dir": str(DRAFTS_DIR),
            "language": self.lang
        }
        
        # Analyze by symbol and side
        symbols = {}
        sides = {"buy": 0, "sell": 0}
        
        for draft_file in drafts:
            try:
                data = self.load_draft(draft_file)
                if data:
                    symbol = data.get("symbol", "UNKNOWN")
                    side = data.get("side", "unknown")
                    
                    symbols[symbol] = symbols.get(symbol, 0) + 1
                    if side in sides:
                        sides[side] += 1
            except Exception:
                pass
                
        stats["by_symbol"] = symbols
        stats["by_side"] = sides
        
        return stats

# Convenience functions for easy use
def stage_market_order(symbol: str, side: str, qty: float, **kwargs) -> Optional[Path]:
    """Stage a market order."""
    client = StageOrderClient()
    return client.stage_order(symbol, side, qty, "market", **kwargs)

def stage_limit_order(symbol: str, side: str, qty: float, limit_price: float, **kwargs) -> Optional[Path]:
    """Stage a limit order."""
    client = StageOrderClient()
    return client.stage_order(symbol, side, qty, "limit", limit_price=limit_price, **kwargs)

def get_staging_stats() -> Dict[str, Any]:
    """Get staging statistics."""
    client = StageOrderClient()
    return client.get_stats()