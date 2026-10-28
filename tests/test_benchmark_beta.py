import pandas as pd
import pytest

from ai_trading.benchmark_beta import benchmark_beta, benchmark_beta_summary


def test_benchmark_beta_matches_covariance_variance_ratio() -> None:
    benchmark = pd.Series([0.01, -0.01, 0.02, -0.02])
    strategy = benchmark * 2.0

    assert benchmark_beta(strategy, benchmark) == pytest.approx(2.0)


def test_benchmark_beta_returns_none_for_insufficient_history() -> None:
    benchmark = pd.Series([0.01])
    strategy = pd.Series([0.02])

    assert benchmark_beta(strategy, benchmark) is None


def test_benchmark_beta_summary_reports_aligned_observations() -> None:
    benchmark = pd.Series([0.01, 0.02, 0.03])
    strategy = pd.Series([0.02, None, 0.06])

    report = benchmark_beta_summary(strategy, benchmark)

    assert report["observations"] == 2
    assert report["beta"] == pytest.approx(2.0)


@pytest.mark.parametrize("invalid", [float("inf"), float("-inf")])
def test_benchmark_beta_rejects_infinite_returns(invalid):
    benchmark = pd.Series([0.01, invalid, 0.03])
    strategy = pd.Series([0.02, 0.04, 0.06])

    with pytest.raises(ValueError, match="returns must be finite"):
        benchmark_beta(strategy, benchmark)


def test_benchmark_beta_rejects_overflowed_calculation():
    benchmark = pd.Series([-1e308, 1e308])
    strategy = pd.Series([1e308, -1e308])

    with pytest.raises(ValueError, match="non-finite result"):
        benchmark_beta(strategy, benchmark)
