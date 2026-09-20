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


def test_safety_filter_removes_known_flags_only():
    from scanner.surveillance import apply_safety_filter

    candidates = pd.DataFrame(
        [
            {"Symbol": "SAFE", "Exchange": "NSE"},
            {"Symbol": "FLAGGED", "Exchange": "NSE"},
            {"Symbol": "BSE1", "Exchange": "BSE"},
        ]
    )
    safety = pd.DataFrame(
        [
            {
                "Symbol": "SAFE",
                "Safety flags": "",
                "Safety status": "NSE check clear",
            },
            {
                "Symbol": "FLAGGED",
                "Safety flags": "ASM: 11",
                "Safety status": "Flagged - review before trading",
            },
        ]
    )

    result = apply_safety_filter(candidates, safety, exclude_flagged=True)

    assert result["Symbol"].tolist() == ["SAFE", "BSE1"]
    assert result.loc[result["Symbol"].eq("BSE1"), "Safety status"].iloc[0] == (
        "Manual check required"
    )


def test_liquidity_warning():
    from scanner.surveillance import liquidity_warning

    assert liquidity_warning(10.0, 200_000) == "Low recent traded value"
    assert liquidity_warning(10.0, 100_000) == "Low recent traded value"
    assert liquidity_warning(20.0, 100_000) == "OK"


def test_score_combines_opportunity_and_setup_scores():
    rows = pd.DataFrame(
        [
            {
                "Symbol": "SETUP",
                "5-min change %": 2.0,
                "Volume surge x": 2.0,
                "Session range %": 2.0,
                "Breakout": "YES",
                "Low-price flag": "—",
                "Setup score": 80,
            }
        ]
    )

    result = score_opportunity_rows(rows)

    assert result.iloc[0]["Opportunity score"] == 82.5
    assert result.iloc[0]["Composite score"] == 81.5
