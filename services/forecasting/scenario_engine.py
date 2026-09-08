from __future__ import annotations

import logging
from typing import List

from services.forecasting.models import ForecastScenario, ForecastResult

logger = logging.getLogger(__name__)


class ScenarioIntelligenceEngine:
    """Institutional forecasting engine for probability-weighted scenarios."""

    @classmethod
    def evaluate_scenarios(cls, symbol: str, scenarios: List[ForecastScenario]) -> ForecastResult:
        logger.info("Evaluating %d forecast scenarios for %s", len(scenarios), symbol)
        if not symbol or not str(symbol).strip():
            raise ValueError("symbol is required")
        if not scenarios:
            raise ValueError(f"Cannot evaluate scenarios without data for {symbol}.")

        probabilities = [float(s.probability) for s in scenarios]
        if any(p < 0.0 or p > 1.0 for p in probabilities):
            raise ValueError(f"Scenario probabilities must be between 0 and 1 for {symbol}.")
        total_probability = sum(probabilities)
        if abs(total_probability - 1.0) > 1e-6:
            raise ValueError(
                f"Scenario probabilities must sum to 1.0 for {symbol}; got {total_probability:.6f}."
            )

        values = [float(s.intrinsic_value) for s in scenarios]
        expected_val = sum(value * probability for value, probability in zip(values, probabilities))
        bull_candidates = [float(s.intrinsic_value) for s in scenarios if s.name.upper() == "BULL"]
        bear_candidates = [float(s.intrinsic_value) for s in scenarios if s.name.upper() == "BEAR"]
        base_candidates = [float(s.intrinsic_value) for s in scenarios if s.name.upper() == "BASE"]
        bull_val = max(bull_candidates) if bull_candidates else expected_val
        base_val = base_candidates[0] if base_candidates else expected_val
        bear_val = min(bear_candidates) if bear_candidates else expected_val

        prob_dist = {s.name: float(s.probability) for s in scenarios}
        concentration = sum(p * p for p in probabilities)
        confidence = round(max(0.0, min(1.0, 1.0 - concentration)), 4)

        key_drivers = [
            "Revenue Growth Acceleration",
            "Operating Margin Expansion",
            "Capital Cost Discipline",
        ]
        major_risks = [
            "Interest Rate Volatility",
            "Input Cost Inflation",
            "Demand Compression",
        ]
        assumptions = [
            "Scenario values and probabilities are supplied by the upstream forecasting pipeline.",
            "Expected value is probability-weighted across supplied scenarios.",
            "Confidence is derived from scenario probability concentration.",
        ]

        return ForecastResult(
            symbol=str(symbol).strip().upper(),
            expected_value=round(expected_val, 2),
            bull_value=round(bull_val, 2),
            base_value=round(base_val, 2),
            bear_value=round(bear_val, 2),
            confidence=confidence,
            probability_distribution=prob_dist,
            key_drivers=key_drivers,
            major_risks=major_risks,
            assumptions=assumptions,
        )
