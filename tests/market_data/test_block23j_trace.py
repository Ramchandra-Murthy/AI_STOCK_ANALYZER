from services.market_data.confidence_trace import ConfidenceAuditLogger, ConfidenceDecisionTraceRecord

def test_block23j_confidence_decision_trace_generation():
    record = ConfidenceAuditLogger.create_trace(
        symbol="RELIANCE.NS",
        raw_state="FALLBACK",
        valid=True,
        directive="USE_FALLBACK_WITH_WARNING",
        base_conf=0.85,
        penalty=0.15,
        adj_conf=0.70,
        composite_score=82.4,
        action="BUY"
    )

    assert isinstance(record, ConfidenceDecisionTraceRecord)
    assert record.symbol == "RELIANCE.NS"
    assert record.raw_data_state == "FALLBACK"
    assert record.base_confidence == 0.85
    assert record.confidence_penalty == 0.15
    assert record.adjusted_confidence == 0.70
    assert record.final_investment_action == "BUY"
    assert record.details["engine_version"] == "EROS-3.0-BLOCK-23J"
