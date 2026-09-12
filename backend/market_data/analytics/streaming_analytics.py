from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class StreamingAnalyticsEngine:
    """Computes real-time technical indicators on incoming normalized tick streams."""

    @staticmethod
    def calculate_tick_metrics(history: list[float], current_price: float) -> dict[str, Any]:
        prices = history + [current_price]
        sma = sum(prices) / len(prices)

        # Simple momentum estimation
        momentum = current_price - prices[0]
        volatility = max(prices) - min(prices)

        return {
            "current_price": current_price,
            "sma": round(sma, 2),
            "momentum": round(momentum, 2),
            "volatility": round(volatility, 2),
            "tick_count": len(prices),
        }
