"""Tests for the options analytics foundation."""

import pandas as pd

from services.options_analytics import summarize_option_chain


def test_summarize_option_chain_calculates_pcr_and_oi_levels():
    chain = pd.DataFrame(
        {
            "strike": [24900, 25000, 25100],
            "CE LTP": [150.0, 100.0, 60.0],
            "CE volume": [1000, 2000, 1500],
            "CE OI": [10000, 20000, 30000],
            "CE OI change": [500, 1000, 1500],
            "CE IV": [0.18, 0.17, 0.19],
            "PE LTP": [50.0, 100.0, 160.0],
            "PE volume": [1200, 2200, 1800],
            "PE OI": [30000, 25000, 15000],
            "PE OI change": [1000, 1200, 800],
            "PE IV": [0.19, 0.18, 0.17],
            "PCR OI": [3.0, 1.25, 0.5],
        }
    )

    summary = summarize_option_chain(chain)
    values = dict(zip(summary["Metric"], summary["Value"], strict=True))

    assert values["Call OI"] == 60000.0
    assert values["Put OI"] == 70000.0
    assert values["PCR (OI)"] == 70000 / 60000
    assert values["Highest Call OI strike"] == 25100.0
    assert values["Highest Put OI strike"] == 24900.0


def test_empty_chain_has_stable_summary_schema():
    summary = summarize_option_chain(pd.DataFrame())
    assert list(summary.columns) == ["Metric", "Value"]
    assert summary.empty
