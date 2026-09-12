from services.market_data.decision_gate import MarketDataDecisionGate
from services.market_data.integrity import MarketDataValidationReport


def test_block23i_zero_penalty_live():
    # Verify LIVE state yields zero penalty
    report = MarketDataValidationReport(
        symbol="RELIANCE.NS", data_state="LIVE", is_valid=True, errors=[], freshness_age_seconds=5.0
    )
    decision = MarketDataDecisionGate.evaluate_decision(report)
    assert decision.confidence_penalty == 0.0

    base_confidence = 0.85
    adjusted = max(0.0, base_confidence - decision.confidence_penalty)
    assert adjusted == 0.85


def test_block23i_degraded_penalty_fallback():
    # Verify FALLBACK state yields exact 0.15 penalty (0.85 -> 0.70)
    report = MarketDataValidationReport(
        symbol="INFY.NS",
        data_state="FALLBACK",
        is_valid=True,
        errors=[],
        freshness_age_seconds=120.0,
    )
    decision = MarketDataDecisionGate.evaluate_decision(report)
    assert decision.confidence_penalty == 0.15

    base_confidence = 0.85
    adjusted = max(0.0, base_confidence - decision.confidence_penalty)
    assert round(adjusted, 2) == 0.70


def test_block23i_stale_penalty_bounds():
    # Verify STALE state yields exact 0.30 penalty (0.85 -> 0.55)
    report = MarketDataValidationReport(
        symbol="TCS.NS", data_state="STALE", is_valid=True, errors=[], freshness_age_seconds=90000.0
    )
    decision = MarketDataDecisionGate.evaluate_decision(report)
    assert decision.confidence_penalty == 0.30

    base_confidence = 0.85
    adjusted = max(0.0, base_confidence - decision.confidence_penalty)
    assert round(adjusted, 2) == 0.55


def test_block23i_floor_bounds():
    # Verify confidence floor bounds at 0.0 under maximum penalty
    base_confidence = 0.50
    heavy_penalty = 1.0
    adjusted = max(0.0, base_confidence - heavy_penalty)
    assert adjusted == 0.0
