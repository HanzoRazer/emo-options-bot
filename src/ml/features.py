"""
EMO Options Bot - ML Features
Technical analysis and feature engineering for machine learning
"""

import numpy as np
import pandas as pd

def add_core_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add technical analysis features to price data
    
    Args:
        df: DataFrame with columns ['close','high','low','open','volume'] indexed by datetime
        
    Returns:
        DataFrame with additional technical features
    """
    out = df.copy()
    
    # Returns
    out['returns_1'] = out['close'].pct_change(1)
    out['returns_5'] = out['close'].pct_change(5)
    
    # Volatility
    out['vol_10'] = out['returns_1'].rolling(10).std().fillna(0.0)
    out['realized_vol_20'] = out['returns_1'].rolling(20).std().fillna(0.0)
    
    # RSI (Relative Strength Index) - 14 period
    chg = out['close'].diff()
    gain = chg.clip(lower=0).rolling(14).mean()
    loss = (-chg.clip(upper=0)).rolling(14).mean()
    rs = (gain / (loss.replace(0, np.nan))).fillna(0)
    out['rsi_14'] = 100 - (100 / (1 + rs))
    
    # MACD (Moving Average Convergence Divergence) - 12,26,9
    ema12 = out['close'].ewm(span=12, adjust=False).mean()
    ema26 = out['close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    out['macd'] = macd - signal
    
    # VIX placeholder if not available
    if 'vix' not in out.columns:
        out['vix'] = 0.0
    
    return out

def build_supervised(
    df: pd.DataFrame,
    features: list[str],
    horizon: int,
    target_name: str | None = None
):
    """
    Create supervised learning dataset from time series data
    
    Args:
        df: Price data DataFrame
        features: List of feature column names to use
        horizon: Forward-looking periods for target
        target_name: Name for target variable
        
    Returns:
        Tuple of (X, y, index) where X is features, y is targets, index is time index
    """
    # Add technical features
    out = add_core_features(df)
    
    # Create forward-looking target (future return)
    fwd = out['close'].shift(-horizon) / out['close'] - 1.0
    y = fwd.rename(target_name or f"fwd_ret_h{horizon}")
    
    # Extract features
    X = out[features].copy()
    
    # Combine and clean data
    data = pd.concat([X, y], axis=1).dropna()
    X_clean = data[features].values.astype(np.float32)
    y_clean = data[y.name].values.astype(np.float32)
    index = data.index
    
    return X_clean, y_clean, index

def sliding_windows(X: np.ndarray, y: np.ndarray, lookback: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Convert tabular data to sliding window sequences for time series ML
    
    Args:
        X: Feature array (T, F) where T is time, F is features
        y: Target array (T,)
        lookback: Number of timesteps to look back
        
    Returns:
        Tuple of (sequences, targets) where sequences is (N, lookback, F)
    """
    seqs, targets = [], []
    for t in range(lookback, len(X)):
        seqs.append(X[t-lookback:t])
        targets.append(y[t])
    return np.array(seqs), np.array(targets)

def train_val_test_split(n: int, test=0.2, val=0.1, seed=42):
    """
    Split data indices into train/validation/test sets
    
    Args:
        n: Total number of samples
        test: Fraction for test set
        val: Fraction for validation set
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (train_idx, val_idx, test_idx)
    """
    rng = np.random.default_rng(seed)
    idx = np.arange(n)
    rng.shuffle(idx)
    
    n_test = int(n * test)
    n_val = int(n * val)
    
    test_idx = idx[:n_test]
    val_idx = idx[n_test:n_test+n_val]
    train_idx = idx[n_test+n_val:]
    
    return train_idx, val_idx, test_idx