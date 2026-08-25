from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from services.valuation.dcf import DCFInput, DCFModel, DCFResult


@dataclass(frozen=True)
class SOTPSegmentResult:
    segment_name: str
    valuation_method: str  # e.g., "DCF", "EV/EBITDA", "Book Value"
    enterprise_value: float
    equity_value: float
    net_debt: float
    weight: float = 1.00
    notes: str = ""


@dataclass(frozen=True)
class SOTPValuationOutput:
    company_name: str
    segments: list[SOTPSegmentResult]
    total_enterprise_value: float
    total_equity_value: float
    implied_share_price: float
    shares_outstanding: float
    diagnostics: dict[str, Any] = field(default_factory=dict)


class SOTPLongTermValuationService:
    """Enterprise-grade Sum-of-the-Parts (SOTP) Valuation Service."""

    def __init__(self, company_name: str, shares_outstanding: float):
        self.company_name = company_name
        self.shares_outstanding = shares_outstanding

    def evaluate_dcf_segment(self, segment_params: dict[str, Any]) -> SOTPSegmentResult:
        """
        Translate legacy SOTP segment parameters into the modern DCFInput contract.

        Compatibility is intentionally preserved:
        - Modern keys take precedence.
        - Legacy EBIT / working-capital keys remain accepted.
        - Legacy net_debt remains accepted.
        - Explicit total_debt / cash_and_equivalents take precedence
          over net_debt when supplied.
        """

        # -------------------------------------------------------------
        # LEGACY -> MODERN OPERATING DRIVER BRIDGE
        # -------------------------------------------------------------
        ebit_margin_forecast = segment_params.get(
            "ebit_margin_forecast",
            segment_params.get(
                "ebit_margins",
                [0.20, 0.20, 0.22, 0.22, 0.25],
            ),
        )

        nwc_pct_rev = segment_params.get(
            "nwc_pct_rev",
            segment_params.get(
                "working_capital_ratios",
                [0.02] * 5,
            ),
        )

        capex_pct_rev = segment_params.get(
            "capex_pct_rev",
            [0.05] * 5,
        )

        dna_pct_rev = segment_params.get(
            "dna_pct_rev",
            [0.03] * 5,
        )

        # -------------------------------------------------------------
        # DEBT / CASH BRIDGE
        # -------------------------------------------------------------
        if (
            "total_debt" in segment_params
            or "cash_and_equivalents" in segment_params
        ):
            total_debt = segment_params.get("total_debt", 0.0)
            cash_and_equivalents = segment_params.get(
                "cash_and_equivalents",
                0.0,
            )
        else:
            net_debt = segment_params.get("net_debt", 0.0)

            total_debt = max(0.0, net_debt)
            cash_and_equivalents = max(0.0, -net_debt)

        # -------------------------------------------------------------
        # MODERN DCF INPUT
        # -------------------------------------------------------------
        dcf_input = DCFInput(
            company_name=segment_params.get(
                "segment_name",
                self.company_name,
            ),
            currency=segment_params.get(
                "currency",
                "INR",
            ),
            last_historical_revenue=segment_params.get(
                "last_historical_revenue",
                1000.0,
            ),
            revenue_growth_rates=segment_params.get(
                "revenue_growth_rates",
                [0.10, 0.10, 0.08, 0.08, 0.06],
            ),
            ebit_margin_forecast=ebit_margin_forecast,
            capex_pct_rev=capex_pct_rev,
            nwc_pct_rev=nwc_pct_rev,
            dna_pct_rev=dna_pct_rev,
            tax_rate=segment_params.get(
                "tax_rate",
                0.25,
            ),
            cost_of_equity=segment_params.get(
                "cost_of_equity",
                0.12,
            ),
            cost_of_debt_post_tax=segment_params.get(
                "cost_of_debt_post_tax",
                0.05,
            ),
            equity_weight=segment_params.get(
                "equity_weight",
                0.80,
            ),
            debt_weight=segment_params.get(
                "debt_weight",
                0.20,
            ),
            terminal_growth_rate=segment_params.get(
                "terminal_growth_rate",
                0.04,
            ),
            total_debt=total_debt,
            cash_and_equivalents=cash_and_equivalents,
            shares_outstanding=segment_params.get(
                "shares_outstanding",
                self.shares_outstanding,
            ),
        )

        # -------------------------------------------------------------
        # VALIDATE BEFORE MODEL EXECUTION
        # -------------------------------------------------------------
        dcf_input.validate()

        # Modern DCF engine execution path.
        dcf_model = DCFModel(dcf_input)
        dcf_result: DCFResult = dcf_model.run_model()

        # -------------------------------------------------------------
        # ENTERPRISE -> EQUITY BRIDGE
        # -------------------------------------------------------------
        ev = dcf_result.enterprise_value
        net_debt = total_debt - cash_and_equivalents
        equity_val = ev - net_debt

        return SOTPSegmentResult(
            segment_name=segment_params.get(
                "segment_name",
                "Core Segment",
            ),
            valuation_method="DCF",
            enterprise_value=ev,
            equity_value=equity_val,
            net_debt=net_debt,
            weight=segment_params.get(
                "weight",
                1.0,
            ),
            notes="Evaluated via modern EROS DCF engine with legacy-to-modern bridge",
        )

    def evaluate_sotp(
        self,
        dcf_segments_raw: list[dict[str, Any]],
        other_segments_raw: list[dict[str, Any]] | None = None,
        holdco_discount: float = 0.0,
    ) -> SOTPValuationOutput:
        segment_results: list[SOTPSegmentResult] = []
        sum_enterprise_value = 0.0
        sum_equity_value = 0.0

        for seg in dcf_segments_raw:
            res = self.evaluate_dcf_segment(seg)
            segment_results.append(res)
            sum_enterprise_value += res.enterprise_value * res.weight
            sum_equity_value += res.equity_value * res.weight

        if other_segments_raw:
            for seg in other_segments_raw:
                ev = seg.get("enterprise_value", 0.0)
                nd = seg.get("net_debt", 0.0)
                eq = ev - nd
                wt = seg.get("weight", 1.0)
                res = SOTPSegmentResult(
                    segment_name=seg.get("segment_name", "Other Segment"),
                    valuation_method=seg.get("valuation_method", "Comparable / NAV"),
                    enterprise_value=ev,
                    equity_value=eq,
                    net_debt=nd,
                    weight=wt,
                    notes=seg.get("notes", ""),
                )
                segment_results.append(res)
                sum_enterprise_value += ev * wt
                sum_equity_value += eq * wt

        if holdco_discount > 0.0:
            sum_equity_value *= 1.0 - holdco_discount

        implied_price = (
            sum_equity_value / self.shares_outstanding
            if self.shares_outstanding > 0
            else 0.0
        )

        return SOTPValuationOutput(
            company_name=self.company_name,
            segments=segment_results,
            total_enterprise_value=sum_enterprise_value,
            total_equity_value=sum_equity_value,
            implied_share_price=implied_price,
            shares_outstanding=self.shares_outstanding,
            diagnostics={
                "holdco_discount_applied": holdco_discount,
                "segment_count": len(segment_results),
            },
        )
