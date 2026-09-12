from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class PredictionRecord:
    prediction_id: str
    symbol: str
    recommendation: str  # "BUY", "HOLD", "SELL"
    expected_return: float
    expected_value: float
    confidence: float
    model_version: str = "v1.0"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass(frozen=True)
class OutcomeRecord:
    prediction_id: str
    actual_return: float
    actual_price: float
    benchmark_return: float
    accuracy_score: float  # 0.0 to 1.0
    evaluated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass(frozen=True)
class LearningResult:
    total_predictions_evaluated: int
    overall_accuracy: float
    average_alpha: float
    analyst_scores: dict[str, float]
    calibration_recommendations: list[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
