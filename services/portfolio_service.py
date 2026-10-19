"""Portfolio valuation service.

Portfolio valuation uses the canonical market-data service directly. It does
not run the full technical analyzer for every holding, avoiding database
writes and avoiding a misleading "live" label for daily market data.
"""

import math

import pandas as pd

from portfolio.portfolio import load_portfolio
from services.market_service import get_latest_available_price


def _is_positive_finite_number(value):
    """Return whether a value is a finite positive number."""
    try:
        return math.isfinite(float(value)) and float(value) > 0
    except (TypeError, ValueError):
        return False


def get_live_price(symbol):
    """Backward-compatible price helper returning the latest available price."""
    data = get_latest_available_price(symbol)
    return data["price"]


def get_portfolio():
    """Return portfolio with latest available prices and valuation metadata."""
    df = load_portfolio()

    if df.empty:
        return df

    prices = []
    observed_at = []
    sources = []
    frequencies = []
    current_values = []
    profits = []
    returns = []
    cost_basis_validity = []

    for _, row in df.iterrows():
        quote = get_latest_available_price(row["symbol"])
        cmp = quote["price"]

        prices.append(cmp)
        observed_at.append(quote["observed_at"])
        sources.append(quote["source"])
        frequencies.append(quote["frequency"])

        valid_quantity = _is_positive_finite_number(row.get("quantity"))
        valid_buy_price = _is_positive_finite_number(row.get("buy_price"))
        valid_cost_basis = valid_quantity and valid_buy_price
        cost_basis_validity.append(valid_cost_basis)

        if not _is_positive_finite_number(cmp) or not valid_quantity:
            current_values.append(None)
            profits.append(None)
            returns.append(None)
            continue

        current_value = float(row["quantity"]) * float(cmp)
        current_values.append(round(current_value, 2))

        if not valid_cost_basis:
            # Do not report the entire market value as profit when the purchase
            # cost is missing, zero, negative, or non-finite.
            profits.append(None)
            returns.append(None)
            continue

        investment = float(row["quantity"]) * float(row["buy_price"])
        profit = current_value - investment
        ret = (profit / investment) * 100

        profits.append(round(profit, 2))
        returns.append(round(ret, 2))

    df["CMP"] = prices
    df["Price Observed"] = observed_at
    df["Price Source"] = sources
    df["Price Frequency"] = frequencies
    df["Current Value"] = current_values
    df["Profit"] = profits
    df["Return %"] = returns
    df["Cost Basis Valid"] = cost_basis_validity

    return df


def get_summary(df):
    """Summarize priced holdings without fabricating profit for invalid cost basis."""
    if df.empty:
        return {
            "investment": 0,
            "current_value": 0,
            "profit": 0,
            "return": 0,
            "holdings": 0,
            "valued_holdings": 0,
            "unpriced_holdings": 0,
            "cost_basis_incomplete": False,
        }

    if "Current Value" in df.columns:
        valued = df.loc[df["Current Value"].notna()].copy()
        current_value = pd.to_numeric(valued["Current Value"], errors="coerce").sum()
    else:
        valued = df.iloc[0:0].copy()
        current_value = 0.0

    if valued.empty:
        valid_cost_basis = pd.Series(dtype=bool, index=valued.index)
    else:
        valid_cost_basis = valued.apply(
            lambda row: _is_positive_finite_number(row.get("quantity"))
            and _is_positive_finite_number(row.get("buy_price")),
            axis=1,
        )

    cost_basis_incomplete = bool(len(valued) and not valid_cost_basis.all())
    known_investment = (
        (
            pd.to_numeric(valued.loc[valid_cost_basis, "quantity"], errors="coerce")
            * pd.to_numeric(valued.loc[valid_cost_basis, "buy_price"], errors="coerce")
        ).sum()
        if len(valued)
        else 0.0
    )

    if cost_basis_incomplete:
        profit = None
        returns = None
    else:
        profit = current_value - known_investment
        returns = (profit / known_investment) * 100 if known_investment else 0.0

    return {
        "investment": round(float(known_investment), 2),
        "current_value": round(float(current_value), 2),
        "profit": round(float(profit), 2) if profit is not None else None,
        "return": round(float(returns), 2) if returns is not None else None,
        "holdings": len(df),
        "valued_holdings": len(valued),
        "unpriced_holdings": len(df) - len(valued),
        "cost_basis_incomplete": cost_basis_incomplete,
    }
