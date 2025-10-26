"""
PositionSizer: volatility- & risk-based sizing helpers.

Includes:
- Equity sizing using rolling volatility or ATR-like measure
- Options credit-spread sizing using (width - credit) max loss
- Correlation-aware adjustment (scales down if basket is concentrated)

All functions are pure and require callers to supply equity, series, etc.
"""

from __future__ import annotations
from typing import Iterable, Dict, Optional, List
import math
import statistics

def _pct_returns(prices: Iterable[float]) -> List[float]:
    prices = list(prices)
    out = []
    for i in range(1, len(prices)):
        if prices[i-1] != 0:
            out.append((prices[i] - prices[i-1]) / prices[i-1])
    return out

def equity_size_by_vol(
    prices: Iterable[float],
    equity: float,
    per_position_risk: float = 0.01,
    vol_lookback: int = 20,
    price_now: Optional[float] = None,
    min_shares: int = 1
) -> int:
    """
    Sizing rule of thumb:
      risk_budget = per_position_risk * equity
      daily_vol   = stdev(returns_{lookback})
      $vol_per_share ~= price_now * daily_vol
      shares      = risk_budget / $vol_per_share
    """
    prices = list(prices)
    if len(prices) < max(vol_lookback, 2):
        return 0
    returns = _pct_returns(prices[-(vol_lookback+1):])
    if not returns:
        return 0
    stdev = statistics.pstdev(returns) or 0.0
    px = prices[-1] if price_now is None else price_now
    if stdev <= 0.0 or px <= 0.0:
        return 0
    risk_budget = per_position_risk * equity
    vol_per_share = px * stdev
    raw = int(math.floor(risk_budget / max(vol_per_share, 1e-9)))
    return max(min_shares, raw) if raw > 0 else 0

def credit_spread_contracts(
    credit_per_contract: float,
    width: float,
    equity: float,
    per_position_risk: float = 0.01,
    contract_multiplier: int = 100,
    max_contracts: int = 10
) -> int:
    """
    Max loss per contract (credit spread) ~= (width - credit) * multiplier
    Contracts = floor( risk_budget / max_loss_per_contract )
    """
    risk_budget = per_position_risk * equity
    max_loss_per = (width - credit_per_contract) * contract_multiplier
    if max_loss_per <= 0:
        return 0
    c = int(math.floor(risk_budget / max_loss_per))
    return max(0, min(max_contracts, c))

def correlation_scale(
    base_size: int,
    avg_corr_to_book: Optional[float],
    corr_soft_cap: float = 0.80,
    min_scale: float = 0.25,
) -> int:
    """
    If basket is highly correlated, scale size down.
    Example:
      avg_corr_to_book=0.9 => scale ~ 0.5
    """
    if avg_corr_to_book is None:
        return base_size
    if avg_corr_to_book <= corr_soft_cap:
        return base_size
    # linear scale from cap..1.0 -> 1.0..min_scale
    span = max(1e-6, 1.0 - corr_soft_cap)
    t = min(1.0, max(0.0, (avg_corr_to_book - corr_soft_cap) / span))
    scale = 1.0 - t * (1.0 - min_scale)
    return max(0, int(math.floor(base_size * scale)))