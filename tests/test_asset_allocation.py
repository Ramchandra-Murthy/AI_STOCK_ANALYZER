import numpy as np
import pandas as pd
import pytest

from algorithmic_trading.asset_allocation import (
    allocation_summary,
    apply_weight_cap,
    equal_weight,
    inverse_volatility_weight,
    minimum_variance_weight,
)


@pytest.fixture
def returns() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "RELIANCE": [0.01, -0.005, 0.008, 0.004],
            "TCS": [0.005, 0.002, -0.003, 0.004],
            "INFY": [0.003, 0.001, 0.002, -0.001],
        }
    )


def test_equal_weight(returns: pd.DataFrame) -> None:
    weights = equal_weight(returns)
    assert weights.sum() == pytest.approx(1.0)
    assert np.allclose(weights.to_numpy(), 1 / 3)


def test_inverse_volatility_weight(returns: pd.DataFrame) -> None:
    weights = inverse_volatility_weight(returns)
    assert weights.sum() == pytest.approx(1.0)
    assert (weights >= 0).all()


def test_minimum_variance_weight(returns: pd.DataFrame) -> None:
    weights = minimum_variance_weight(returns)
    assert weights.sum() == pytest.approx(1.0)
    assert (weights >= 0).all()


def test_weight_cap(returns: pd.DataFrame) -> None:
    weights = equal_weight(returns)
    capped = apply_weight_cap(weights, 0.40)
    assert capped.max() <= 0.40 + 1e-12
    assert capped.sum() == pytest.approx(1.0)


def test_allocation_summary(returns: pd.DataFrame) -> None:
    summary = allocation_summary(equal_weight(returns))
    assert list(summary.columns) == ["weight", "weight_pct"]
