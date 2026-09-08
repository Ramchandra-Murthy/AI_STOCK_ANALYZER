from services.market_data.integrity import MarketDataValidationReport
from services.market_data.decision_gate import MarketDataDecisionGate


def test_block23f_decision_gate_live():
    report = MarketDataValidationReport(
        symbol="RELIANCE.NS",
        data_state="LIVE",
        is_valid=True,
        errors=[],
        freshness_age_seconds=10.0,
    )
    res = MarketDataDecisionGate.evaluate_decision(report)
    assert res.directive == "USE_LIVE"
    assert res.allowed_in_scoring is True
    assert res.confidence_penalty == 0.0


def test_block23f_decision_gate_fallback_is_blocked():
    report = MarketDataValidationReport(
        symbol="INFY.NS",
        data_state="FALLBACK",
        is_valid=False,
        errors=[],
        freshness_age_seconds=100.0,
    )
    res = MarketDataDecisionGate.evaluate_decision(report)
    assert res.directive == "REJECT_FALLBACK"
    assert res.allowed_in_scoring is False
    assert res.confidence_penalty == 1.0
    assert res.warning_message is not None


def test_block23f_decision_gate_stale_is_blocked():
    report = MarketDataValidationReport(
        symbol="TCS.NS",
        data_state="STALE",
        is_valid=False,
        errors=[],
        freshness_age_seconds=95000.0,
    )
    res = MarketDataDecisionGate.evaluate_decision(report)
    assert res.directive == "REJECT_STALE"
    assert res.allowed_in_scoring is False
    assert res.confidence_penalty == 1.0


def test_block23f_decision_gate_invalid():
    report = MarketDataValidationReport(
        symbol="BAD.NS",
        data_state="INVALID",
        is_valid=False,
        errors=["Negative price"],
        freshness_age_seconds=0.0,
    )
    res = MarketDataDecisionGate.evaluate_decision(report)
    assert res.directive == "REJECT_DATA"
    assert res.allowed_in_scoring is False
    assert res.confidence_penalty == 1.0
