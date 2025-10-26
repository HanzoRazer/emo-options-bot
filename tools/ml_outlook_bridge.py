# tools/ml_outlook_bridge.py
import json, os, sys, datetime as dt, importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT  = ROOT / "ops" / "ml_outlook.json"

DEFAULT_SYMBOLS = os.getenv("EMO_SYMBOLS", "SPY,QQQ").split(",")

def _safe_float(x, default=None):
    try:
        return float(x)
    except Exception:
        return default

def main(symbols=None):
    symbols = [s.strip().upper() for s in (symbols or DEFAULT_SYMBOLS) if s.strip()]
    result = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "symbols": []
    }

    # Try to import your ML predictor (predict_ml.py with function predict_symbols)
    predict_mod = None
    try:
        sys.path.insert(0, str(ROOT))
        predict_mod = importlib.import_module("predict_ml")
    except Exception:
        predict_mod = None

    for sym in symbols:
        outlook = {
            "symbol": sym,
            "horizon": "1d",
            "trend": "unknown",
            "confidence": None,
            "expected_return": None,
            "notes": ""
        }
        if predict_mod and hasattr(predict_mod, "predict_symbols"):
            try:
                # expect dict like: { 'SPY': {'trend':'up','confidence':0.73,'expected_return':0.004} }
                batch = predict_mod.predict_symbols(symbols=[sym], horizon="1d")
                data = batch.get(sym, {})
                outlook["trend"] = data.get("trend", "flat")
                outlook["confidence"] = _safe_float(data.get("confidence"))
                outlook["expected_return"] = _safe_float(data.get("expected_return"))
            except Exception as e:
                outlook["notes"] = f"predict_ml error: {e}"
        else:
            outlook["notes"] = "predict_ml not found; using placeholder"
            outlook["trend"] = "flat"
            outlook["confidence"] = 0.50
            outlook["expected_return"] = 0.0

        result["symbols"].append(outlook)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"[ml_outlook_bridge] wrote {OUT}")

if __name__ == "__main__":
    main()