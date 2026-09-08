from __future__ import annotations

import logging
from typing import Any, Dict, List

from services.execution.models import ExecutionOrder

logger = logging.getLogger(__name__)


class InstitutionalExecutionEngine:
    """Transforms validated rebalance targets into cost-aware execution orders."""

    @staticmethod
    def generate_orders(
        allocations: List[Dict[str, Any]],
        execution_policy: str = "VWAP-oriented",
        aum_baseline: float = 100000000.0,
    ) -> List[ExecutionOrder]:
        if aum_baseline <= 0:
            raise ValueError("aum_baseline must be positive")

        logger.info(
            "Generating execution orders for %d allocations under policy '%s'",
            len(allocations),
            execution_policy,
        )

        orders: List[ExecutionOrder] = []

        for alloc in allocations:
            symbol = str(alloc.get("symbol", "")).strip().upper()
            action = str(alloc.get("action", "BUY")).strip().upper()
            weight = float(alloc.get("trade_weight", 0.05))

            if not symbol:
                raise ValueError("Execution allocation is missing symbol")
            if action not in {"BUY", "SELL", "HOLD"}:
                raise ValueError(f"{symbol}: unsupported execution action {action}")
            if weight < 0:
                raise ValueError(f"{symbol}: trade_weight cannot be negative")

            market_price = alloc.get("current_price")
            try:
                market_price = float(market_price)
            except (TypeError, ValueError):
                market_price = 0.0

            if action in {"BUY", "SELL"} and market_price <= 0:
                raise ValueError(
                    f"{symbol}: positive live current_price is required; "
                    "no synthetic execution price is permitted"
                )

            if action == "HOLD":
                quantity = 0.0
                limit_price = market_price if market_price > 0 else 0.0
            else:
                notional_value = weight * aum_baseline
                quantity = round(notional_value / market_price, 2)
                limit_price = (
                    round(market_price * 0.998, 2)
                    if action == "BUY"
                    else round(market_price * 1.002, 2)
                )

            slippage = round(market_price * 0.0012, 2)
            tca_cost = round(
                (weight * aum_baseline) * 0.0005,
                2,
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
                        "Generated via portfolio optimization rebalance target",
                        f"Executed under institutional policy: {execution_policy}",
                    ],
                    metadata={
                        "market_price_source": alloc.get(
                            "market_price_source",
                            "canonical-market-data",
                        ),
                        "market_data_state": alloc.get(
                            "market_data_state",
                            "UNKNOWN",
                        ),
                        "synthetic_price_used": False,
                    },
                )
            )

        return orders
