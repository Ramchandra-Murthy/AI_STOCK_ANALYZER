from services.market_data.confidence_trace import (
    ConfidenceAuditLogger,
)
from services.market_data.decision_gate import MarketDataDecisionGate
from services.market_data.integrity import MarketDataValidationReport


def test_block23k_path_live():
    report = MarketDataValidationReport(
        symbol="RELIANCE.NS",
        data_state="LIVE",
        is_valid=True,
        errors=[],
        freshness_age_seconds=10.0,
    )
    decision = MarketDataDecisionGate.evaluate_decision(report)
    trace = ConfidenceAuditLogger.create_trace(
        symbol="RELIANCE.NS",
        raw_state="LIVE",
        valid=True,
        directive=decision.directive,
        base_conf=0.85,
        penalty=decision.confidence_penalty,
        adj_conf=0.85,
        composite_score=82.4,
        action="BUY",
    )
    assert trace.raw_data_state == "LIVE"
    assert trace.decision_directive == "USE_LIVE"
    assert trace.confidence_penalty == 0.0
    assert trace.adjusted_confidence == 0.85


def test_block23k_path_fallback():
    report = MarketDataValidationReport(
        symbol="INFY.NS",
        data_state="FALLBACK",
        is_valid=True,
        errors=[],
        freshness_age_seconds=100.0,
    )
    decision = MarketDataDecisionGate.evaluate_decision(report)
    trace = ConfidenceAuditLogger.create_trace(
        symbol="INFY.NS",
        raw_state="FALLBACK",
        valid=True,
        directive=decision.directive,
        base_conf=0.85,
        penalty=decision.confidence_penalty,
        adj_conf=0.70,
        composite_score=82.4,
        action="BUY",
    )
    assert trace.raw_data_state == "FALLBACK"
    assert trace.decision_directive == "USE_FALLBACK_WITH_WARNING"
    assert trace.confidence_penalty == 0.15
    assert trace.adjusted_confidence == 0.70


def test_block23k_path_stale():
    report = MarketDataValidationReport(
        symbol="TCS.NS", data_state="STALE", is_valid=True, errors=[], freshness_age_seconds=95000.0
    )
    decision = MarketDataDecisionGate.evaluate_decision(report)
    trace = ConfidenceAuditLogger.create_trace(
        symbol="TCS.NS",
        raw_state="STALE",
        valid=True,
        directive=decision.directive,
        base_conf=0.85,
        penalty=decision.confidence_penalty,
        adj_conf=0.55,
        composite_score=82.4,
        action="HOLD",
    )
    assert trace.raw_data_state == "STALE"
    assert trace.decision_directive == "USE_STALE_WITH_WARNING"
    assert trace.confidence_penalty == 0.30
    assert trace.adjusted_confidence == 0.55


def test_block23k_path_invalid():
    report = MarketDataValidationReport(
        symbol="BAD.NS",
        data_state="INVALID",
        is_valid=False,
        errors=["Negative price"],
        freshness_age_seconds=0.0,
    )
    decision = MarketDataDecisionGate.evaluate_decision(report)
    trace = ConfidenceAuditLogger.create_trace(
        symbol="BAD.NS",
        raw_state="INVALID",
        valid=False,
        directive=decision.directive,
        base_conf=0.85,
        penalty=decision.confidence_penalty,
        adj_conf=0.0,
        composite_score=0.0,
        action="REJECT_DATA",
    )
    assert trace.raw_data_state == "INVALID"
    assert trace.decision_directive == "REJECT_DATA"
    assert trace.confidence_penalty == 1.0
    assert trace.validation_status is False
