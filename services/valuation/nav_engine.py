from __future__ import annotations

"""
==========================================================
NAV VALUATION ENGINE ADAPTER
Module  : nav_engine
Version : V1.0
==========================================================

Adapter between the generic valuation dispatcher and the
institutional NAV valuation engine.

Responsibilities
----------------
• Accept standardized entity input
• Build NAVInput
• Execute NAVModel
• Return standardized ValuationResult
"""

from typing import Any, Dict
from services.valuation.base_engine import BaseValuationEngine
from services.valuation.models import (
    ValuationMethod,
    ValuationResult,
    ValuationStatus,
)
from services.valuation.nav.nav_input import (
    NAVInput,
    NAVAsset,
    NAVLiability,
)
from services.valuation.nav.nav_model import NAVModel


class NAVEngine(BaseValuationEngine):
    """
    Adapter exposing the NAV engine through the common
    valuation interface.
    """

    @property
    def valuation_method(self) -> str:
        return ValuationMethod.NAV.value

    def value(
        self,
        entity: Dict[str, Any],
    ) -> ValuationResult:

        assets = [
            NAVAsset(**asset)
            for asset in entity.get("assets", [])
        ]

        liabilities = [
            NAVLiability(**liability)
            for liability in entity.get("liabilities", [])
        ]

        nav_input = NAVInput(
            company_name=entity["company_name"],
            currency=entity.get("currency", "INR"),
            assets=assets,
            liabilities=liabilities,
            minority_interest=entity.get(
                "minority_interest",
                0.0,
            ),
            holding_company_discount_pct=entity.get(
                "holding_company_discount_pct",
                0.0,
            ),
            shares_outstanding=entity["shares_outstanding"],
        )

        nav_result = NAVModel(nav_input).run_model()

        return ValuationResult(
            entity_name=nav_result.company_name,
            valuation_method=ValuationMethod.NAV,
            valuation_status=ValuationStatus.COMPLETE,
            enterprise_value=nav_result.gross_asset_value,
            equity_value=nav_result.equity_value,
            diagnostics={
                "gross_asset_value": nav_result.gross_asset_value,
                "net_asset_value": nav_result.net_asset_value,
                "adjusted_nav": nav_result.adjusted_nav,
                "share_price": nav_result.implied_share_price,
                "asset_count": nav_result.asset_count,
                "liability_count": nav_result.liability_count,
            },
            raw_result=nav_result,
        )
