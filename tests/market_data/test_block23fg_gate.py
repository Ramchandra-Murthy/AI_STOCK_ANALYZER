from services.market_data.integrity import MarketDataValidationReport
from services.market_data.decision_gate import MarketDataDecisionGate, MarketDataDecisionResult
from services.market_data.pipeline_integration import FullyIntegratedMarketPipeline

def test_block23f_decision_gate_live():
    report = MarketDataValidationReport(
        symbol="RELIANCE.NS",
        data_state="LIVE",
        is_valid=True,
        errors=[],
        freshness_age_seconds=10.0
    )
    res = MarketDataDecisionGate.evaluate_decision(report)
    assert res.directive == "USE_LIVE"
    assert res.allowed_in_scoring is True
    assert res.confidence_penalty == 0.0

def test_block23f_decision_gate_fallback():
    report = MarketDataValidationReport(
        symbol="INFY.NS",
        data_state="FALLBACK",
        is_valid=True,
        errors=[],
        freshness_age_seconds=100.0
    )
    res = MarketDataDecisionGate.evaluate_decision(report)
    assert res.directive == "USE_FALLBACK_WITH_WARNING"
    assert res.allowed_in_scoring is True
    assert res.confidence_penalty > 0.0
    assert res.warning_message is not None

def test_block23f_decision_gate_invalid():
    report = MarketDataValidationReport(
        symbol="BAD.NS",
        data_state="INVALID",
        is_valid=False,
        errors=["Negative price"],
        freshness_age_seconds=0.0
    )
    res = MarketDataDecisionGate.evaluate_decision(report)
    assert res.directive == "REJECT_DATA"
    assert res.allowed_in_scoring is False
    assert res.confidence_penalty == 1.0

def test_block23g_fully_integrated_pipeline():
    pipeline = FullyIntegratedMarketPipeline(policy_profile="Institutional")
    packet, decision, result, trace = pipeline.evaluate_stock_securely("TCS.NS")
    
    assert packet.symbol == "TCS.NS"
    assert decision.symbol == "TCS.NS"
    assert trace is not None
    if decision.allowed_in_scoring:
        assert result is not None
        assert result.symbol == "TCS.NS"
        assert result.final_action in ["BUY", "STRONG BUY", "HOLD", "REDUCE", "SELL"]
