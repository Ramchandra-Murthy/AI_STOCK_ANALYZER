from services.market_data.integrity import MarketDataValidationReport
from services.market_data.decision_gate import MarketDataDecisionGate
from services.market_data.confidence_trace import ConfidenceAuditLogger


def trace_for(report):
    decision = MarketDataDecisionGate.evaluate_decision(report)
    return decision, ConfidenceAuditLogger.create_trace(
        symbol=report.symbol,
        raw_state=report.data_state,
        valid=report.is_valid,
        directive=decision.directive,
        base_conf=0.85,
        penalty=decision.confidence_penalty,
        adj_conf=0.85 if decision.allowed_in_scoring else 0.0,
        composite_score=82.4 if decision.allowed_in_scoring else 0.0,
        action="BUY" if decision.allowed_in_scoring else "REJECT_DATA",
    )


def test_block23k_path_live():
    report = MarketDataValidationReport(
        symbol="RELIANCE.NS", data_state="LIVE", is_valid=True,
        errors=[], freshness_age_seconds=10.0
    )
    decision, trace = trace_for(report)
    assert decision.directive == "USE_LIVE"
    assert trace.raw_data_state == "LIVE"
    assert trace.confidence_penalty == 0.0
    assert trace.adjusted_confidence == 0.85


def test_block23k_path_fallback_is_rejected():
    report = MarketDataValidationReport(
        symbol="INFY.NS", data_state="FALLBACK", is_valid=False,
        errors=[], freshness_age_seconds=100.0
    )
    decision, trace = trace_for(report)
    assert decision.directive == "REJECT_FALLBACK"
    assert decision.allowed_in_scoring is False
    assert trace.adjusted_confidence == 0.0
    assert trace.final_investment_action == "REJECT_DATA"


def test_block23k_path_stale_is_rejected():
    report = MarketDataValidationReport(
        symbol="TCS.NS", data_state="STALE", is_valid=False,
        errors=[], freshness_age_seconds=95000.0
    )
    decision, trace = trace_for(report)
    assert decision.directive == "REJECT_STALE"
    assert decision.allowed_in_scoring is False
    assert trace.adjusted_confidence == 0.0
    assert trace.final_investment_action == "REJECT_DATA"


def test_block23k_path_invalid():
    report = MarketDataValidationReport(
        symbol="BAD.NS", data_state="INVALID", is_valid=False,
        errors=["Negative price"], freshness_age_seconds=0.0
    )
    decision, trace = trace_for(report)
    assert trace.raw_data_state == "INVALID"
    assert trace.decision_directive == "REJECT_DATA"
    assert trace.confidence_penalty == 1.0
    assert trace.adjusted_confidence == 0.0
    assert trace.validation_status is False
