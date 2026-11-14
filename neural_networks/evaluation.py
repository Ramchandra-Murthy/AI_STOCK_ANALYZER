"""Chronological baselines and walk-forward evaluation for research models."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    brier_score_loss,
    log_loss,
    roc_auc_score,
)
from sklearn.model_selection import TimeSeriesSplit
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from neural_networks.baseline import chronological_split


def _pipeline(classifier: Any, *, scale: bool = True) -> Pipeline:
    steps: list[tuple[str, Any]] = [("imputer", SimpleImputer(strategy="median"))]
    if scale:
        steps.append(("scaler", StandardScaler()))
    steps.append(("classifier", classifier))
    return Pipeline(steps)


def _mlp(random_state: int) -> Pipeline:
    return _pipeline(
        MLPClassifier(
            hidden_layer_sizes=(32, 16),
            activation="relu",
            alpha=0.01,
            max_iter=300,
            early_stopping=False,
            random_state=random_state,
        )
    )


def _score_row(
    model_name: str,
    actual: pd.Series,
    predicted: Any,
    probability_up: Any | None = None,
    *,
    score_hard_label_auc: bool = False,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "Model": model_name,
        "Accuracy": float(accuracy_score(actual, predicted)),
        "Balanced accuracy": float(balanced_accuracy_score(actual, predicted)),
    }
    if probability_up is not None:
        probabilities = np.asarray(probability_up, dtype=float)
        labels = np.asarray(actual, dtype=int)
        row["Brier score"] = float(brier_score_loss(labels, probabilities))
        row["Log loss"] = float(log_loss(labels, probabilities, labels=[0, 1]))
        row["ROC-AUC"] = (
            float(roc_auc_score(labels, probabilities))
            if np.unique(labels).size == 2
            else float("nan")
        )
    else:
        row["Brier score"] = float("nan")
        row["Log loss"] = float("nan")
        # Hard labels are not probability scores. Keep ROC-AUC undefined by
        # default, with an explicit opt-in for the majority-class reference.
        row["ROC-AUC"] = (
            float(roc_auc_score(actual, np.asarray(predicted)))
            if score_hard_label_auc and np.unique(np.asarray(actual)).size == 2
            else float("nan")
        )
    return row


def compare_holdout_baselines(
    features: pd.DataFrame,
    target: pd.Series,
    train_fraction: float = 0.70,
    random_state: int = 42,
    horizon: int = 0,) -> pd.DataFrame:
    """Compare majority-class, logistic-regression, and MLP on a purged chronological holdout."""
    X_train, X_test, y_train, y_test = chronological_split(
        features, target, train_fraction, horizon
    )
    if y_train.nunique() < 2:
        raise ValueError("Training target must contain both classes")

    models = [
        (
            "Majority-class",
            _pipeline(
                DummyClassifier(strategy="most_frequent", random_state=random_state), scale=False
            ),
        ),
        (
            "Logistic regression",
            _pipeline(LogisticRegression(max_iter=1000, random_state=random_state)),
        ),
        ("MLP", _mlp(random_state)),
    ]
    rows = []
    for name, model in models:
        model.fit(X_train, y_train)
        predicted = model.predict(X_test)
        # The hard majority-class predictor is an accuracy reference, not a
        # meaningful probability forecast. Do not score its 0/1 probabilities
        # with Brier score or log loss.
        probability_up = None
        if name != "Majority-class" and hasattr(model, "predict_proba") and 1 in model.classes_:
            probability_up = model.predict_proba(X_test)[:, list(model.classes_).index(1)]
        rows.append(
            _score_row(
                name,
                y_test,
                predicted,
                probability_up,
                score_hard_label_auc=(name == "Majority-class"),
            )
        )

    # A constant training-prevalence forecast is a proper probabilistic
    # reference: it uses only the training labels and is evaluated on the
    # exact same holdout dates as the learned models.
    prevalence = float(y_train.mean())
    prevalence_probabilities = np.full(len(y_test), prevalence, dtype=float)
    prevalence_predictions = (prevalence_probabilities >= 0.5).astype(int)
    rows.insert(
        1,
        _score_row(
            "Training-prevalence probability baseline",
            y_test,
            prevalence_predictions,
            prevalence_probabilities,
        ),
    )
    return pd.DataFrame(rows)



def walk_forward_evaluation(
    features: pd.DataFrame,
    target: pd.Series,
    n_splits: int = 3,
    random_state: int = 42,
    horizon: int = 5,
) -> pd.DataFrame:
    """Compare probability and classification baselines on purged future folds.

    Every fold fits preprocessing and learned models on earlier observations
    only. The horizon-aware gap removes training labels whose forward outcome
    could overlap the test window. A training-prevalence forecast is included
    as a probability benchmark; it never uses test labels.
    """
    if not features.index.equals(target.index):
        raise ValueError("features and target must have identical indexes")
    if not features.index.is_unique or not features.index.is_monotonic_increasing:
        raise ValueError("features must have a unique chronological index")
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")
    if horizon < 1:
        raise ValueError("horizon must be at least 1")
    if target.isna().any() or not target.isin([0, 1]).all():
        raise ValueError("target must contain only non-null binary labels")

    splitter = TimeSeriesSplit(n_splits=n_splits, gap=horizon + 1)
    rows: list[dict[str, Any]] = []
    for fold_number, (train_indices, test_indices) in enumerate(splitter.split(features), start=1):
        X_train, X_test = features.iloc[train_indices], features.iloc[test_indices]
        y_train, y_test = target.iloc[train_indices], target.iloc[test_indices]
        if len(X_train) < 100 or len(X_test) < 30:
            raise ValueError(
                "Walk-forward evaluation needs at least 100 training and 30 test rows per fold"
            )
        if y_train.nunique() < 2:
            raise ValueError(f"Fold {fold_number} training target contains only one class")

        models = [
            (
                "Majority-class",
                _pipeline(
                    DummyClassifier(strategy="most_frequent", random_state=random_state),
                    scale=False,
                ),
            ),
            (
                "Logistic regression",
                _pipeline(
                    LogisticRegression(max_iter=1000, random_state=random_state + fold_number)
                ),
            ),
            ("MLP", _mlp(random_state + fold_number)),
        ]
        fold_rows: list[dict[str, Any]] = []
        for name, model in models:
            model.fit(X_train, y_train)
            predicted = model.predict(X_test)
            probability_up = None
            if name != "Majority-class" and hasattr(model, "predict_proba") and 1 in model.classes_:
                probability_up = model.predict_proba(X_test)[:, list(model.classes_).index(1)]
            row = _score_row(name, y_test, predicted, probability_up)
            fold_rows.append(row)

        # A constant forecast based only on the training fold is a proper
        # probabilistic benchmark for Brier score and log loss.
        prevalence = float(y_train.mean())
        prevalence_probabilities = np.full(len(y_test), prevalence, dtype=float)
        prevalence_predictions = (prevalence_probabilities >= 0.5).astype(int)
        fold_rows.append(
            _score_row(
                "Training-prevalence probability baseline",
                y_test,
                prevalence_predictions,
                prevalence_probabilities,
            )
        )

        for row in fold_rows:
            row.update(
                {
                    "Fold": fold_number,
                    "Train start": str(X_train.index[0].date()),
                    "Train end": str(X_train.index[-1].date()),
                    "Test start": str(X_test.index[0].date()),
                    "Test end": str(X_test.index[-1].date()),
                    "Train rows": len(train_indices),
                    "Test rows": len(test_indices),
                    "Train positive rate": prevalence,
                    "Test positive rate": float(y_test.mean()),
                }
            )
            rows.append(row)
    return pd.DataFrame(rows)

def summarize_probability_reliability(
    actual: Any,
    probabilities: Any,
    n_bins: int = 5,
) -> pd.DataFrame:
    """Compare mean predicted up-probability with observed up frequency by fixed bins.

    The table is descriptive holdout diagnostics, not proof of calibration or    profitable signals. Empty bins are omitted; small bin counts are noisy.
    """
    if n_bins < 2 or n_bins > 20:
        raise ValueError("n_bins must be between 2 and 20")
    actual_values = np.asarray(actual)
    probability_values = np.asarray(probabilities, dtype=float)
    if actual_values.ndim != 1 or probability_values.ndim != 1:
        raise ValueError("actual and probabilities must be one-dimensional")
    if len(actual_values) != len(probability_values):
        raise ValueError("actual and probabilities must have equal lengths")
    if len(actual_values) == 0:
        raise ValueError("actual and probabilities must not be empty")
    if not np.isin(actual_values, [0, 1]).all():
        raise ValueError("actual values must contain only binary labels 0 and 1")
    if (
        not np.isfinite(probability_values).all()
        or ((probability_values < 0) | (probability_values > 1)).any()
    ):
        raise ValueError("probabilities must be finite values between 0 and 1")

    edges = np.linspace(0.0, 1.0, n_bins + 1)
    bin_indices = np.minimum(np.digitize(probability_values, edges[1:-1]), n_bins - 1)
    rows: list[dict[str, Any]] = []
    for bin_number in range(n_bins):
        selected = bin_indices == bin_number
        if not selected.any():
            continue
        mean_probability = float(probability_values[selected].mean())
        observed_rate = float(actual_values[selected].mean())
        lower, upper = edges[bin_number], edges[bin_number + 1]
        rows.append(
            {
                "Probability band": f"{lower:.2f}–{upper:.2f}",
                "Samples": int(selected.sum()),
                "Mean predicted probability": mean_probability,
                "Observed up rate": observed_rate,
                "Calibration gap": observed_rate - mean_probability,
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "Probability band",
            "Samples",
            "Mean predicted probability",
            "Observed up rate",
            "Calibration gap",
        ],
    )


def summarize_probability_calibration(
    actual: Any,
    probabilities: Any,
    n_bins: int = 5,
) -> dict[str, float | int]:
    """Summarize holdout probability calibration using fixed-width bins.

    Expected calibration error is the sample-weighted mean absolute gap between
    each occupied bin's observed event rate and mean predicted probability.
    It is descriptive and depends on the selected bin count; it is not a
    guarantee of future calibration or trading performance.
    """
    actual_values = np.asarray(actual, dtype=float)
    probability_values = np.asarray(probabilities, dtype=float)
    reliability = summarize_probability_reliability(actual_values, probability_values, n_bins)
    if reliability.empty:
        raise ValueError("actual and probabilities must not be empty")

    sample_counts = reliability["Samples"].to_numpy(dtype=float)
    absolute_gaps = reliability["Calibration gap"].abs().to_numpy(dtype=float)
    total_samples = int(sample_counts.sum())
    expected_calibration_error = float(np.average(absolute_gaps, weights=sample_counts))
    return {
        "Samples": total_samples,
        "Mean predicted probability": float(probability_values.mean()),
        "Observed up rate": float(actual_values.mean()),
        "Expected calibration error": expected_calibration_error,
        "Maximum absolute calibration gap": float(absolute_gaps.max()),
    }


def permutation_feature_sensitivity(
    model: Any,
    features: pd.DataFrame,
    target: pd.Series,
    *,
    n_repeats: int = 5,
    random_state: int = 42,
) -> pd.DataFrame:
    """Rank holdout features by balanced-accuracy drop after permutation.

    This is a descriptive sensitivity diagnostic on the supplied holdout.
    Correlated features can mask one another, and repeated use of a holdout
    for interpretation can bias research conclusions. It is not causal evidence.
    """
    from sklearn.inspection import permutation_importance

    if not features.index.equals(target.index):
        raise ValueError("features and target must have identical indexes")
    if features.empty or target.empty:
        raise ValueError("features and target must not be empty")
    if n_repeats < 1:
        raise ValueError("n_repeats must be at least 1")
    if target.nunique() < 2:
        raise ValueError("target must contain both classes")

    result = permutation_importance(
        model,
        features,
        target,
        scoring="balanced_accuracy",
        n_repeats=n_repeats,
        random_state=random_state,
        n_jobs=1,
    )
    summary = pd.DataFrame(
        {
            "Feature": features.columns,
            "Balanced accuracy drop mean": result.importances_mean,
            "Balanced accuracy drop std": result.importances_std,
        }
    )
    return summary.sort_values(
        "Balanced accuracy drop mean", ascending=False, kind="stable"
    ).reset_index(drop=True)


def evaluate_mlp_seed_stability(
    features: pd.DataFrame,
    target: pd.Series,
    *,
    train_fraction: float = 0.70,
    horizon: int = 5,
    random_states: tuple[int, ...] = (7, 21, 42, 84, 126),
) -> pd.DataFrame:
    """Measure how MLP initialization seeds affect metrics on one fixed chronological holdout.

    This is a sensitivity check, not independent validation: all seeds share the
    same train/test dates, and repeated comparison on that holdout can bias research.
    """
    from sklearn.metrics import brier_score_loss

    if not features.index.equals(target.index):
        raise ValueError("features and target must have identical indexes")
    if len(random_states) < 2:
        raise ValueError("random_states must contain at least two seeds")
    if len(set(random_states)) != len(random_states):
        raise ValueError("random_states must be unique")
    X_train, X_test, y_train, y_test = chronological_split(
        features, target, train_fraction, horizon
    )
    if y_train.nunique() < 2:
        raise ValueError("Training target must contain both classes")
    if y_test.nunique() < 2:
        raise ValueError("Holdout target must contain both classes")

    rows: list[dict[str, Any]] = []
    for seed in random_states:
        model = _mlp(int(seed))        model.fit(X_train, y_train)
        predicted = model.predict(X_test)
        classes = list(model.classes_)
        if 1 not in classes:
            raise ValueError("Training target must contain the positive class 1")
        probability_up = model.predict_proba(X_test)[:, classes.index(1)]
        rows.append(
            {
                "Random seed": int(seed),
                "Accuracy": float(accuracy_score(y_test, predicted)),
                "Balanced accuracy": float(balanced_accuracy_score(y_test, predicted)),
                "ROC-AUC": float(roc_auc_score(y_test, probability_up)),
                "Brier score": float(brier_score_loss(y_test, probability_up)),
                "Train rows": int(len(X_train)),
                "Holdout rows": int(len(X_test)),
                "Train end": str(X_train.index[-1].date()),
                "Holdout start": str(X_test.index[0].date()),
                "Holdout end": str(X_test.index[-1].date()),
            }
        )
    return pd.DataFrame(rows)


def summarize_mlp_seed_stability(seed_results: pd.DataFrame) -> pd.DataFrame:
    """Summarize metric dispersion across MLP seeds evaluated on one shared holdout.

    This describes initialization sensitivity only. The runs are not independent
    validation samples because they reuse the same training and holdout observations.
    """
    if seed_results.empty:
        raise ValueError("Seed-stability results must not be empty")
    metrics = ["Accuracy", "Balanced accuracy", "ROC-AUC", "Brier score"]
    missing = sorted(set(metrics).difference(seed_results.columns))
    if missing:
        raise ValueError("Seed-stability results missing columns: " + ", ".join(missing))

    metric_values: dict[str, pd.Series] = {}
    for metric in metrics:
        values = pd.to_numeric(seed_results[metric], errors="coerce")
        if values.isna().any() or not np.isfinite(values.to_numpy(dtype=float)).all():
            raise ValueError(f"{metric} values must be finite numeric values")
        if ((values < 0) | (values > 1)).any():
            raise ValueError(f"{metric} values must be between 0 and 1")
        metric_values[metric] = values

    rows: list[dict[str, Any]] = []
    for metric in metrics:
        values = metric_values[metric]
        mean = float(values.mean())
        std = float(values.std(ddof=1)) if len(values) > 1 else 0.0
        minimum = float(values.min())
        maximum = float(values.max())
        rows.append(
            {
                "Metric": metric,
                "Runs": int(len(values)),
                "Mean": mean,
                "Std": std,
                "Min": minimum,
                "Max": maximum,
            }
        )
    return pd.DataFrame(rows)


def summarize_walk_forward_stability(fold_results: pd.DataFrame) -> pd.DataFrame:
    """Summarize fold-to-fold dispersion for each model without pooling models."""
    required = {"Model", "Fold", "Accuracy", "Balanced accuracy", "ROC-AUC"}
    missing = sorted(required.difference(fold_results.columns))
    if missing:
        raise ValueError("Walk-forward results missing columns: " + ", ".join(missing))
    if fold_results.empty:
        return pd.DataFrame(
            columns=[
                "Model",
                "Folds",
                "Accuracy mean",
                "Accuracy std",
                "Accuracy min",
                "Accuracy max",
                "Balanced accuracy mean",
                "Balanced accuracy std",
                "Balanced accuracy min",
                "Balanced accuracy max",
                "ROC-AUC mean",
                "ROC-AUC std",
                "ROC-AUC min",
                "ROC-AUC max",
            ]
        )

    metrics = ["Accuracy", "Balanced accuracy", "ROC-AUC"]
    rows: list[dict[str, Any]] = []
    for model_name, group in fold_results.groupby("Model", sort=False):
        row: dict[str, Any] = {"Model": model_name, "Folds": int(group["Fold"].nunique())}
        for metric in metrics:
            values = pd.to_numeric(group[metric], errors="coerce").dropna()
            row[f"{metric} mean"] = float(values.mean()) if not values.empty else float("nan")
            if len(values) > 1:
                row[f"{metric} std"] = float(values.std(ddof=1))
            elif len(values) == 1:
                row[f"{metric} std"] = 0.0
            else:
                row[f"{metric} std"] = float("nan")
            row[f"{metric} min"] = float(values.min()) if not values.empty else float("nan")
            row[f"{metric} max"] = float(values.max()) if not values.empty else float("nan")
        rows.append(row)
    return pd.DataFrame(rows)


def compare_feature_ablation(
    ohlcv: pd.DataFrame,
    horizon: int = 5,
    train_fraction: float = 0.70,
    random_state: int = 42,
) -> pd.DataFrame:
    """Compare original and expanded causal factors on identical chronological rows.

    This controlled ablation adapts the Cookbook's factor-research mindset:
    keep the target, holdout dates, and model settings fixed while comparing
    the incremental value of additional factors. It does not tune parameters
    on the holdout and does not imply that the expanded set will perform better.
    """
    from neural_networks.features import build_direction_dataset

    all_features, target = build_direction_dataset(ohlcv, horizon=horizon)
    original_columns = [
        "return_1d",
        "return_5d",
        "return_20d",
        "volatility_20d",
        "relative_volume_20d",
        "range_pct",
    ]
    missing = [column for column in original_columns if column not in all_features.columns]
    if missing:
        raise ValueError("Original feature columns missing: " + ", ".join(missing))

    # Both variants use the exact same labelled rows and chronological split.
    feature_sets = [
        ("Original factors", all_features.loc[:, original_columns]),
        ("Expanded factors", all_features),
    ]
    rows: list[dict[str, Any]] = []
    for feature_set_name, features in feature_sets:
        X_train, X_test, y_train, y_test = chronological_split(
            features, target, train_fraction, horizon
        )
        if y_train.nunique() < 2:
            raise ValueError("Training target must contain both classes")
        models = [
            (
                "Logistic regression",
                _pipeline(LogisticRegression(max_iter=1000, random_state=random_state)),
            ),
            ("MLP", _mlp(random_state)),
        ]
        for model_name, model in models:
            model.fit(X_train, y_train)
            predicted = model.predict(X_test)
            probability_up = None
            if hasattr(model, "predict_proba") and 1 in model.classes_:
                probability_up = model.predict_proba(X_test)[:, list(model.classes_).index(1)]
            row = _score_row(model_name, y_test, predicted, probability_up)
            row.update(
                {
                    "Feature set": feature_set_name,
                    "Feature count": int(features.shape[1]),
                    "Train start": str(features.index[0].date()),
                    "Train end": str(X_train.index[-1].date()),
                    "Test start": str(X_test.index[0].date()),
                    "Test end": str(X_test.index[-1].date()),
                    "Test rows": int(len(X_test)),
                }
            )
            rows.append(row)
    return pd.DataFrame(rows)[
        [
            "Feature set",
            "Model",