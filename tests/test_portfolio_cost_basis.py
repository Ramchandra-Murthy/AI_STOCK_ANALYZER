from unittest.mock import patch

import pandas as pd

from services.portfolio_service import get_portfolio


def _quote(price):
    return {
        "price": price,
        "observed_at": "2026-10-19T10:00:00+05:30",
        "source": "test",
        "frequency": "daily",
    }


def test_get_portfolio_does_not_treat_missing_cost_basis_as_profit():
    portfolio = pd.DataFrame(
        {
            "symbol": ["SBIN.NS"],
            "quantity": [1],
            "buy_price": [0],
        }
    )

    with (
        patch("services.portfolio_service.load_portfolio", return_value=portfolio),
        patch(
            "services.portfolio_service.get_latest_available_price",
            return_value=_quote(973.75),
        ),
    ):
        result = get_portfolio()

    assert result.loc[0, "Current Value"] == 973.75
    assert pd.isna(result.loc[0, "Profit"])
    assert pd.isna(result.loc[0, "Return %"])
    assert result.loc[0, "Cost Basis Valid"] == False


def test_get_portfolio_calculates_profit_when_cost_basis_is_valid():
    portfolio = pd.DataFrame(
        {
            "symbol": ["SBIN.NS"],
            "quantity": [2],
            "buy_price": [400.0],
        }
    )

    with (
        patch("services.portfolio_service.load_portfolio", return_value=portfolio),
        patch(
            "services.portfolio_service.get_latest_available_price",
            return_value=_quote(450.0),
        ),
    ):
        result = get_portfolio()

    assert result.loc[0, "Current Value"] == 900.0
    assert result.loc[0, "Profit"] == 100.0
    assert result.loc[0, "Return %"] == 12.5
    assert result.loc[0, "Cost Basis Valid"] == True


def test_get_portfolio_marks_missing_market_price_as_unvalued():
    portfolio = pd.DataFrame(
        {
            "symbol": ["SBIN.NS"],
            "quantity": [1],
            "buy_price": [400.0],
        }
    )

    with (
        patch("services.portfolio_service.load_portfolio", return_value=portfolio),
        patch(
            "services.portfolio_service.get_latest_available_price",
            return_value=_quote(None),
        ),
    ):
        result = get_portfolio()

    assert pd.isna(result.loc[0, "Current Value"])
    assert pd.isna(result.loc[0, "Profit"])
    assert pd.isna(result.loc[0, "Return %"])
