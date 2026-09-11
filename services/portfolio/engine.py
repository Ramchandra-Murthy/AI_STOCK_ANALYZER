from __future__ import annotations

import logging
import math
import random

from services.portfolio.models import PortfolioAnalyticsResult, PositionResult

logger = logging.getLogger(__name__)


class PortfolioAnalyticsEngine:
    """Calculate portfolio analytics from caller-supplied holdings only."""

    def analyze(
        self,
        holdings: dict[str, dict[str, float]],
        risk_free_rate: float = 0.06,
        simulations: int = 1000,
    ) -> PortfolioAnalyticsResult:
        if not isinstance(holdings, dict):
            raise ValueError("holdings must be a mapping")
        if not 0 <= risk_free_rate < 1:
            raise ValueError("risk_free_rate must be between 0 and 1")
        if simulations <= 0:
            raise ValueError("simulations must be positive")

        position_results: list[PositionResult] = []
        total_value = 0.0
        normalized_holdings: dict[str, tuple[float, float, float]] = {}

        for raw_symbol, raw_data in holdings.items():
            symbol = str(raw_symbol).strip().upper()
            if not symbol or not isinstance(raw_data, dict):
                raise ValueError("each holding requires a symbol and mapping")

            shares_raw = raw_data.get("shares")
            price_raw = raw_data.get("price")
            cost_basis_raw = raw_data.get("cost_basis")
            if not isinstance(shares_raw, (int, float)) or shares_raw < 0:
                raise ValueError(f"shares must be non-negative for {symbol}")
            if not isinstance(price_raw, (int, float)) or price_raw <= 0:
                raise ValueError(f"positive price is required for {symbol}")
            if cost_basis_raw is None:
                cost_basis = float(price_raw)
            elif isinstance(cost_basis_raw, (int, float)) and cost_basis_raw > 0:
                cost_basis = float(cost_basis_raw)
            else:
                raise ValueError(f"positive cost_basis is required for {symbol}")

            shares = float(shares_raw)
            price = float(price_raw)
            normalized_holdings[symbol] = (shares, price, cost_basis)
            total_value += shares * price

        for symbol, (shares, price, cost_basis) in normalized_holdings.items():
            market_value = shares * price
            weight = market_value / total_value if total_value > 0 else 0.0
            pnl = market_value - shares * cost_basis
            position_results.append(
                PositionResult(
                    symbol=symbol,
                    shares=shares,
                    current_price=price,
                    market_value=round(market_value, 2),
                    weight=round(weight, 4),
                    unrealized_pnl=round(pnl, 2),
                )
            )

        if total_value <= 0:
            beta = 0.0
            sharpe = 0.0
            var_95 = 0.0
            median_mc = 0.0
            sector_allocation: dict[str, float] = {}
        else:
            # These values are deliberately derived from portfolio value and a simple
            # risk model; no company-specific sector/beta data is invented here.
            beta = 1.0
            annual_return = risk_free_rate
            annual_volatility = 0.15
            sharpe = annual_return / annual_volatility
            daily_volatility = annual_volatility / math.sqrt(252.0)
            var_95 = total_value * 1.645 * daily_volatility
            random_values = [
                total_value * (1.0 + random.normalvariate(annual_return, annual_volatility))
                for _ in range(simulations)
            ]
            random_values.sort()
            median_mc = random_values[len(random_values) // 2]
            sector_allocation = {"Unclassified": 1.0}

        return PortfolioAnalyticsResult(
            total_portfolio_value=round(total_value, 2),
            positions=position_results,
            sector_allocation=sector_allocation,
            portfolio_beta=beta,
            sharpe_ratio=round(sharpe, 4),
            value_at_risk_95=round(var_95, 2),
            monte_carlo_median_end_value=round(median_mc, 2),
            assumptions={
                "risk_free_rate": risk_free_rate,
                "simulations": simulations,
                "sector_classification": "UNAVAILABLE",
                "beta_source": "MODEL_BASELINE",
            },
        )
