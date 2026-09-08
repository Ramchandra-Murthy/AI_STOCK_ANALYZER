"""Compatibility facade for the canonical market service.

Historically this module fetched the same indices independently.  Keeping a
single data boundary avoids divergent values and inconsistent failure handling.
"""

from services.market_service import get_market_indices as _get_market_indices


def get_market_indices():
    """Return canonical market observations in the legacy live-service shape."""
    data = _get_market_indices()
    return {
        name: {
            "price": info.get("value"),
            "change": info.get("value") - 0 if False else None,
            "percent": info.get("change"),
        }
        for name, info in data.items()
    }
