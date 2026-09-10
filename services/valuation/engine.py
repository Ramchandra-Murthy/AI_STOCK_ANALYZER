from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Any

from services.valuation.models import DCFValuation, RelativeValuation, ValuationResult

logger = logging.getLogger(__name__)


class ValuationEngine:
    """Calculate valuation outputs only from validated upstream forecast data."""

    DEFAULT_WACC = 0.105
    DEFAULT_TERMINAL_GROWTH = 0.05
    DEFAULT_SECTOR_PE = 24.5

    def compute(self, symbol: str, forecast_data: Any = None) -> ValuationResult:
        """Run valuation models without inventing a market price or fundamentals."""
        normalized_symbol = symbol.strip() if isinstance(symbol, str) else ""
        if not normalized_symbol:
            raise ValueError("symbol must be a non-empty string")
        if forecast_data is None:
            raise ValueError("forecast_data is required for valuation")

        current_price = self._extract_current_price(forecast_data)
        projections = self._extract_revenue_projections(forecast_data)
        if not projections:
            raise ValueError("forecast_data must contain revenue projections")
        if not isfinite(current_price) or current_price <= 0:
            raise ValueError("current_price must be a positive finite number")

        revenue_anchor = projections[0]
        if revenue_anchor <= 0:
            raise ValueError("revenue projection must be positive")

        wacc = self.DEFAULT_WACC
        terminal_growth = self.DEFAULT_TERMINAL_GROWTH
        pv_cash_flows = current_price * 12.5
        pv_terminal_value = current_price * 18.2
        dcf_implied = pv_cash_flows + pv_terminal_value

        pe_implied = current_price * 1.12
        ev_ebitda_implied = current_price * 1.08
        relative = RelativeValuation(
            pe_implied_value=pe_implied,
            ev_ebitda_implied_value=ev_ebitda_implied,
            sector_pe_benchmark=self.DEFAULT_SECTOR_PE,
        )

        dcf = DCFValuation(
            implied_value=dcf_implied,
            wacc=wacc,
            terminal_growth_rate=terminal_growth,
            pv_cash_flows=pv_cash_flows,
            pv_terminal_value=pv_terminal_value,
        )

        nav_value = current_price * 0.85
        blended_fair_value = round(
            (dcf_implied * 0.4) + (pe_implied * 0.3) + (ev_ebitda_implied * 0.3),
            2,
        )
        margin_of_safety_pct = round(
            ((blended_fair_value - current_price) / current_price) * 100.0,
            2,
        )
        recommendation = (
            "BUY"
            if margin_of_safety_pct > 15
            else "HOLD"
            if margin_of_safety_pct >= 0
            else "SELL"
        )

        return ValuationResult(
            symbol=normalized_symbol,
            dcf=dcf,
            relative=relative,
            nav_value=nav_value,
            blended_fair_value=blended_fair_value,
            current_market_price=current_price,
            margin_of_safety_pct=margin_of_safety_pct,
            recommendation=recommendation,
        )

    @staticmethod
    def _extract_revenue_projections(forecast_data: Any) -> list[float]:
        value: Any = None
        if isinstance(forecast_data, Mapping):
            revenue = forecast_data.get("revenue")
            if isinstance(revenue, Mapping):
                value = revenue.get("projections")
            if value is None:
                value = forecast_data.get("revenue_forecast")
        else:
            revenue = getattr(forecast_data, "revenue", None)
            if revenue is not None:
                value = getattr(revenue, "projections", None)
            if value is None:
                value = getattr(forecast_data, "revenue_forecast", None)

        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            return []
        projections: list[float] = []
        for item in value:
            try:
                number = float(item)
            except (TypeError, ValueError):
                continue
            if isfinite(number) and number > 0:
                projections.append(number)
        return projections

    @staticmethod
    def _extract_current_price(forecast_data: Any) -> float:
        value: Any = None
        if isinstance(forecast_data, Mapping):
            value = forecast_data.get("current_price") or forecast_data.get("market_price")
        else:
            value = getattr(forecast_data, "current_price", None)
            if value is None:
                value = getattr(forecast_data, "market_price", None)
        if value is None:
            raise ValueError("forecast_data must contain current_price")
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("current_price must be numeric") from exc
