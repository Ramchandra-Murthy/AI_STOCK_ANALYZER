"""Risk-based position sizing."""

from __future__ import annotations


def atr_position_size(
    capital: float,
    risk_fraction: float,
    entry_price: float,
    atr: float,
    atr_multiple: float = 1.5,
) -> int:
    """Size a position so an ATR stop represents fixed account risk."""
    if capital <= 0 or risk_fraction <= 0:
        return 0
    if entry_price <= 0 or atr <= 0 or atr_multiple <= 0:
        return 0

    risk_budget = capital * risk_fraction
    risk_per_share = atr * atr_multiple
    return max(0, int(risk_budget // risk_per_share))
