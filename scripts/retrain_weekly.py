import os, importlib, sys, traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

def main(symbols=None):
    symbols = [s.strip().upper() for s in (symbols or os.getenv("EMO_SYMBOLS","SPY,QQQ").split(",")) if s.strip()]
    try:
        train = importlib.import_module("train_ml")  # your Phase 2 training script
    except Exception:
        print("train_ml.py not found; weekly retrain skipped.")
        return
    for sym in symbols:
        try:
            print(f"[retrain_weekly] training {sym}…")
            # expected signature: train.run(symbol="SPY")
            if hasattr(train, "run"):
                train.run(symbol=sym)
            elif hasattr(train, "main"):
                train.main([sym])
            else:
                print("train_ml has no run/main entrypoint; please adapt.")
        except Exception:
            traceback.print_exc()

if __name__ == "__main__":
    main()