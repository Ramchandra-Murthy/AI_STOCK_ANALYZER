import pandas as pd
import pytest

from ai_trading.return_autocorrelation import (
    return_autocorrelation,
    return_autocorrelation_summary,
)


def test_return_autocorrelation_matches_lagged_correlation() -> None:
    returns = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05])

    assert return_autocorrelation(returns, lag=1) == pytest.approx(1.0)


def test_return_autocorrelation_returns_none_when_insufficient_history() -> None:
    returns = pd.Series([0.01, 0.02])

    assert return_autocorrelation(returns, lag=2) is None


def test_return_autocorrelation_summary_reports_selected_lags() -> None:
    returns = pd.Series([0.01, 0.02, 0.03, 0.04, 0.05])

    report = return_autocorrelation_summary(returns, lags=(1, 2))

    assert set(report) == {"lag_1", "lag_2"}
    assert report["lag_1"] == pytest.approx(1.0)


def test_return_autocorrelation_rejects_invalid_lag() -> None:
    with pytest.raises(ValueError, match="lag must be at least 1"):
        return_autocorrelation(pd.Series([0.01, 0.02]), lag=0)


@pytest.mark.parametrize("infinite", [float("inf"), float("-inf")])
def test_return_autocorrelation_rejects_infinite_returns(infinite: float) -> None:
    returns = pd.Series([0.01, infinite, -0.02])

    with pytest.raises(ValueError, match="finite"):
        return_autocorrelation(returns, lag=1)

    with pytest.raises(ValueError, match="finite"):
        return_autocorrelation_summary(returns, lags=(1, 2))


@pytest.mark.parametrize("invalid_lag", [1.5, True, False])
def test_return_autocorrelation_rejects_non_integer_lags(invalid_lag: object) -> None:
    returns = pd.Series([0.01, 0.02, 0.03, 0.04])

    with pytest.raises(ValueError, match="integer"):
        return_autocorrelation(returns, lag=invalid_lag)

    with pytest.raises(ValueError, match="integer"):
        return_autocorrelation_summary(returns, lags=(1, invalid_lag))
