from __future__ import annotations

"""
==========================================================
SOTP AGGREGATION ENGINE
Module  : sotp_engine
Version : V1.0
==========================================================

Aggregates component valuations from ValuationDispatcher
and applies corporate net debt & HoldCo discount waterfall.
"""

from typing import Any, List
from services.valuation.dispatcher import ValuationDispatcher
from services.valuation.models import SOTPResult, ValuationResult


class SOTPEngine:
    """Aggregates multi-entity valuations into a single SOTP valuation."""

    def __init__(self, dispatcher: ValuationDispatcher):
        self.dispatcher = dispatcher

    def value(
        self,
        entities: List[Any],
        net_debt: float = 0.0,
        shares_outstanding: float = 1.0,
        holdco_discount: float = 0.0,
    ) -> SOTPResult:
        component_results: List[ValuationResult] = []
        gross_enterprise_value = 0.0
        gross_equity_value = 0.0

        for entity in entities:
            # Extract valuation method
            if isinstance(entity, dict):
                raw_method = entity.get("valuation_method", "DCF")
            elif hasattr(entity, "valuation_method"):
                raw_method = getattr(entity, "valuation_method")
            else:
                raise ValueError(f"Unable to determine valuation_method for entity: {entity}")

            # Route through dispatcher dynamically based on interface
            if hasattr(self.dispatcher, "value"):
                result = self.dispatcher.value(raw_method, entity)
            elif hasattr(self.dispatcher, "get_engine"):
                engine = self.dispatcher.get_engine(raw_method)
                result = engine.value(entity)
            elif hasattr(self.dispatcher, "dispatch"):
                result = self.dispatcher.dispatch(raw_method, entity)
            else:
                raise AttributeError("ValuationDispatcher does not expose a recognized evaluation method.")

            component_results.append(result)

            gross_enterprise_value += result.enterprise_value
            gross_equity_value += result.equity_value

        # Calculate SOTP Waterfall
        combined_equity_pre_discount = gross_equity_value - net_debt
        holdco_discount_amount = combined_equity_pre_discount * holdco_discount
        final_equity_value = combined_equity_pre_discount - holdco_discount_amount
        implied_share_price = final_equity_value / shares_outstanding if shares_outstanding > 0 else 0.0

        return SOTPResult(
            enterprise_value=gross_enterprise_value,
            equity_value=final_equity_value,
            implied_share_price=implied_share_price,
            net_debt=net_debt,
            holdco_discount_pct=holdco_discount,
            holdco_discount_amount=holdco_discount_amount,
            component_results=component_results,
        )
