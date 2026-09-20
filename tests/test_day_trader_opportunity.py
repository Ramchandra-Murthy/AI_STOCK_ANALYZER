import pandas as pd

from scanner.day_trader_opportunity import score_opportunity_rows


def test_score_ranks_volume_momentum_breakout():
    rows = pd.DataFrame(
        [
            {
                "Symbol": "A",
                "5-min change %": 2.0,
                "Volume surge x": 3.0,
                "Session range %": 4.0,
                "Breakout": "YES",
                "Low-price flag": "YES",
            },
            {
                "Symbol": "B",
                "5-min change %": 0.5,
                "Volume surge x": 1.2,
                "Session range %": 1.0,
                "Breakout": "—",
                "Low-price flag": "—",
            },
        ]
    )

    result = score_opportunity_rows(rows)

    assert result.iloc[0]["Symbol"] == "A"
    assert result.iloc[0]["Opportunity score"] == 100.0
    assert result.iloc[0]["Setup"] == "Low-price volume watch"


def test_score_handles_empty_input():
    result = score_opportunity_rows(pd.DataFrame())

    assert result.empty
