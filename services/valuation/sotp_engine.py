from __future__ import annotations

from typing import Any
from domain.valuation.result import ValuationResult, ValuationMethod, ValuationStatus

class BaseValuationEngine:
    """Abstract base class for valuation engines."""
    def __init__(self) -> None:
        pass
    
    @property
    def valuation_method(self) -> str:
        raise NotImplementedError

    def evaluate(self, data: Any) -> Any:
        raise NotImplementedError

    def value(self, data: Any) -> Any:
        return self.evaluate(data)

class SOTPValuationEngine(BaseValuationEngine):
    """Adapter for SOTP Valuation Engine conforming to BaseValuationEngine."""
    def __init__(self) -> None:
        super().__init__()

    @property
    def valuation_method(self) -> str:
        return "SOTP"

    def evaluate(self, data: Any) -> ValuationResult:
        from services.valuation.sotp_long_term_equity_valuation_service import (
            SOTPLongTermValuationService,
        )
        company_name = data.get("company_name", "Target Co")
        shares = data.get("shares_outstanding", 1.0)
        service = SOTPLongTermValuationService(company_name, shares)
        res = service.evaluate_sotp(
            dcf_segments_raw=data.get("dcf_segments", []),
            other_segments_raw=data.get("other_segments", []),
            holdco_discount=data.get("holdco_discount", 0.0)
        )
        return ValuationResult(
            method=ValuationMethod.SOTP,
            enterprise_value=res.total_enterprise_value,
            equity_value=res.total_equity_value,
            implied_share_price=res.implied_share_price,
            status=ValuationStatus.SUCCESS,
            details={"notes": "Evaluated successfully via modular SOTP engine"}
        )

# Backward compatibility alias
SOTPEngine = SOTPValuationEngine
