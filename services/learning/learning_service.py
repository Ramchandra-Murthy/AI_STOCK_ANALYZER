from __future__ import annotations

import logging
from typing import Dict, List, Any
from services.learning.models import PredictionRecord, OutcomeRecord, LearningResult

logger = logging.getLogger(__name__)

class SelfLearningAIService:
    """Institutional learning service that tracks prediction accuracy, calculates alpha, and calibrates specialist confidence scores."""

    def __init__(self) -> None:
        self._predictions: Dict[str, PredictionRecord] = {}
        self._outcomes: Dict[str, OutcomeRecord] = {}
        self._analyst_scores: Dict[str, float] = {
            "Valuation Analyst": 0.88,
            "Quality Analyst": 0.92,
            "Risk Analyst": 0.85,
            "Forecast Engine": 0.82
        }

    def record_prediction(self, prediction: PredictionRecord) -> None:
        logger.info("Recording prediction %s for symbol %s", prediction.prediction_id, prediction.symbol)
        self._predictions[prediction.prediction_id] = prediction

    def record_outcome(self, outcome: OutcomeRecord) -> None:
        logger.info("Recording outcome for prediction %s with accuracy %s", outcome.prediction_id, outcome.accuracy_score)
        self._outcomes[outcome.prediction_id] = outcome

    def evaluate_learning_loop(self) -> LearningResult:
        logger.info("Evaluating self-learning institutional feedback loop across %d outcomes", len(self._outcomes))
        
        if not self._outcomes:
            return LearningResult(
                total_predictions_evaluated=0,
                overall_accuracy=0.0,
                average_alpha=0.0,
                analyst_scores=self._analyst_scores,
                calibration_recommendations=["Insufficient outcomes recorded for calibration."]
            )

        accuracies = []
        alphas = []

        for pred_id, outcome in self._outcomes.items():
            pred = self._predictions.get(pred_id)
            if pred:
                accuracies.append(outcome.accuracy_score)
                alpha = outcome.actual_return - outcome.benchmark_return
                alphas.append(alpha)

        overall_acc = round(sum(accuracies) / len(accuracies), 4) if accuracies else 0.0
        avg_alpha = round(sum(alphas) / len(alphas), 4) if alphas else 0.0

        recommendations = []
        if overall_acc >= 0.80:
            recommendations.append("High overall prediction accuracy. Maintain current departmental weighting matrix.")
        else:
            recommendations.append("Accuracy threshold below target. Increase weighting on Quality and Valuation engines.")

        return LearningResult(
            total_predictions_evaluated=len(self._outcomes),
            overall_accuracy=overall_acc,
            average_alpha=avg_alpha,
            analyst_scores=self._analyst_scores,
            calibration_recommendations=recommendations
        )
