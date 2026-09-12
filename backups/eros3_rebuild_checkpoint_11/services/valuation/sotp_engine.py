from __future__ import annotations

from typing import Any

from domain.valuation.result import (
    ValuationMethod,
    ValuationResult,
    ValuationStatus,
)
from services.valuation.base_engine import BaseValuationEngine


class SOTPValuationEngine(BaseValuationEngine):
    """Adapter for the canonical SOTP valuation engine."""

    def __init__(self) -> None:
        super().__init__()

    @property
    def valuation_method(self) -> str:
        return ValuationMethod.SOTP.value

    def value(self, data: Any) -> ValuationResult:
        from services.sotp_long_term_equity_valuation_service import (
            SOTPLongTermValuationService,
        )

        company_name = data.get("company_name", "Target Co")
        shares = data.get("shares_outstanding", 1.0)

        service = SOTPLongTermValuationService(
            company_name,
            shares,
        )

        res = service.evaluate_sotp(
            dcf_segments_raw=data.get("dcf_segments", []),
            other_segments_raw=data.get("other_segments", []),
            holdco_discount=data.get("holdco_discount", 0.0),
        )

        return ValuationResult(
            method=ValuationMethod.SOTP,
            enterprise_value=res.total_enterprise_value,
            equity_value=res.total_equity_value,
            implied_share_price=res.implied_share_price,
            status=ValuationStatus.SUCCESS,
            details={"notes": "Evaluated successfully via modular SOTP engine"},
        )

    def evaluate(self, data: Any) -> ValuationResult:
        """Backward-compatible alias for value()."""
        return self.value(data)


SOTPEngine = SOTPValuationEngine
