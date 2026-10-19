from unittest.mock import patch

import pandas as pd
import pytest

from components.investment_chart import show_investment_chart


def test_investment_chart_uses_compact_responsive_layout():
    df = pd.DataFrame(
        {
            "symbol": ["RELIANCE"],
            "quantity": [2],
            "buy_price": [400.0],
            "Current Value": [976.7],
        }
    )

    with patch("components.investment_chart.st.plotly_chart") as plotly_chart:
        show_investment_chart(df)

    fig = plotly_chart.call_args.args[0]
    kwargs = plotly_chart.call_args.kwargs
    assert fig.layout.height == 320
    assert fig.layout.barmode == "group"
    assert kwargs["key"] == "dashboard_investment_comparison_chart"
    assert kwargs["config"]["responsive"] is True
    assert kwargs["config"]["displayModeBar"] is False
    assert len(fig.data) == 2
    assert list(fig.data[0].y) == [800.0]


def test_investment_chart_handles_empty_portfolio():
    with (
        patch("components.investment_chart.st.info") as info,
        patch("components.investment_chart.st.plotly_chart") as plotly_chart,
    ):
        show_investment_chart(pd.DataFrame())

    info.assert_called_once_with("No holdings available.")
    plotly_chart.assert_not_called()


def test_investment_chart_handles_missing_current_prices():
    df = pd.DataFrame(
        {
            "symbol": ["RELIANCE"],
            "quantity": [2],
            "buy_price": [400.0],
            "Current Value": [float("nan")],
        }
    )

    with (
        patch("components.investment_chart.st.info") as info,
        patch("components.investment_chart.st.plotly_chart") as plotly_chart,
    ):
        show_investment_chart(df)

    info.assert_called_once_with(
        "Investment comparison is unavailable because no holdings have current prices."
    )
    plotly_chart.assert_not_called()


@pytest.mark.parametrize("buy_price", [None, 0, -10, float("nan"), float("inf")])
def test_investment_chart_does_not_plot_invalid_cost_basis(buy_price):
    df = pd.DataFrame(
        {
            "symbol": ["SBIN.NS"],
            "quantity": [1],
            "buy_price": [buy_price],
            "Current Value": [973.75],
        }
    )

    with (
        patch("components.investment_chart.st.info") as info,
        patch("components.investment_chart.st.warning") as warning,
        patch("components.investment_chart.st.plotly_chart") as plotly_chart,
    ):
        show_investment_chart(df)

    info.assert_called_once_with(
        "Investment comparison is unavailable because purchase cost is missing or invalid "
        "for all priced holdings."
    )
    warning.assert_not_called()
    plotly_chart.assert_not_called()


def test_investment_chart_excludes_invalid_cost_basis_from_mixed_portfolio():
    df = pd.DataFrame(
        {
            "symbol": ["RELIANCE.NS", "SBIN.NS"],
            "quantity": [2, 1],
            "buy_price": [400.0, 0],
            "Current Value": [976.7, 973.75],
        }
    )

    with (
        patch("components.investment_chart.st.warning") as warning,
        patch("components.investment_chart.st.plotly_chart") as plotly_chart,
    ):
        show_investment_chart(df)

    warning.assert_called_once_with(
        "Investment comparison excludes 1 priced holding(s) with missing or invalid purchase cost."
    )
    fig = plotly_chart.call_args.args[0]
    assert list(fig.data[0].x) == ["RELIANCE.NS"]
    assert list(fig.data[0].y) == [800.0]
    assert list(fig.data[1].x) == ["RELIANCE.NS"]
    assert list(fig.data[1].y) == [976.7]
