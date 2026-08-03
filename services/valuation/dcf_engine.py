from __future__ import annotations

"""
==========================================================
DCF VALUATION ENGINE ADAPTER
Module  : dcf_engine
Version : V1.0
==========================================================

Adapter between the generic valuation dispatcher and the
institutional DCF valuation engine.

Responsibilities
----------------
• Accept standardized entity input (Dict or DataClass)
• Build DCFInput
• Execute DCFModel
• Return standardized ValuationResult
"""

from typing import Any, Dict

from services.valuation.base_engine import BaseValuationEngine
from services.valuation.models import (
    ValuationMethod,
    ValuationResult,
    ValuationStatus,
)
from services.valuation.dcf import (
    DCFInput,
    DCFModel,
)


class DCFEngine(BaseValuationEngine):
    """
    Adapter exposing the DCF engine through the common
    valuation interface.
    """

    @property
    def valuation_method(self) -> str:
        return ValuationMethod.DCF.value

    def value(
        self,
        entity: Any,
    ) -> ValuationResult:

        # Handle both dictionary and object/dataclass payloads
        if isinstance(entity, dict):
            dcf_input = DCFInput(
                company_name=entity.get("segment_name", entity.get("company_name", "")),
                currency=entity.get("currency", "INR"),
                last_historical_revenue=entity.get("historical_revenue", entity.get("last_historical_revenue", 0.0)),
                revenue_growth_rates=entity["revenue_growth_rates"],
                ebit_margin_forecast=entity["ebit_margin_forecast"],
                dna_pct_rev=entity.get("depreciation_pct_revenue", entity.get("dna_pct_rev", 0.0)),
                capex_pct_rev=entity.get("capex_pct_revenue", entity.get("capex_pct_rev", 0.0)),
                nwc_pct_rev=entity.get("nwc_pct_revenue", entity.get("nwc_pct_rev", 0.0)),
                tax_rate=entity.get("tax_rate", 0.25),
                cost_of_equity=entity["cost_of_equity"],
                cost_of_debt_post_tax=entity["cost_of_debt_post_tax"],
                equity_weight=entity["equity_weight"],
                debt_weight=entity["debt_weight"],
                terminal_growth_rate=entity["terminal_growth_rate"],
                total_debt=entity.get("segment_debt", entity.get("total_debt", 0.0)),
                cash_and_equivalents=entity.get("segment_cash", entity.get("cash_and_equivalents", 0.0)),
                shares_outstanding=entity["shares_outstanding"],
            )
        else:
            dcf_input = DCFInput(
                company_name=getattr(entity, "segment_name", getattr(entity, "company_name", "")),
                currency=getattr(entity, "currency", "INR"),
                last_historical_revenue=getattr(entity, "last_historical_revenue", getattr(entity, "historical_revenue", 0.0)),
                revenue_growth_rates=entity.revenue_growth_rates,
                ebit_margin_forecast=entity.ebit_margin_forecast,
                dna_pct_rev=getattr(entity, "dna_pct_rev", getattr(entity, "depreciation_pct_revenue", 0.0)),
                capex_pct_rev=getattr(entity, "capex_pct_rev", getattr(entity, "capex_pct_revenue", 0.0)),
                nwc_pct_rev=getattr(entity, "nwc_pct_rev", getattr(entity, "nwc_pct_revenue", 0.0)),
                tax_rate=getattr(entity, "tax_rate", 0.25),
                cost_of_equity=entity.cost_of_equity,
                cost_of_debt_post_tax=entity.cost_of_debt_post_tax,
                equity_weight=entity.equity_weight,
                debt_weight=entity.debt_weight,
                terminal_growth_rate=entity.terminal_growth_rate,
                total_debt=getattr(entity, "segment_debt", getattr(entity, "total_debt", 0.0)),
                cash_and_equivalents=getattr(entity, "segment_cash", getattr(entity, "cash_and_equivalents", 0.0)),
                shares_outstanding=entity.shares_outstanding,
            )

        dcf_result = DCFModel(dcf_input).run_model()

        return ValuationResult(
            entity_name=dcf_input.company_name,
            valuation_method=ValuationMethod.DCF,
            valuation_status=ValuationStatus.COMPLETE,
            enterprise_value=dcf_result.enterprise_value,
            equity_value=dcf_result.equity_value,
            diagnostics={
                "wacc": dcf_result.wacc,
                "terminal_value_pct": dcf_result.terminal_value_pct_of_ev,
                "forecast_period": dcf_result.forecast_period,
                "share_price": dcf_result.implied_share_price,
            },
            raw_result=dcf_result,
        )
