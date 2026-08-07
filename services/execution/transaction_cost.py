from __future__ import annotations

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class TransactionCostAnalyzer:
    """Computes comprehensive transaction cost analysis (TCA) including brokerage, exchange fees, taxes, and market impact."""

    @staticmethod
    def analyze_order_costs(notional_value: float, order_size_pct_adv: float) -> Dict[str, float]:
        logger.info("Performing TCA for order notional value: %.2f (ADV participation: %.2f%%)", notional_value, order_size_pct_adv * 100)

        brokerage = notional_value * 0.0003
        exchange_fees = notional_value * 0.000035
        taxes = notional_value * 0.001 # STT / GST estimates
        market_impact = notional_value * (0.001 * (1.0 + order_size_pct_adv * 5.0))

        total_cost = brokerage + exchange_fees + taxes + market_impact

        return {
            "brokerage": round(brokerage, 2),
            "exchange_fees": round(exchange_fees, 2),
            "taxes": round(taxes, 2),
            "market_impact": round(market_impact, 2),
            "total_transaction_cost": round(total_cost, 2)
        }
