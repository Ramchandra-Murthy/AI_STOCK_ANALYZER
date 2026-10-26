"""Tests for chronological MLP configuration evaluation."""

import numpy as np
import pandas as pd
import pytest

from neural_networks.evaluation import compare_mlp_configurations


def _dataset(rows: int = 420) -> tuple[pd.DataFrame, pd.Series]:
    index = pd.date_range("2023-01-01", periods=rows, freq="D")
    rng = np.random.default_rng(17)
    features = pd.DataFrame(
        {"signal": rng.normal(size=rows), "noise": rng.normal(size=rows)}, index=index
    )
    target = pd.Series((features["signal"] + rng.normal(scale=0.8, size=rows) > 0).astype(int), index=index)
    return features, target


def test_mlp_configuration_evaluation_reports_chronological_folds() -> None:
    features, target = _dataset()
    results = compare_mlp_configurations(
        features,
        target,
        configurations=(((4,), 0.1),),
        n_splits=2,
        horizon=1,
    )

    assert len(results) == 2
    assert results["Fold"].tolist() == [1, 2]
    assert (results["Train rows"] > 0).all()
    assert (results["Validation rows"] > 0).all()
    assert results["Validation start"].notna().all()
    assert results["Brier score"].between(0, 1).all()


def test_mlp_configuration_evaluation_rejects_invalid_alpha() -> None:
    features, target = _dataset()
    with pytest.raises(ValueError, match="alpha must be finite and positive"):
        compare_mlp_configurations(features, target, configurations=(((8,), 0.0),))
