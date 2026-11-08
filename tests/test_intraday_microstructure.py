import numpy as np
import pandas as pd
import pytest

from ai_trading.intraday_microstructure import intraday_microstructure_features


def _bars(count=6):
    close = pd.Series([100.0, 101.0, 100.5, 102.0, 101.5, 103.0][:count])
    return pd.DataFrame(
        {
            "Open": close - 0.2,
            "High": close + 1.0,
            "Low": close - 1.0,
            "Close": close,
            "Volume": [1000.0, 1100.0, 900.0, 1200.0, 1000.0, 1500.0][:count],
        },
        index=pd.date_range("2026-10-01 09:15", periods=count, freq="min"),
    )


def test_features_preserve_index_and_include_expected_columns():
    bars = _bars()
    result = intraday_microstructure_features(bars, window=3)
    assert result.index.equals(bars.index)
    assert {
        "log_return",
        "range_pct",
        "realized_variance",
        "realized_volatility",
        "parkinson_volatility",
        "turnover",
        "amihud_illiquidity",
        "volume_zscore",
    }.issubset(result.columns)
    assert result["turnover"].iloc[-1] == pytest.approx(103.0 * 1500.0)


def test_realized_volatility_is_square_root_of_rolling_variance():
    result = intraday_microstructure_features(_bars(), window=3)
    assert result["realized_volatility"].iloc[-1] == pytest.approx(
        np.sqrt(result["realized_variance"].iloc[-1])
    )


def test_volume_zscore_uses_only_prior_bars():
    bars = _bars()
    result = intraday_microstructure_features(bars, window=3)
    prior = bars["Volume"].iloc[1:4]
    expected = (bars["Volume"].iloc[4] - prior.mean()) / prior.std(ddof=0)
    assert result["volume_zscore"].iloc[4] == pytest.approx(expected)


def test_missing_ohlcv_rows_are_dropped():
    bars = _bars()
    bars.loc[bars.index[2], "Close"] = np.nan
    result = intraday_microstructure_features(bars, window=2)
    assert bars.index[2] not in result.index


@pytest.mark.parametrize("window", [0, 1, 2.5, True, "3"])
def test_invalid_window_is_rejected(window):
    with pytest.raises(ValueError, match="window"):
        intraday_microstructure_features(_bars(), window=window)


def test_missing_columns_are_rejected():
    with pytest.raises(ValueError, match="OHLCV"):
        intraday_microstructure_features(_bars().drop(columns="Volume"))


@pytest.mark.parametrize(
    "column,value",
    [("Open", 0.0), ("Close", -1.0), ("Volume", -1.0), ("High", np.inf)],
)
def test_invalid_values_are_rejected(column, value):
    bars = _bars()
    bars.iloc[2, bars.columns.get_loc(column)] = value
    with pytest.raises(ValueError):
        intraday_microstructure_features(bars, window=2)


def test_invalid_ohlc_relationship_is_rejected():
    bars = _bars()
    bars.iloc[1, bars.columns.get_loc("High")] = 99.0
    with pytest.raises(ValueError, match="Low <= Open/Close <= High"):
        intraday_microstructure_features(bars, window=2)


def test_zero_turnover_does_not_create_infinite_illiquidity():
    bars = _bars()
    bars.loc[bars.index[2], "Volume"] = 0.0
    result = intraday_microstructure_features(bars, window=2)
    finite = result["amihud_illiquidity"].dropna()
    assert np.isfinite(finite.to_numpy()).all()
