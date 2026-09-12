from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class PortfolioRebalancer:
    """Generates optimal trade lists to transition current portfolio weights to target institutional allocations."""

    @staticmethod
    def generate_rebalance_trades(
        current_weights: dict[str, float], target_weights: dict[str, float]
    ) -> list[dict[str, Any]]:
        logger.info("Generating rebalance trade list with minimal turnover")
        trades = []
        all_symbols = set(current_weights.keys()).union(set(target_weights.keys()))

        for symbol in all_symbols:
            curr = current_weights.get(symbol, 0.0)
            target = target_weights.get(symbol, 0.0)
            diff = target - curr

            if abs(diff) > 0.005:  # Threshold for rebalancing action
                action = "BUY" if diff > 0 else "SELL"
                trades.append(
                    {
                        "symbol": symbol,
                        "action": action,
                        "trade_weight": round(abs(diff), 4),
                        "current_weight": curr,
                        "target_weight": target,
                    }
                )

        return trades
