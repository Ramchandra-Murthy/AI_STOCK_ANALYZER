from __future__ import annotations

from typing import Any

from domain.valuation.result import (
    ValuationMethod,
    ValuationResult,
    ValuationStatus,
)

from services.valuation.base_engine import BaseValuationEngine
from services.valuation.contracts import SOTPSegmentInput
from services.valuation.dcf import DCFInput, DCFModel, DCFResult


class DCFValuationEngine(BaseValuationEngine):
    """
    Canonical DCF valuation adapter.

    Converts the EROS valuation boundary input into the
    canonical DCF model input and returns the domain-level
    ValuationResult contract.
    """

    @property
    def valuation_method(self) -> str:
        return ValuationMethod.DCF.value

    def value(self, entity: Any) -> ValuationResult:
        if isinstance(entity, SOTPSegmentInput):
            dcf_input = DCFInput(
                last_historical_revenue=entity.last_historical_revenue,
                revenue_growth_rates=entity.revenue_growth_rates,
                ebit_margin_forecast=entity.ebit_margin_forecast,
                dna_pct_rev=entity.dna_pct_rev,
                capex_pct_rev=entity.capex_pct_rev,
                nwc_pct_rev=entity.nwc_pct_rev,
                tax_rate=entity.tax_rate,
                cost_of_equity=entity.cost_of_equity,
                cost_of_debt_post_tax=entity.cost_of_debt_post_tax,
                equity_weight=entity.equity_weight,
                debt_weight=entity.debt_weight,
                terminal_growth_rate=entity.terminal_growth_rate,
                total_debt=entity.segment_debt,
                cash_and_equivalents=entity.segment_cash,
                shares_outstanding=entity.shares_outstanding,
                company_name=entity.segment_name,
                currency=entity.currency,
            )

        elif isinstance(entity, DCFInput):
            dcf_input = entity

        elif isinstance(entity, dict):
            dcf_input = DCFInput(**entity)

        else:
            raise TypeError(
                "DCFValuationEngine requires SOTPSegmentInput, "
                "DCFInput, or dict payload; "
                f"received {type(entity).__name__}"
            )

        dcf_input.validate()

        dcf_result: DCFResult = DCFModel(dcf_input).run_model()

        return ValuationResult(
            method=ValuationMethod.DCF,
            enterprise_value=dcf_result.enterprise_value,
            equity_value=dcf_result.equity_value,
            implied_share_price=dcf_result.implied_share_price,
            status=ValuationStatus.SUCCESS,
            details={
                "company_name": dcf_input.company_name,
                "currency": dcf_input.currency,
                "wacc": dcf_result.wacc,
                "terminal_value_pct": dcf_result.terminal_value_pct_of_ev,
                "forecast_years": dcf_result.forecast_period,
            },
        )
