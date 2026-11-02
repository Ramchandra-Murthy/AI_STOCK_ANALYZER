import pandas as pd
import pytest

from ai_trading.parameter_sensitivity import (
    parameter_sensitivity_report,
    parameter_sensitivity_summary,
)


def test_parameter_sensitivity_report_ranks_configurations_by_return():
    returns = {
        "fast": pd.Series([0.02, -0.01, 0.03]),
        "slow": pd.Series([0.01, 0.01, 0.01]),
        "medium": pd.Series([-0.01, 0.02, 0.01]),
    }

    result = parameter_sensitivity_report(returns)

    assert result["parameter"].tolist() == ["fast", "slow", "medium"]
    assert result["return_rank"].tolist() == [1.0, 2.0, 3.0]


def test_parameter_sensitivity_report_ignores_missing_observations():
    returns = {"config": pd.Series([0.01, None, 0.02])}

    result = parameter_sensitivity_report(returns)

    assert result["observations"].tolist() == [2.0]


def test_parameter_sensitivity_summary_reports_performance_spread():
    report = pd.DataFrame(
        {
            "parameter": ["a", "b", "c"],
            "total_return": [0.10, 0.05, -0.02],
            "sharpe_ratio": [1.5, 0.8, -0.4],
            "max_drawdown": [0.03, 0.05, 0.09],
        }
    )

    result = parameter_sensitivity_summary(report)

    assert result["configurations"] == 3.0
    assert result["best_parameter"] == "a"
    assert result["worst_parameter"] == "c"
    assert result["return_spread"] == pytest.approx(0.12)
    assert result["sharpe_spread"] == pytest.approx(1.9)
    assert result["drawdown_spread"] == pytest.approx(0.06)


def test_parameter_sensitivity_summary_handles_empty_report():
    report = pd.DataFrame(columns=["parameter", "total_return", "sharpe_ratio", "max_drawdown"])

    result = parameter_sensitivity_summary(report)

    assert result["configurations"] == 0.0
    assert result["best_parameter"] is None


def test_invalid_parameter_inputs_are_rejected():
    with pytest.raises(ValueError, match="must not be empty"):
        parameter_sensitivity_report({})

    with pytest.raises(ValueError, match="finite and positive"):
        parameter_sensitivity_report({"config": pd.Series([0.01])}, periods_per_year=0)

    with pytest.raises(ValueError, match="finite and positive"):
        parameter_sensitivity_report({"config": pd.Series([0.01])}, periods_per_year=float("nan"))

    with pytest.raises(ValueError, match="finite and positive"):
        parameter_sensitivity_report({"config": pd.Series([0.01])}, periods_per_year=True)


@pytest.mark.parametrize("infinite", [float("inf"), float("-inf")])
def test_parameter_sensitivity_rejects_infinite_returns(infinite: float):
    with pytest.raises(ValueError, match="finite"):
        parameter_sensitivity_report({"config": pd.Series([0.01, infinite, -0.02])})


@pytest.mark.parametrize("invalid", ["not-a-return", ""])
def test_parameter_sensitivity_rejects_nonnumeric_returns(invalid: str):
    with pytest.raises(ValueError, match="numeric values or missing values"):
        parameter_sensitivity_report({"config": pd.Series([0.01, invalid, -0.02])})


def test_parameter_sensitivity_accepts_numeric_strings_and_missing_values():
    result = parameter_sensitivity_report({"config": pd.Series(["0.01", None, "-0.02"])})

    assert result["observations"].tolist() == [2.0]


def test_parameter_sensitivity_rejects_returns_below_total_loss():
    with pytest.raises(ValueError, match="below -100%"):
        parameter_sensitivity_report({"config": pd.Series([0.01, -1.01])})


def test_parameter_sensitivity_rejects_compounding_overflow():
    with pytest.raises(ValueError, match="total return.*overflowed"):
        parameter_sensitivity_report({"config": pd.Series([1e308, 1e308])})


@pytest.mark.parametrize(
    ("column", "invalid"),
    [
        ("total_return", float("nan")),
        ("sharpe_ratio", float("inf")),
        ("max_drawdown", float("-inf")),
        ("total_return", "not-a-number"),
    ],
)
def test_parameter_sensitivity_summary_rejects_invalid_metrics(column, invalid) -> None:
    report = pd.DataFrame(
        {
            "parameter": ["a", "b"],
            "total_return": [0.10, 0.05],
            "sharpe_ratio": [1.5, 0.8],
            "max_drawdown": [0.03, 0.05],
        }
    )
    report[column] = report[column].astype(object)
    report.loc[0, column] = invalid

    with pytest.raises(ValueError, match=column):
        parameter_sensitivity_summary(report)
