"""Tests for chronological MLP configuration summary metrics."""

import numpy as np
import pandas as pd
import pytest

from neural_networks.evaluation import summarize_mlp_configuration_results


def _fold_results() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Configuration": 1,
                "Hidden layers": "(8,)",
                "Alpha": 0.01,
                "Fold": 1,
                "Accuracy": 0.6,
                "Balanced accuracy": 0.58,
                "ROC-AUC": 0.62,
                "Brier score": 0.22,
                "Log loss": 0.65,
                "Training iterations": 120,
                "Reached iteration limit": False,
            },
            {
                "Configuration": 1,
                "Hidden layers": "(8,)",
                "Alpha": 0.01,
                "Fold": 2,
                "Accuracy": 0.7,
                "Balanced accuracy": 0.68,
                "ROC-AUC": 0.72,
                "Brier score": 0.18,
                "Log loss": 0.55,
                "Training iterations": 300,
                "Reached iteration limit": True,
            },
        ]
    )


def test_summary_aggregates_metrics_across_folds() -> None:
    summary = summarize_mlp_configuration_results(_fold_results())

    assert len(summary) == 1
    row = summary.iloc[0]
    assert row["Folds"] == 2
    assert row["Accuracy mean"] == pytest.approx(0.65)
    assert row["Accuracy min"] == pytest.approx(0.6)
    assert row["Accuracy max"] == pytest.approx(0.7)
    assert row["Accuracy std"] == pytest.approx(np.std([0.6, 0.7], ddof=1))
    assert row["Iteration-limit folds"] == 1


def test_summary_keeps_undefined_roc_auc_out_of_aggregates() -> None:
    results = _fold_results()
    results.loc[0, "ROC-AUC"] = np.nan

    summary = summarize_mlp_configuration_results(results)

    assert summary.iloc[0]["ROC-AUC mean"] == pytest.approx(0.72)
    assert summary.iloc[0]["ROC-AUC std"] == 0.0


def test_summary_rejects_duplicate_configuration_fold_rows() -> None:
    results = pd.concat([_fold_results(), _fold_results().iloc[[0]]], ignore_index=True)

    with pytest.raises(ValueError, match="only one row per fold"):
        summarize_mlp_configuration_results(results)


def test_summary_rejects_out_of_range_metrics() -> None:
    results = _fold_results()
    results.loc[0, "Brier score"] = 1.2

    with pytest.raises(ValueError, match="Brier score"):
        summarize_mlp_configuration_results(results)
