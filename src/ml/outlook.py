"""
EMO Options Bot - ML Outlook Generation
Generates ML outlook reports and saves to JSON for dashboard consumption
"""

import json
import os
import sys
import datetime as dt
from pathlib import Path
from typing import List, Dict, Any, Optional

from .models import predict_symbols

# Configuration
ROOT = Path(__file__).resolve().parents[2]  # src/ml/ -> project root
DATA_DIR = ROOT / "data"
OUTLOOK_PATH = DATA_DIR / "ml_outlook.json"

DEFAULT_SYMBOLS = os.getenv("EMO_SYMBOLS", "SPY,QQQ").split(",")

def _safe_float(x, default=None):
    """Safely convert value to float"""
    try:
        return float(x)
    except Exception:
        return default

def generate_ml_outlook(symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Generate ML outlook for specified symbols
    
    Args:
        symbols: List of symbols to analyze (defaults to EMO_SYMBOLS)
        
    Returns:
        Dictionary containing outlook data
    """
    symbols = [s.strip().upper() for s in (symbols or DEFAULT_SYMBOLS) if s.strip()]
    
    result = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "symbols": [],
        "metadata": {
            "version": "1.0",
            "model": "ml_enhanced",
            "symbols_count": len(symbols)
        }
    }
    
    try:
        # Get ML predictions for all symbols
        predictions = predict_symbols(symbols, horizon="1d")
        
        for sym in symbols:
            prediction = predictions.get(sym, {})
            
            outlook = {
                "symbol": sym,
                "horizon": "1d",
                "trend": prediction.get("trend", "UNKNOWN").upper(),
                "confidence": _safe_float(prediction.get("confidence")),
                "expected_return": _safe_float(prediction.get("expected_return")),
                "method": prediction.get("method", "unknown"),
                "features": prediction.get("features", {}),
                "notes": prediction.get("error", "")
            }
            
            result["symbols"].append(outlook)
            
    except Exception as e:
        # Fallback if ML prediction fails
        for sym in symbols:
            outlook = {
                "symbol": sym,
                "horizon": "1d", 
                "trend": "FLAT",
                "confidence": 0.50,
                "expected_return": 0.0,
                "method": "fallback",
                "notes": f"ML prediction error: {e}"
            }
            result["symbols"].append(outlook)
    
    return result

def save_ml_outlook(outlook_data: Dict[str, Any], path: Optional[Path] = None) -> Path:
    """
    Save ML outlook data to JSON file
    
    Args:
        outlook_data: Outlook data to save
        path: Optional custom save path
        
    Returns:
        Path where data was saved
    """
    save_path = path or OUTLOOK_PATH
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(outlook_data, f, indent=2)
    
    return save_path

def load_ml_outlook(path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """
    Load ML outlook data from JSON file
    
    Args:
        path: Optional custom load path
        
    Returns:
        Outlook data or None if file doesn't exist
    """
    load_path = path or OUTLOOK_PATH
    
    try:
        with open(load_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error loading ML outlook: {e}")
        return None

def main(symbols: Optional[List[str]] = None) -> None:
    """
    Main function to generate and save ML outlook
    
    Args:
        symbols: Optional list of symbols to analyze
    """
    print("[ml_outlook] Generating ML outlook...")
    
    # Generate outlook
    outlook = generate_ml_outlook(symbols)
    
    # Save to file
    save_path = save_ml_outlook(outlook)
    
    print(f"[ml_outlook] Generated outlook for {len(outlook['symbols'])} symbols")
    print(f"[ml_outlook] Saved to: {save_path}")
    
    # Print summary
    for symbol_data in outlook["symbols"]:
        symbol = symbol_data["symbol"]
        trend = symbol_data["trend"]
        confidence = symbol_data["confidence"]
        expected_return = symbol_data["expected_return"]
        method = symbol_data["method"]
        
        print(f"  {symbol}: {trend} (conf: {confidence:.3f}, ret: {expected_return:.6f}) [{method}]")

if __name__ == "__main__":
    main()