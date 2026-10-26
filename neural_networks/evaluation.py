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
    X_train, X_test, y_train, y_test = chronological_split(
        features, target, train_fraction, horizon
    )
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


def summarize_probability_reliability(
    actual: Any,
    probabilities: Any,
    n_bins: int = 5,
) -> pd.DataFrame:
    """Compare mean predicted up-probability with observed up frequency by fixed bins.

    The table is descriptive holdout diagnostics, not proof of calibration or
    profitable signals. Empty bins are omitted; small bin counts are noisy.
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
        model = _mlp(int(seed))
        model.fit(X_train, y_train)
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


def compare_mlp_configurations(
    features: pd.DataFrame,
    target: pd.Series,
    *,
    configurations: tuple[tuple[tuple[int, ...], float], ...] = (
        ((8,), 0.01),
        ((16,), 0.1),
        ((16, 8), 0.1),
        ((32, 16), 0.01),
    ),
    n_splits: int = 3,
    horizon: int = 5,
    random_state: int = 42,
) -> pd.DataFrame:
    """Compare MLP configurations on expanding chronological validation folds.

    This reports validation diagnostics only. It does not select or deploy a
    model automatically, and the final untouched test period must remain unused.
    """
    if not features.index.equals(target.index):
        raise ValueError("features and target must have identical indexes")
    if features.empty or target.empty:
        raise ValueError("features and target must not be empty")
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")
    if horizon < 1:
        raise ValueError("horizon must be at least 1")
    if not configurations:
        raise ValueError("at least one MLP configuration is required")
    for hidden_layers, alpha in configurations:
        if not hidden_layers or any(width < 1 for width in hidden_layers):
            raise ValueError("hidden layer sizes must be positive integers")
        if alpha <= 0 or not np.isfinite(alpha):
            raise ValueError("alpha must be finite and positive")

    splitter = TimeSeriesSplit(n_splits=n_splits, gap=horizon + 1)
    rows: list[dict[str, Any]] = []
    for fold_number, (train_indices, test_indices) in enumerate(
        splitter.split(features), start=1
    ):
        X_train, X_test = features.iloc[train_indices], features.iloc[test_indices]
        y_train, y_test = target.iloc[train_indices], target.iloc[test_indices]
        if len(X_train) < 100 or len(X_test) < 30:
            raise ValueError(
                "MLP configuration validation needs at least 100 training and 30 test rows per fold"
            )
        if y_train.nunique() < 2:
            raise ValueError(f"Fold {fold_number} training target contains only one class")
        for config_number, (hidden_layers, alpha) in enumerate(configurations, start=1):
            network = MLPClassifier(
                hidden_layer_sizes=hidden_layers,
                activation="relu",
                alpha=float(alpha),
                max_iter=300,
                early_stopping=False,
                random_state=random_state + fold_number,
            )
            model = _pipeline(network)
            model.fit(X_train, y_train)
            probabilities = model.predict_proba(X_test)[:, list(model.classes_).index(1)]
            predicted = model.predict(X_test)
            row = _score_row("MLP", y_test, predicted, probabilities)
            row.update(
                {
                    "Brier score": float(np.mean((probabilities - y_test.to_numpy()) ** 2)),
                    "Log loss": float(
                        -np.mean(
                            y_test.to_numpy() * np.log(np.clip(probabilities, 1e-15, 1 - 1e-15))
                            + (1 - y_test.to_numpy())
                            * np.log(np.clip(1 - probabilities, 1e-15, 1 - 1e-15))
                        )
                    ),
                }
            )
            row.update(
                {
                    "Configuration": config_number,
                    "Hidden layers": str(hidden_layers),
                    "Alpha": float(alpha),
                    "Fold": fold_number,
                    "Train rows": int(len(X_train)),
                    "Validation rows": int(len(X_test)),
                    "Train end": str(features.index[train_indices[-1]].date()),
                    "Validation start": str(features.index[test_indices[0]].date()),
                    "Validation end": str(features.index[test_indices[-1]].date()),
                    "Training iterations": int(network.n_iter_),
                    "Reached iteration limit": bool(network.n_iter_ >= network.max_iter),
                }
            )
            rows.append(row)
    return pd.DataFrame(rows)
