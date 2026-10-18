import pandas as pd
import pytest

from services.portfolio_service import get_summary


def test_summary_excludes_unpriced_holdings_from_valuation_totals():
    portfolio = pd.DataFrame(
        {
            "symbol": ["AAA.NS", "BBB.NS", "CCC.NS"],
            "quantity": [10, 5, 20],
            "buy_price": [100.0, 200.0, 50.0],
            "Current Value": [1100.0, 900.0, None],
        }
    )

    summary = get_summary(portfolio)

    assert summary["holdings"] == 3
    assert summary["valued_holdings"] == 2
    assert summary["unpriced_holdings"] == 1
    assert summary["investment"] == pytest.approx(2000.0)
    assert summary["current_value"] == pytest.approx(2000.0)
    assert summary["profit"] == pytest.approx(0.0)
    assert summary["return"] == pytest.approx(0.0)


def test_summary_with_no_available_prices_does_not_report_a_false_loss():
    portfolio = pd.DataFrame(
        {
            "symbol": ["AAA.NS", "BBB.NS"],
            "quantity": [10, 5],
            "buy_price": [100.0, 200.0],
            "Current Value": [None, None],
        }
    )

    summary = get_summary(portfolio)

    assert summary["holdings"] == 2
    assert summary["valued_holdings"] == 0
    assert summary["unpriced_holdings"] == 2
    assert summary["investment"] == 0
    assert summary["current_value"] == 0
    assert summary["profit"] == 0
    assert summary["return"] == 0


def test_summary_with_empty_portfolio():
    summary = get_summary(pd.DataFrame())

    assert summary == {
        "investment": 0,
        "current_value": 0,
        "profit": 0,
        "return": 0,
        "holdings": 0,
        "valued_holdings": 0,
        "unpriced_holdings": 0,
    }
