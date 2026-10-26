"""Chronological baselines and walk-forward evaluation for research models."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score
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
    model_name: str, actual: pd.Series, predicted: Any, probability_up: Any | None = None
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "Model": model_name,
        "Accuracy": float(accuracy_score(actual, predicted)),
        "Balanced accuracy": float(balanced_accuracy_score(actual, predicted)),
    }
    if probability_up is not None and actual.nunique() == 2:
        row["ROC-AUC"] = float(roc_auc_score(actual, probability_up))
    else:
        row["ROC-AUC"] = float("nan")
    return row


def compare_holdout_baselines(
    features: pd.DataFrame,
    target: pd.Series,
    train_fraction: float = 0.70,
    random_state: int = 42,
    horizon: int = 0,
) -> pd.DataFrame:
    """Compare majority-class, logistic-regression, and MLP on a purged chronological holdout."""
    X_train, X_test, y_train, y_test = chronological_split(features, target, train_fraction, horizon)
    if y_train.nunique() < 2:
        raise ValueError("Training target must contain both classes")

    models = [
        ("Majority-class", _pipeline(DummyClassifier(strategy="most_frequent"), scale=False)),
        ("Logistic regression", _pipeline(LogisticRegression(max_iter=1000))),
        ("MLP", _mlp(random_state)),
    ]
    rows = []
    for name, model in models:
        model.fit(X_train, y_train)
        predicted = model.predict(X_test)
        probability_up = None
        if hasattr(model, "predict_proba") and 1 in model.classes_:
            probability_up = model.predict_proba(X_test)[:, list(model.classes_).index(1)]
        rows.append(_score_row(name, y_test, predicted, probability_up))
    return pd.DataFrame(rows)


def walk_forward_evaluation(
    features: pd.DataFrame,
    target: pd.Series,
    n_splits: int = 3,
    random_state: int = 42,
    horizon: int = 5,
) -> pd.DataFrame:
    """Evaluate baselines on future folds with a horizon-aware embargo."""
    if not features.index.equals(target.index):
        raise ValueError("features and target must have identical indexes")
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")
    if horizon < 1:
        raise ValueError("horizon must be at least 1")
    # Exclude boundary rows whose forward outcome could reach into the test fold.
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
            ("Majority-class", _pipeline(DummyClassifier(strategy="most_frequent"), scale=False)),
            ("Logistic regression", _pipeline(LogisticRegression(max_iter=1000))),
            ("MLP", _mlp(random_state + fold_number)),
        ]
        for name, model in models:
            model.fit(X_train, y_train)
            predicted = model.predict(X_test)
            probability_up = None
            if hasattr(model, "predict_proba") and 1 in model.classes_:
                probability_up = model.predict_proba(X_test)[:, list(model.classes_).index(1)]
            row = _score_row(name, y_test, predicted, probability_up)
            row.update(
                {
                    "Fold": fold_number,
                    "Train start": str(features.index[train_indices[0]].date()),
                    "Train end": str(features.index[train_indices[-1]].date()),
                    "Test start": str(features.index[test_indices[0]].date()),
                    "Test end": str(features.index[test_indices[-1]].date()),
                    "Train rows": len(train_indices),
                    "Test rows": len(test_indices),
                }
            )
            rows.append(row)
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
        X_train, X_test, y_train, y_test = chronological_split(features, target, train_fraction, horizon)
        if y_train.nunique() < 2:
            raise ValueError("Training target must contain both classes")
        models = [
            ("Logistic regression", _pipeline(LogisticRegression(max_iter=1000))),
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
            "Feature count",
            "Accuracy",
            "Balanced accuracy",
            "ROC-AUC",
            "Train start",
            "Train end",
            "Test start",
            "Test end",
            "Test rows",
        ]
    ]


def _block_bootstrap_spearman_ic_interval(
    factor_values: pd.Series,
    forward_returns: pd.Series,
    *,
    n_bootstrap: int = 200,
    block_size: int = 5,
    confidence_level: float = 0.95,
    random_state: int = 42,
) -> tuple[float, float]:
    """Estimate a percentile interval for Spearman IC using moving-block resampling.

    Contiguous blocks preserve some local dependence. This is a descriptive
    uncertainty estimate, not a formal significance test or proof of predictability.
    """
    if n_bootstrap < 50:
        raise ValueError("n_bootstrap must be at least 50")
    if block_size < 1:
        raise ValueError("block_size must be at least 1")
    pair = (
        pd.concat([factor_values, forward_returns], axis=1)
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )
    n = len(pair)
    if n < max(10, block_size * 2):
        return float("nan"), float("nan")
    first_unique = pair.iloc[:, 0].nunique(dropna=True)
    second_unique = pair.iloc[:, 1].nunique(dropna=True)
    if min(first_unique, second_unique) < 2:
        return float("nan"), float("nan")

    values = pair.to_numpy(dtype=float)
    block_size = min(block_size, n)
    starts = np.arange(n - block_size + 1)
    rng = np.random.default_rng(random_state)
    estimates: list[float] = []
    blocks_needed = int(np.ceil(n / block_size))
    for _ in range(n_bootstrap):
        sampled_starts = rng.choice(starts, size=blocks_needed, replace=True)
        positions = np.concatenate(
            [np.arange(start, start + block_size) for start in sampled_starts]
        )[:n]
        sample = pd.DataFrame(values[positions])
        estimate = sample.iloc[:, 0].corr(sample.iloc[:, 1], method="spearman")
        if pd.notna(estimate):
            estimates.append(float(estimate))
    if len(estimates) < max(30, int(n_bootstrap * 0.5)):
        return float("nan"), float("nan")
    tail = (1.0 - confidence_level) / 2.0
    lower, upper = np.quantile(estimates, [tail, 1.0 - tail])
    return float(lower), float(upper)


def factor_information_coefficient(
    ohlcv: pd.DataFrame,
    horizon: int = 5,
    n_windows: int = 5,
    n_bootstrap: int = 200,
    block_size: int = 5,
    confidence_level: float = 0.95,
) -> pd.DataFrame:
    """Summarize factor rank correlation with forward returns by chronological window.

    Positive IC means higher factor values tended to coincide with higher forward
    returns within that window. IC is descriptive, not a trading strategy or a
    guarantee of out-of-sample predictive value.
    """
    from neural_networks.features import REQUIRED_COLUMNS, build_features

    if horizon < 1:
        raise ValueError("horizon must be at least 1")
    if n_windows < 2:
        raise ValueError("n_windows must be at least 2")
    if n_bootstrap < 50:
        raise ValueError("n_bootstrap must be at least 50")
    if block_size < 1:
        raise ValueError("block_size must be at least 1")
    if not 0 < confidence_level < 1:
        raise ValueError("confidence_level must be between 0 and 1")
    missing = [column for column in REQUIRED_COLUMNS if column not in ohlcv.columns]
    if missing:
        raise ValueError("Missing required OHLCV columns: " + ", ".join(missing))

    frame = ohlcv.loc[:, REQUIRED_COLUMNS].copy().sort_index()
    close = pd.to_numeric(frame["Close"], errors="coerce").astype(float)
    entry_close = close.shift(-1)
    exit_close = close.shift(-(horizon + 1))
    forward_return = exit_close / entry_close - 1.0
    features = build_features(frame)
    valid = (
        features.notna().all(axis=1)
        & forward_return.notna()
        & entry_close.gt(0)
        & exit_close.gt(0)
        & close.gt(0)
    )
    features = features.loc[valid]
    forward_return = forward_return.loc[valid]
    if len(features) < n_windows * 10:
        raise ValueError(
            f"Need at least {n_windows * 10} valid observations for {n_windows} IC windows"
        )

    window_indices = [
        part for part in np.array_split(np.arange(len(features)), n_windows) if len(part)
    ]
    rows: list[dict[str, Any]] = []
    for factor in features.columns:
        correlations: list[float] = []
        for window_number, positions in enumerate(window_indices, start=1):
            factor_values = features.iloc[list(positions)][factor]
            returns = forward_return.iloc[list(positions)]
            pair = pd.concat([factor_values, returns], axis=1).dropna()
            ic = float(pair.iloc[:, 0].corr(pair.iloc[:, 1], method="spearman"))
            if pd.isna(ic):
                ic = float("nan")
            correlations.append(ic)
            ci_lower, ci_upper = _block_bootstrap_spearman_ic_interval(
                pair.iloc[:, 0],
                pair.iloc[:, 1],
                n_bootstrap=n_bootstrap,
                block_size=block_size,
                confidence_level=confidence_level,
                random_state=42 + window_number,
            )
            rows.append(
                {
                    "Factor": factor,
                    "Window": window_number,
                    "Window start": str(pair.index.min().date()) if not pair.empty else "",
                    "Window end": str(pair.index.max().date()) if not pair.empty else "",
                    "Observations": int(len(pair)),
                    "Spearman IC": ic,
                    "IC CI lower": ci_lower,
                    "IC CI upper": ci_upper,
                }
            )
        valid_ics = [value for value in correlations if pd.notna(value)]
        summary = {
            "Factor": factor,
            "Window": "Summary",
            "Window start": str(features.index.min().date()),
            "Window end": str(features.index.max().date()),
            "Observations": int(len(features)),
            "Spearman IC": (float(sum(valid_ics) / len(valid_ics)) if valid_ics else float("nan")),
            "IC CI lower": float("nan"),
            "IC CI upper": float("nan"),
            "IC standard deviation": (
                float(pd.Series(valid_ics).std(ddof=0)) if valid_ics else float("nan")
            ),
            "Positive windows": int(sum(value > 0 for value in valid_ics)),
            "Valid windows": int(len(valid_ics)),
        }
        rows.append(summary)
    return pd.DataFrame(rows)
