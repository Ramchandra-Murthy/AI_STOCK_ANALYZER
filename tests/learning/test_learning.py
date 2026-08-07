from __future__ import annotations

import pytest
from services.learning.models import PredictionRecord, OutcomeRecord
from services.learning.learning_service import SelfLearningAIService

def test_self_learning_ai_service() -> None:
    service = SelfLearningAIService()

    pred = PredictionRecord(
        prediction_id="PRED-SLI-001",
        symbol="RELIANCE.NS",
        recommendation="BUY",
        expected_return=0.18,
        expected_value=3200.0,
        confidence=0.91,
        model_version="v1.0"
    )
    service.record_prediction(pred)

    outcome = OutcomeRecord(
        prediction_id="PRED-SLI-001",
        actual_return=0.16,
        actual_price=2950.0,
        benchmark_return=0.10,
        accuracy_score=0.89
    )
    service.record_outcome(outcome)

    result = service.evaluate_learning_loop()
    assert result.total_predictions_evaluated == 1
    assert result.overall_accuracy == 0.89
    assert result.average_alpha == 0.06
    assert "Valuation Analyst" in result.analyst_scores
    assert len(result.calibration_recommendations) > 0
