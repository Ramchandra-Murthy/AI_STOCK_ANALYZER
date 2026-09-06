"""
EROS 3.0 data boundary.

This module deliberately does not implement financial mathematics.
It accepts raw financial data supplied by the caller/application and
normalizes the boundary into a predictable mapping.
"""

from typing import Any, Mapping


def require_symbol(symbol: str) -> str:
    if not symbol or not str(symbol).strip():
        raise ValueError("symbol is required")
    return str(symbol).strip().upper()


def prepare_raw_data(symbol: str, raw_data: Any = None) -> dict[str, Any]:
    symbol = require_symbol(symbol)

    if raw_data is None:
        return {
            "symbol": symbol,
            "data": {},
            "source": "caller",
        }

    if isinstance(raw_data, Mapping):
        payload = dict(raw_data)
    else:
        payload = {"value": raw_data}

    payload.setdefault("symbol", symbol)

    return {
        "symbol": symbol,
        "data": payload,
        "source": "caller",
    }


__all__ = [
    "require_symbol",
    "prepare_raw_data",
]
