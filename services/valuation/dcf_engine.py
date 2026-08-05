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

class DCFValuationEngine(BaseValuationEngine):
    """Adapter for DCF Valuation Engine conforming to BaseValuationEngine."""
    def __init__(self) -> None:
        super().__init__()

    @property
    def valuation_method(self) -> str:
        return "DCF"

    def evaluate(self, data: Any) -> ValuationResult:
        from services.valuation.dcf import DCFInput, DCFModel
        dcf_input = DCFInput(**data) if isinstance(data, dict) else data
        model = DCFModel(dcf_input)
        res = model.evaluate()
        return ValuationResult(
            method=ValuationMethod.DCF,
            enterprise_value=res.enterprise_value,
            equity_value=res.equity_value,
            implied_share_price=res.implied_share_price,
            status=ValuationStatus.SUCCESS,
            details={"notes": "Evaluated successfully via modular DCF engine"}
        )

# Backward compatibility alias
DCFEngine = DCFValuationEngine
