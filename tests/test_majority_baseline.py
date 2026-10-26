"""Regression tests for majority-class holdout evaluation semantics."""

import numpy as np
import pandas as pd
import pytest

from neural_networks.evaluation import compare_holdout_baselines


def test_majority_baseline_uses_training_majority_not_test_majority() -> None:
    """The baseline predicts the most common training label, then scores on test labels."""
    index = pd.date_range("2020-01-01", periods=520, freq="B")
    features = pd.DataFrame({"signal": np.arange(len(index), dtype=float)}, index=index)

    # With train_fraction=0.70, split_at=364 and horizon=0, training rows are 0..362.
    # Make class 1 the training majority, but class 0 the test majority.
    target_values = np.zeros(len(index), dtype=int)
    target_values[:200] = 1
    target_values[363:433] = 1  # 70 positive and 86 negative labels in the 156-row test set.
    target = pd.Series(target_values, index=index, name="target")

    comparison = compare_holdout_baselines(
        features, target, train_fraction=0.70, random_state=7, horizon=0
    )
    majority = comparison.loc[comparison["Model"] == "Majority-class"].iloc[0]

    assert target.iloc[:363].value_counts().idxmax() == 1
    assert target.iloc[364:].value_counts().idxmax() == 0
    assert majority["Accuracy"] == pytest.approx(70 / 156)
    assert majority["Balanced accuracy"] == pytest.approx(0.5)
    assert majority["ROC-AUC"] == pytest.approx(0.5)
