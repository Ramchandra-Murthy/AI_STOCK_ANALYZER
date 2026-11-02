"""Tests for comparable probability metrics in model evaluation."""

import numpy as np
import pandas as pd
import pytest

from neural_networks.evaluation import _score_row


def test_score_row_reports_brier_and_log_loss_for_probabilities() -> None:
    actual = pd.Series([0, 1, 1, 0])
    probabilities = np.array([0.2, 0.7, 0.8, 0.4])

    row = _score_row("example", actual, np.array([0, 1, 1, 0]), probabilities)

    expected_brier = np.mean((probabilities - actual.to_numpy()) ** 2)
    assert row["Brier score"] == pytest.approx(expected_brier)
    assert row["Log loss"] > 0
    assert 0 <= row["ROC-AUC"] <= 1


def test_score_row_marks_probability_metrics_undefined_without_probabilities() -> None:
    row = _score_row("example", pd.Series([0, 1]), np.array([0, 1]))

    assert np.isnan(row["Brier score"])
    assert np.isnan(row["Log loss"])
    assert np.isnan(row["ROC-AUC"])
