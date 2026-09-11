from __future__ import annotations

from typing import Any

from domain.valuation.result import (
    ValuationResult,
    ValuationMethod,
    ValuationStatus,
)

from services.valuation.base_engine import BaseValuationEngine


class NAVValuationEngine(BaseValuationEngine):
    """Adapter for the canonical NAV valuation engine."""

    def __init__(self) -> None:
        super().__init__()

    @property
    def valuation_method(self) -> str:
        return ValuationMethod.NAV.value

    def value(self, data: Any) -> ValuationResult:
        from services.valuation.nav.nav_input import NAVInput
        from services.valuation.nav.nav_model import NAVModel

        nav_input = NAVInput(**data) if isinstance(data, dict) else data

        model = NAVModel(nav_input)
        res = model.evaluate()

        return ValuationResult(
            method=ValuationMethod.NAV,
            enterprise_value=res.total_asset_value,
            equity_value=res.net_asset_value,
            implied_share_price=res.implied_share_price,
            status=ValuationStatus.SUCCESS,
            details={"notes": "Evaluated successfully via modular NAV engine"},
        )

    def evaluate(self, data: Any) -> ValuationResult:
        """Backward-compatible alias for value()."""
        return self.value(data)


NAVEngine = NAVValuationEngine
