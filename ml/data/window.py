import numpy as np
from typing import Iterator, Tuple

def sliding_windows(X: np.ndarray, y: np.ndarray, lookback: int) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convert tabular (T, F) -> stacked sequences (N, lookback, F), aligned to predict y[t].
    """
    seqs, targets = [], []
    for t in range(lookback, len(X)):
        seqs.append(X[t-lookback:t])
        targets.append(y[t])
    return np.array(seqs), np.array(targets)

def train_val_test_split(n: int, test=0.2, val=0.1, seed=42):
    rng = np.random.default_rng(seed)
    idx = np.arange(n)
    rng.shuffle(idx)
    n_test = int(n * test)
    n_val  = int(n * val)
    test_idx  = idx[:n_test]
    val_idx   = idx[n_test:n_test+n_val]
    train_idx = idx[n_test+n_val:]
    return train_idx, val_idx, test_idx