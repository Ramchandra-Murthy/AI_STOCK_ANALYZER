from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from math import isfinite
from typing import Any

from services.valuation.models import DCFValuation, RelativeValuation, ValuationResult

logger = logging.getLogger(__name__)


class ValuationEngine:
    """Calculate valuation outputs only from explicit market, earnings and forecast inputs."""

    DEFAULT_WACC = 0.105
    DEFAULT_TERMINAL_GROWTH = 0.05
    DEFAULT_SECTOR_PE = 24.5

    def compute(self, symbol: str, forecast_data: Any = None) -> ValuationResult:
        normalized_symbol = symbol.strip().upper() if isinstance(symbol, str) else ""
        if not normalized_symbol:
            raise ValueError("symbol must be a non-empty string")
        if forecast_data is None:
            raise ValueError("forecast_data is required for valuation")

        current_price = self._extract_positive_number(
            forecast_data, "current_price", "market_price"
        )
        revenue_projections = self._extract_series(
            forecast_data, "revenue_forecast", nested_key="revenue"
        )
        fcf_projections = self._extract_series(
            forecast_data, "free_cash_flow_forecast", nested_key="free_cash_flow"
        )
        eps_projections = self._extract_series(forecast_data, "eps_forecast", nested_key="eps")
        ebitda_projections = self._extract_series(
            forecast_data, "ebitda_forecast", nested_key="ebitda"
        )

        if not revenue_projections or not fcf_projections:
            raise ValueError("forecast_data must contain revenue and free-cash-flow projections")
        if len(revenue_projections) != len(fcf_projections):
            raise ValueError("revenue and free-cash-flow projections must have equal length")

        current_eps = self._extract_positive_number_optional(forecast_data, "current_eps", "eps")
        current_ebitda = self._extract_positive_number_optional(
            forecast_data, "current_ebitda", "ebitda"
        )
        shares = self._extract_positive_number_optional(
            forecast_data, "shares_outstanding", "shares"
        )
        total_debt = self._extract_nonnegative_number_optional(forecast_data, "total_debt", "debt")
        cash = self._extract_nonnegative_number_optional(forecast_data, "cash", "total_cash")
        equity = self._extract_positive_number_optional(
            forecast_data, "equity", "shareholders_equity"
        )

        wacc = self._extract_rate(forecast_data, "wacc", self.DEFAULT_WACC)
        terminal_growth = self._extract_rate(
            forecast_data, "terminal_growth_rate", self.DEFAULT_TERMINAL_GROWTH
        )
        if terminal_growth >= wacc:
            raise ValueError("terminal growth rate must be below WACC")

        discount_factors = [
            1.0 / ((1.0 + wacc) ** (index + 1)) for index in range(len(fcf_projections))
        ]
        pv_cash_flows = sum(cf * factor for cf, factor in zip(fcf_projections, discount_factors))
        terminal_fcf = fcf_projections[-1] * (1.0 + terminal_growth)
        terminal_value = terminal_fcf / (wacc - terminal_growth)
        pv_terminal_value = terminal_value * discount_factors[-1]
        enterprise_value = pv_cash_flows + pv_terminal_value
        equity_value_dcf = enterprise_value - total_debt + cash

        dcf_implied_per_share = (
            equity_value_dcf / shares if shares and shares > 0 else equity_value_dcf
        )

        relative_values: list[float] = []
        pe_implied = None
        if eps_projections:
            if eps_projections[-1] <= 0:
                raise ValueError("EPS projection must be positive for P/E valuation")
            pe_implied = eps_projections[-1] * self._extract_rate(
                forecast_data, "sector_pe", self.DEFAULT_SECTOR_PE
            )
            relative_values.append(pe_implied)

        ev_ebitda_implied = None
        if ebitda_projections:
            if ebitda_projections[-1] <= 0:
                raise ValueError("EBITDA projection must be positive for EV/EBITDA valuation")
            ev_multiple = self._extract_rate(forecast_data, "ev_ebitda_multiple", 14.0)
            ev_ebitda_value = ebitda_projections[-1] * ev_multiple
            ev_ebitda_implied = (
                (ev_ebitda_value - total_debt + cash) / shares
                if shares and shares > 0
                else ev_ebitda_value - total_debt + cash
            )
            relative_values.append(ev_ebitda_implied)

        if not relative_values and equity_value_dcf <= 0:
            raise ValueError("valuation inputs do not produce a positive fair-value estimate")

        nav_value = self._extract_positive_number_optional(forecast_data, "nav_value")
        if nav_value is None:
            nav_value = equity if equity is not None else equity_value_dcf

        fair_value_candidates = [dcf_implied_per_share, *relative_values]
        fair_value_candidates = [
            value for value in fair_value_candidates if isfinite(value) and value > 0
        ]
        if nav_value is not None and nav_value > 0:
            fair_value_candidates.append(nav_value)
        if not fair_value_candidates:
            raise ValueError("no positive fair-value estimate could be produced")

        blended_fair_value = round(sum(fair_value_candidates) / len(fair_value_candidates), 2)
        margin_of_safety_pct = round(
            ((blended_fair_value - current_price) / current_price) * 100.0, 2
        )
        recommendation = (
            "BUY" if margin_of_safety_pct > 15 else "HOLD" if margin_of_safety_pct >= 0 else "SELL"
        )

        return ValuationResult(
            symbol=normalized_symbol,
            dcf=DCFValuation(
                implied_value=round(dcf_implied_per_share, 2),
                wacc=wacc,
                terminal_growth_rate=terminal_growth,
                pv_cash_flows=round(pv_cash_flows, 2),
                pv_terminal_value=round(pv_terminal_value, 2),
            ),
            relative=RelativeValuation(
                pe_implied_value=round(pe_implied, 2) if pe_implied is not None else 0.0,
                ev_ebitda_implied_value=(
                    round(ev_ebitda_implied, 2) if ev_ebitda_implied is not None else 0.0
                ),
                sector_pe_benchmark=self._extract_rate(
                    forecast_data, "sector_pe", self.DEFAULT_SECTOR_PE
                ),
            ),
            nav_value=round(float(nav_value), 2),
            blended_fair_value=blended_fair_value,
            current_market_price=current_price,
            margin_of_safety_pct=margin_of_safety_pct,
            recommendation=recommendation,
        )

    @staticmethod
    def _extract_series(data: Any, direct_key: str, nested_key: str) -> list[float]:
        value: Any = None
        if isinstance(data, Mapping):
            value = data.get(direct_key)
            if value is None:
                nested = data.get(nested_key)
                if isinstance(nested, Mapping):
                    value = nested.get("projections")
        else:
            value = getattr(data, direct_key, None)
            if value is None:
                nested = getattr(data, nested_key, None)
                value = getattr(nested, "projections", None) if nested is not None else None
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            return []
        result: list[float] = []
        for item in value:
            try:
                number = float(item)
            except (TypeError, ValueError):
                continue
            if isfinite(number):
                result.append(number)
        return result

    @staticmethod
    def _extract_positive_number(data: Any, *keys: str) -> float:
        value = ValuationEngine._extract_number(data, *keys)
        if value is None or not isfinite(value) or value <= 0:
            raise ValueError(f"{keys[0]} must be a positive finite number")
        return value

    @staticmethod
    def _extract_positive_number_optional(data: Any, *keys: str) -> float | None:
        value = ValuationEngine._extract_number(data, *keys)
        if value is None:
            return None
        if not isfinite(value) or value <= 0:
            raise ValueError(f"{keys[0]} must be positive when supplied")
        return value

    @staticmethod
    def _extract_nonnegative_number_optional(data: Any, *keys: str) -> float:
        value = ValuationEngine._extract_number(data, *keys)
        if value is None:
            return 0.0
        if not isfinite(value) or value < 0:
            raise ValueError(f"{keys[0]} must be non-negative when supplied")
        return value

    @staticmethod
    def _extract_number(data: Any, *keys: str) -> float | None:
        for key in keys:
            if isinstance(data, Mapping):
                value = data.get(key)
            else:
                value = getattr(data, key, None)
            if value is not None:
                try:
                    return float(value)
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"{key} must be numeric") from exc
        return None

    @staticmethod
    def _extract_rate(data: Any, key: str, default: float) -> float:
        value = ValuationEngine._extract_number(data, key)
        rate = default if value is None else value
        if key in {"wacc", "terminal_growth_rate"} and rate >= 1:
            rate /= 100.0
        if not isfinite(rate) or rate < 0:
            raise ValueError(f"{key} must be non-negative and finite")
        return float(rate)
