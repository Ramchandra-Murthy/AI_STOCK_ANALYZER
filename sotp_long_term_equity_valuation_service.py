from __future__ import annotations

"""
==========================================================
SUM-OF-THE-PARTS (SOTP) EQUITY VALUATION SERVICE
Module  : sotp_long_term_equity_valuation_service
Version : V1.0
==========================================================

Integrates individual segment valuation engines (DCF, Multiples, 
Asset-based) into a consolidated Sum-Of-The-Parts valuation framework.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

# Import clean public facade from DCF package
from services.valuation.dcf import DCFInput, DCFModel, DCFResult


@dataclass(slots=True)
class SOTPSegmentResult:
    """
    Container for an individual business segment's valuation outcome.
    """

    segment_name: str
    valuation_method: str  # e.g., "DCF", "EV/EBITDA", "Book Value"
    enterprise_value: float
    equity_value: float
    details: Optional[DCFResult] = None


@dataclass(slots=True)
class SOTPValuationResult:
    """
    Consolidated Sum-Of-The-Parts valuation report.
    """

    company_name: str
    segments: List[SOTPSegmentResult]
    total_enterprise_value: float
    net_debt: float
    holding_company_discount_pct: float
    consolidated_equity_value: float
    shares_outstanding: float
    implied_share_price: float


class SOTPLongTermEquityValuationService:
    """
    Orchestrates Sum-of-the-Parts (SOTP) valuation across core operations
    and non-core subsidiaries.
    """

    def __init__(self, company_name: str, shares_outstanding: float):
        self.company_name = company_name
        self.shares_outstanding = shares_outstanding

    def value_dcf_segment(self, segment_params: Dict[str, Any]) -> SOTPSegmentResult:
        """
        Adapts raw segment parameters into DCFInput, runs DCFModel,
        and returns a structured SOTPSegmentResult.
        """
        # 1. Map SOTP segment parameters into immutable DCFInput contract
        dcf_input = DCFInput(
            company_name=segment_params.get("segment_name", self.company_name),
            currency=segment_params.get("currency", "INR"),
            historical_revenue=segment_params["historical_revenue"],
            revenue_growth_rates=segment_params["revenue_growth_rates"],
            ebit_margin_forecast=segment_params["ebit_margin_forecast"],
            depreciation_pct_revenue=segment_params["depreciation_pct_revenue"],
            capex_pct_revenue=segment_params["capex_pct_revenue"],
            nwc_pct_revenue=segment_params["nwc_pct_revenue"],
            tax_rate=segment_params.get("tax_rate", 0.25),
            equity_weight=segment_params["equity_weight"],
            debt_weight=segment_params["debt_weight"],
            cost_of_equity=segment_params["cost_of_equity"],
            cost_of_debt_post_tax=segment_params["cost_of_debt_post_tax"],
            terminal_growth_rate=segment_params["terminal_growth_rate"],
            forecast_years=len(segment_params["revenue_growth_rates"]),
            total_debt=segment_params.get("segment_debt", 0.0),
            cash_and_equivalents=segment_params.get("segment_cash", 0.0),
            shares_outstanding=self.shares_outstanding,
        )

        # 2. Execute modular DCF Engine
        engine = DCFModel(dcf_input)
        dcf_result: DCFResult = engine.run_model()

        # 3. Package into standard SOTP segment format
        return SOTPSegmentResult(
            segment_name=dcf_input.company_name,
            valuation_method="DCF",
            enterprise_value=dcf_result.enterprise_value,
            equity_value=dcf_result.equity_value,
            details=dcf_result,
        )

    def evaluate_sotp(
        self,
        dcf_segments_raw: List[Dict[str, Any]],
        consolidated_debt: float,
        consolidated_cash: float,
        holding_discount_pct: float = 0.0,
    ) -> SOTPValuationResult:
        """
        Aggregates all valued business segments, applies balance sheet net debt
        and holding company discounts, and derives target share price.
        """
        segment_results: List[SOTPSegmentResult] = []
        sum_enterprise_value = 0.0

        # Run DCF valuation for each operational segment
        for raw_seg in dcf_segments_raw:
            seg_res = self.value_dcf_segment(raw_seg)
            segment_results.append(seg_res)
            sum_enterprise_value += seg_res.enterprise_value

        # Consolidated Equity Bridge
        net_debt = consolidated_debt - consolidated_cash
        gross_equity_value = sum_enterprise_value - net_debt

        # Apply Holding Company Discount (if applicable)
        net_equity_value = gross_equity_value * (1.0 - holding_discount_pct)

        # Implied Price Per Share
        target_price = (
            net_equity_value / self.shares_outstanding
            if self.shares_outstanding > 0
            else 0.0
        )

        return SOTPValuationResult(
            company_name=self.company_name,
            segments=segment_results,
            total_enterprise_value=sum_enterprise_value,
            net_debt=net_debt,
            holding_company_discount_pct=holding_discount_pct,
            consolidated_equity_value=net_equity_value,
            shares_outstanding=self.shares_outstanding,
            implied_share_price=target_price,
        )


# ==========================================================
# Example Execution / Sanity Check
# ==========================================================
if __name__ == "__main__":
    service = SOTPLongTermEquityValuationService(
        company_name="Conglomerate Corp",
        shares_outstanding=10_000_000,  # 10M shares
    )

    core_tech_segment = {
        "segment_name": "Core Software Operating Unit",
        "currency": "INR",
        "historical_revenue": [100.0, 120.0, 145.0],
        "revenue_growth_rates": [0.15, 0.12, 0.10, 0.08, 0.06],
        "ebit_margin_forecast": [0.22, 0.23, 0.24, 0.25, 0.25],
        "depreciation_pct_revenue": [0.03] * 5,
        "capex_pct_revenue": [0.04] * 5,
        "nwc_pct_revenue": [0.02] * 5,
        "tax_rate": 0.25,
        "equity_weight": 0.85,
        "debt_weight": 0.15,
        "cost_of_equity": 0.11,
        "cost_of_debt_post_tax": 0.06,
        "terminal_growth_rate": 0.03,
        "segment_debt": 0.0,
        "segment_cash": 0.0,
    }

    sotp_report = service.evaluate_sotp(
        dcf_segments_raw=[core_tech_segment],
        consolidated_debt=15_000_000.0,
        consolidated_cash=25_000_000.0,
        holding_discount_pct=0.10,  # 10% HoldCo Discount
    )

    print(f"--- SOTP Summary: {sotp_report.company_name} ---")
    print(f"Total Enterprise Value : INR {sotp_report.total_enterprise_value:,.2f}")
    print(f"Consolidated Equity Val: INR {sotp_report.consolidated_equity_value:,.2f}")
    print(f"Implied Target Price   : INR {sotp_report.implied_share_price:.2f}")

    # Inspect deep DCF audit trail from DCFResult
    dcf_detail = sotp_report.segments[0].details
    if dcf_detail:
        print(f"\n[DCF Audit - {sotp_report.segments[0].segment_name}]")
        print(f"WACC: {dcf_detail.wacc:.2%}")
        print(f"TV % of EV: {dcf_detail.terminal_value_pct_of_ev:.2f}%")
        print(f"PV FCFF Total: INR {dcf_detail.pv_fcff_total:,.2f}")
