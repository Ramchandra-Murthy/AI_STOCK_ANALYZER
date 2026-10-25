"""Chronological baselines and walk-forward evaluation for research models."""

from __future__ import annotations

from typing import Any

import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit

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
) -> pd.DataFrame:
    """Compare majority-class, logistic-regression, and MLP on one chronological holdout."""
    X_train, X_test, y_train, y_test = chronological_split(
        features, target, train_fraction
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
) -> pd.DataFrame:
    """Evaluate baselines on successive, non-overlapping future folds."""
    if not features.index.equals(target.index):
        raise ValueError("features and target must have identical indexes")
    if n_splits < 2:
        raise ValueError("n_splits must be at least 2")
    splitter = TimeSeriesSplit(n_splits=n_splits)
    rows: list[dict[str, Any]] = []
    for fold_number, (train_indices, test_indices) in enumerate(
        splitter.split(features), start=1
    ):
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
