from services.market_data.confidence_trace import ConfidenceDecisionTraceRecord
from services.market_data.pipeline_integration import FullyIntegratedMarketPipeline


def test_block23k_fully_integrated_pipeline_execution():
    pipeline = FullyIntegratedMarketPipeline(policy_profile="Institutional")
    packet, decision, result, trace = pipeline.evaluate_stock_securely("RELIANCE.NS")

    assert packet is not None
    assert decision is not None
    assert isinstance(trace, ConfidenceDecisionTraceRecord)
    assert trace.symbol == "RELIANCE.NS"
    assert trace.base_confidence == 0.85
    assert trace.confidence_penalty == decision.confidence_penalty
    if decision.allowed_in_scoring and result is not None:
        assert trace.final_investment_action == result.final_action
        assert (
            trace.composite_ai_score == result.ai_score.composite_score
            if hasattr(result, "ai_score")
            else True
        )
    else:
        assert trace.final_investment_action == "REJECT_DATA"
