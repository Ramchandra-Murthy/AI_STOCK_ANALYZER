import pandas as pd
import pytest

from ai_trading.monthly_returns import monthly_return_diagnostics


def test_monthly_return_diagnostics_compounds_calendar_months() -> None:
    index = pd.to_datetime(["2026-01-30", "2026-01-31", "2026-02-02", "2026-02-03"])
    returns = pd.Series([0.10, -0.05, 0.20, -0.10], index=index)

    report = monthly_return_diagnostics(returns)

    assert list(report.columns) == ["year", "month", "return"]
    assert len(report) == 2
    assert report.loc[0, "year"] == 2026
    assert report.loc[0, "month"] == 1
    assert report.loc[0, "return"] == pytest.approx(0.045)
    assert report.loc[1, "month"] == 2
    assert report.loc[1, "return"] == pytest.approx(0.08)


def test_monthly_return_diagnostics_handles_empty_returns() -> None:
    report = monthly_return_diagnostics(pd.Series(dtype=float))

    assert report.empty
    assert list(report.columns) == ["year", "month", "return"]


def test_monthly_return_diagnostics_rejects_invalid_index() -> None:
    returns = pd.Series([0.01], index=["not-a-date"])

    with pytest.raises(ValueError, match="valid timestamps"):
        monthly_return_diagnostics(returns)


@pytest.mark.parametrize("infinite", [float("inf"), float("-inf")])
def test_monthly_return_diagnostics_rejects_infinite_returns(infinite: float) -> None:
    index = pd.to_datetime(["2026-01-01", "2026-01-02"])
    returns = pd.Series([0.01, infinite], index=index)

    with pytest.raises(ValueError, match="finite"):
        monthly_return_diagnostics(returns)


@pytest.mark.parametrize("daily_return", [-1.01, -1.5])
def test_monthly_return_diagnostics_rejects_returns_below_minus_100_percent(
    daily_return: float,
) -> None:
    returns = pd.Series([daily_return], index=pd.to_datetime(["2026-01-01"]))

    with pytest.raises(ValueError, match="below -100%"):
        monthly_return_diagnostics(returns)


def test_monthly_return_diagnostics_accepts_total_loss() -> None:
    index = pd.to_datetime(["2026-01-01", "2026-01-02"])
    returns = pd.Series([-1.0, 0.25], index=index)

    report = monthly_return_diagnostics(returns)

    assert report.loc[0, "return"] == pytest.approx(-1.0)


def test_monthly_return_diagnostics_rejects_compounding_overflow() -> None:
    index = pd.to_datetime(["2026-01-01", "2026-01-02"])
    returns = pd.Series([1e308, 1e308], index=index)

    with pytest.raises(ValueError, match="not finite"):
        monthly_return_diagnostics(returns)
