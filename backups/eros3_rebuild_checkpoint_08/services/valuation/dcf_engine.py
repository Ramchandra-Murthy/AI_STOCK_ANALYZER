from __future__ import annotations

from typing import Any

from domain.valuation.result import (
    ValuationResult,
    ValuationMethod,
    ValuationStatus,
)

from services.valuation.base_engine import BaseValuationEngine


class DCFValuationEngine(BaseValuationEngine):
    """
    Adapter for the canonical DCF valuation engine.

    EROS may provide either:
    1. A complete DCFInput instance, or
    2. A dictionary containing a DCF payload.

    The adapter deliberately strips orchestration-only keys such as
    dcf_segments before constructing DCFInput.
    """

    def __init__(self) -> None:
        super().__init__()

    @property
    def valuation_method(self) -> str:
        return ValuationMethod.DCF.value

    def value(self, data: Any) -> ValuationResult:
        from services.valuation.dcf import DCFInput, DCFModel

        if isinstance(data, DCFInput):
            dcf_input = data

        elif isinstance(data, dict):
            payload = dict(data)

            dcf_segments = payload.get("dcf_segments")

            if isinstance(dcf_segments, list) and dcf_segments:
                segment = dcf_segments[0]

                if isinstance(segment, dict):
                    merged = dict(segment)

                    for key, value in payload.items():
                        if key not in {
                            "dcf_segments",
                            "other_segments",
                            "holdco_discount",
                            "provenance",
                        }:
                            merged.setdefault(key, value)

                    payload = merged

            excluded_keys = {
                "dcf_segments",
                "other_segments",
                "holdco_discount",
                "provenance",
                "status",
                "warnings",
                "source",
                "data",
            }

            for key in excluded_keys:
                payload.pop(key, None)

            if "ebit_margins" in payload and "ebit_margin_forecast" not in payload:
                payload["ebit_margin_forecast"] = payload.pop("ebit_margins")

            if (
                "working_capital_ratios" in payload
                and "nwc_pct_rev" not in payload
            ):
                payload["nwc_pct_rev"] = payload.pop(
                    "working_capital_ratios"
                )

            payload.setdefault(
                "company_name",
                payload.get("symbol", "Target Co"),
            )
            payload.setdefault("currency", "INR")

            payload.setdefault(
                "last_historical_revenue",
                payload.get("revenue", 1000.0),
            )

            payload.setdefault("revenue_growth_rates", [0.08] * 5)
            payload.setdefault("ebit_margin_forecast", [0.20] * 5)
            payload.setdefault("capex_pct_rev", [0.05] * 5)
            payload.setdefault("nwc_pct_rev", [0.02] * 5)
            payload.setdefault("dna_pct_rev", [0.03] * 5)

            payload.setdefault("tax_rate", 0.25)
            payload.setdefault("cost_of_equity", 0.12)
            payload.setdefault("cost_of_debt_post_tax", 0.06)
            payload.setdefault("equity_weight", 0.80)
            payload.setdefault("debt_weight", 0.20)
            payload.setdefault("terminal_growth_rate", 0.03)

            payload.setdefault("total_debt", 0.0)
            payload.setdefault("cash_and_equivalents", 0.0)
            payload.setdefault("shares_outstanding", 1.0)
            payload.setdefault("minority_interest", 0.0)
            payload.setdefault("preferred_stock", 0.0)

            dcf_fields = {
                "company_name",
                "currency",
                "last_historical_revenue",
                "revenue_growth_rates",
                "ebit_margin_forecast",
                "capex_pct_rev",
                "nwc_pct_rev",
                "dna_pct_rev",
                "tax_rate",
                "cost_of_equity",
                "cost_of_debt_post_tax",
                "equity_weight",
                "debt_weight",
                "terminal_growth_rate",
                "total_debt",
                "cash_and_equivalents",
                "shares_outstanding",
                "minority_interest",
                "preferred_stock",
            }

            dcf_payload = {
                key: value
                for key, value in payload.items()
                if key in dcf_fields
            }

            dcf_input = DCFInput(**dcf_payload)

        else:
            raise TypeError(
                "DCFValuationEngine requires DCFInput or dict payload; "
                f"received {type(data).__name__}"
            )

        dcf_input.validate()

        model = DCFModel(dcf_input)
        result = model.run_model()

        return ValuationResult(
            method=ValuationMethod.DCF,
            enterprise_value=result.enterprise_value,
            equity_value=result.equity_value,
            implied_share_price=result.implied_share_price,
            status=ValuationStatus.SUCCESS,
            details={
                "company_name": dcf_input.company_name,
                "currency": dcf_input.currency,
                "wacc": result.wacc,
                "terminal_value_pct": result.terminal_value_pct_of_ev,
                "forecast_years": result.forecast_period,
                "notes": "Evaluated successfully via modular DCF engine",
            },
        )

    def evaluate(self, data: Any) -> ValuationResult:
        """Backward-compatible alias for value()."""
        return self.value(data)


DCFEngine = DCFValuationEngine
