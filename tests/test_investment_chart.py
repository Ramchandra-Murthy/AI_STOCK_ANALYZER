from unittest.mock import patch

import pandas as pd

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
