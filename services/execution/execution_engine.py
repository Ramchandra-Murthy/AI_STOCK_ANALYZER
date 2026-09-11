from __future__ import annotations

import logging
from typing import Any

from services.execution.models import ExecutionOrder

logger = logging.getLogger(__name__)


class InstitutionalExecutionEngine:
    """Transform validated portfolio rebalance targets into execution orders."""

    @staticmethod
    def generate_orders(
        allocations: list[dict[str, Any]],
        execution_policy: str = "VWAP-oriented",
        aum_baseline: float = 100_000_000.0,
    ) -> list[ExecutionOrder]:
        if aum_baseline <= 0:
            raise ValueError("aum_baseline must be positive")

        orders: list[ExecutionOrder] = []
        logger.info(
            "Generating execution orders for %d allocations under policy '%s'",
            len(allocations),
            execution_policy,
        )
        for alloc in allocations:
            symbol = str(alloc.get("symbol", "")).strip().upper()
            action = str(alloc.get("action", "")).strip().upper()
            weight = float(alloc.get("trade_weight", 0.0))
            market_price_raw = alloc.get("current_price")

            if not symbol:
                raise ValueError("allocation symbol is required")
            if action not in {"BUY", "SELL", "HOLD"}:
                raise ValueError(f"unsupported execution action: {action}")
            if weight < 0:
                raise ValueError("trade_weight cannot be negative")
            if action == "HOLD" or weight == 0:
                continue
            if not isinstance(market_price_raw, (int, float)) or float(market_price_raw) <= 0:
                raise ValueError(f"positive current_price is required for {symbol}")

            market_price = float(market_price_raw)
            notional_value = weight * aum_baseline
            quantity = round(notional_value / market_price, 2)
            if quantity <= 0:
                raise ValueError(f"trade weight produces no executable quantity for {symbol}")

            slippage = round(market_price * 0.0012, 2)
            tca_cost = round(notional_value * 0.0005, 2)
            limit_price = (
                round(market_price * 0.998, 2)
                if action == "BUY"
                else round(market_price * 1.002, 2)
            )

            orders.append(
                ExecutionOrder(
                    symbol=symbol,
                    action=action,
                    quantity=quantity,
                    limit_price=limit_price,
                    execution_priority="NORMAL",
                    estimated_slippage=slippage,
                    estimated_transaction_cost=tca_cost,
                    rationale=[
                        "Generated from a validated portfolio rebalance target.",
                        f"Executed under institutional policy: {execution_policy}",
                    ],
                )
            )

        return orders
