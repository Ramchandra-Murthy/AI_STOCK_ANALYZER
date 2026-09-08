from __future__ import annotations
import logging
from typing import List
from services.forecasting.models import ForecastScenario, ForecastResult

logger = logging.getLogger(__name__)

class ScenarioIntelligenceEngine:
    """Calculate probabilistic scenario values from supplied scenario evidence."""

    @classmethod
    def evaluate_scenarios(cls, symbol: str, scenarios: List[ForecastScenario]) -> ForecastResult:
        if not scenarios:
            raise ValueError(f"Cannot evaluate scenarios without data for {symbol}.")
        probabilities = [float(s.probability) for s in scenarios]
        if any(p < 0 or p > 1 for p in probabilities):
            raise ValueError(f"Scenario probabilities must be between 0 and 1 for {symbol}.")
        total_probability = sum(probabilities)
        if abs(total_probability - 1.0) > 1e-6:
            raise ValueError(f"Scenario probabilities must sum to 1.0 for {symbol}; got {total_probability:.6f}.")
        expected_val = sum(float(s.intrinsic_value) * float(s.probability) for s in scenarios)
        bull_val = max((float(s.intrinsic_value) for s in scenarios if s.name.upper() == "BULL"), default=expected_val)
        base_val = next((float(s.intrinsic_value) for s in scenarios if s.name.upper() == "BASE"), expected_val)
        bear_val = min((float(s.intrinsic_value) for s in scenarios if s.name.upper() == "BEAR"), default=expected_val)
        concentration = sum(p * p for p in probabilities)
        confidence = round(max(0.0, min(1.0, 1.0 - concentration)), 4)
        return ForecastResult(
            symbol=symbol, expected_value=round(expected_val, 2),
            bull_value=round(bull_val, 2), base_value=round(base_val, 2),
            bear_value=round(bear_val, 2), confidence=confidence,
            probability_distribution={s.name: s.probability for s in scenarios},
            key_drivers=["Revenue Growth Acceleration", "Operating Margin Expansion", "Capital Cost Discipline"],
            major_risks=["Interest Rate Volatility", "Input Cost Inflation", "Demand Compression"],
            assumptions=[
                "Scenario values and probabilities supplied by the upstream forecasting pipeline.",
                "Expected value is probability-weighted across supplied scenarios.",
                "Confidence is derived from scenario probability concentration.",
            ],
        )
