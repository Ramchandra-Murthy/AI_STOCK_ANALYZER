from __future__ import annotations

import pytest
from services.fundamentals.models import FinancialStatements
from services.scoring.engine import AIScoringEngine


def test_ai_scoring_evaluation() -> None:
    fs = FinancialStatements(symbol="RELIANCE.NS")
    engine = AIScoringEngine()
    result = engine.evaluate(fs)

    assert result.symbol == "RELIANCE.NS"
    assert 0.0 <= result.composite_score <= 100.0
    assert result.growth_score > 0.0
    assert result.quality_score > 0.0
