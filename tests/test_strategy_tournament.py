from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ai_trading.strategy_tournament import compare_strategies


def test_compare_strategies_ranks_consistent_return_streams() -> None:
    returns = {
        "steady": pd.Series([0.01, 0.01, 0.01, 0.01] * 10),
        "volatile": pd.Series([0.05, -0.04, 0.05, -0.04] * 10),
    }

    report = compare_strategies(returns, min_observations=20)

    assert report.iloc[0]["strategy"] == "steady"
    assert report.iloc[0]["rank"] == 1
    assert report["eligible"].all()
    assert set(report["strategy"]) == {"steady", "volatile"}


def test_short_history_is_visible_but_not_ranked() -> None:
    report = compare_strategies(
        {"short": pd.Series([0.01, -0.01]), "enough": pd.Series([0.001] * 30)},
        min_observations=10,
    )

    short = report.loc[report["strategy"] == "short"].iloc[0]
    enough = report.loc[report["strategy"] == "enough"].iloc[0]
    assert not short["eligible"]
    assert pd.isna(short["rank"])
    assert enough["eligible"]


def test_missing_values_are_excluded_and_empty_input_is_supported() -> None:
    report = compare_strategies(
        {"example": pd.Series([0.01, np.nan, -0.005])},
        min_observations=2,
    )

    assert report.iloc[0]["observations"] == 2
    assert report.iloc[0]["eligible"]
    assert list(compare_strategies({}).columns)[0] == "strategy"


@pytest.mark.parametrize("returns", [[0.1, float("inf")], [0.1, -1.1], ["bad", 0.1]])
def test_invalid_returns_are_rejected(returns) -> None:
    with pytest.raises(ValueError):
        compare_strategies({"invalid": pd.Series(returns)})


def test_invalid_configuration_is_rejected() -> None:
    with pytest.raises(ValueError):
        compare_strategies({"example": pd.Series([0.01] * 5)}, periods_per_year=0)
    with pytest.raises(ValueError):
        compare_strategies({"example": pd.Series([0.01] * 5)}, min_observations=0)
