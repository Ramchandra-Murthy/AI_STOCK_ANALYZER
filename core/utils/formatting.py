from __future__ import annotations

from decimal import Decimal
from core.utils.rounding import round_currency

def format_currency(amount: float | Decimal, currency_symbol: str = "₹") -> str:
    """Format a numeric amount into a readable currency string."""
    rounded = round_currency(amount)
    return f"{currency_symbol}{rounded:,.2f}"
