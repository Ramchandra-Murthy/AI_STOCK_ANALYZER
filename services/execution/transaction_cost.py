from __future__ import annotations

import logging
from math import isfinite

logger = logging.getLogger(__name__)


class TransactionCostAnalyzer:
    """Estimate execution costs from explicit notional and ADV participation inputs."""

    @staticmethod
    def analyze_order_costs(notional_value: float, order_size_pct_adv: float) -> dict[str, float]:
        notional = float(notional_value)
        participation = float(order_size_pct_adv)
        if not isfinite(notional) or notional < 0:
            raise ValueError("notional_value must be a finite non-negative number")
        if not isfinite(participation) or participation < 0:
            raise ValueError("order_size_pct_adv must be a finite non-negative fraction")

        # These are transparent model estimates, not asserted broker fees. Callers
        # can replace the cost schedule when a venue/broker-specific schedule exists.
        brokerage = notional * 0.0003
        exchange_fees = notional * 0.000035
        taxes = notional * 0.001
        market_impact = notional * (0.001 * (1.0 + participation * 5.0))
        total_cost = brokerage + exchange_fees + taxes + market_impact

        return {
            "brokerage": round(brokerage, 2),
            "exchange_fees": round(exchange_fees, 2),
            "taxes": round(taxes, 2),
            "market_impact": round(market_impact, 2),
            "total_transaction_cost": round(total_cost, 2),
        }
