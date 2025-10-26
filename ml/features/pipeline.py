import numpy as np
import pandas as pd

def add_core_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Requires df with columns: ['close','high','low','open','volume'] indexed by datetime.
    Adds common TA-like features used by the predictive stack.
    """
    out = df.copy()
    out['returns_1'] = out['close'].pct_change(1)
    out['returns_5'] = out['close'].pct_change(5)
    out['vol_10'] = out['returns_1'].rolling(10).std().fillna(0.0)
    # RSI 14
    chg = out['close'].diff()
    gain = chg.clip(lower=0).rolling(14).mean()
    loss = (-chg.clip(upper=0)).rolling(14).mean()
    rs = (gain / (loss.replace(0, np.nan))).fillna(0)
    out['rsi_14'] = 100 - (100 / (1 + rs))
    # MACD (12,26,9)
    ema12 = out['close'].ewm(span=12, adjust=False).mean()
    ema26 = out['close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    out['macd'] = macd - signal
    out['realized_vol_20'] = out['returns_1'].rolling(20).std().fillna(0.0)
    # placeholder for VIX if available in df; else set 0
    if 'vix' not in out.columns:
        out['vix'] = 0.0
    return out

def build_supervised(
    df: pd.DataFrame,
    features: list[str],
    horizon: int,
    target_name: str | None = None
):
    """make X (features) and y (future return over horizon)."""
    out = add_core_features(df)
    fwd = out['close'].shift(-horizon) / out['close'] - 1.0
    y = fwd.rename(target_name or f"fwd_ret_h{horizon}")
    X = out[features].copy()
    data = pd.concat([X, y], axis=1).dropna()
    X, y = data[features].values.astype(np.float32), data[y.name].values.astype(np.float32)
    index = data.index
    return X, y, index