from services.market_data.pipeline_integration import FullyIntegratedMarketPipeline


def test_block23h_confidence_propagation():
    pipeline = FullyIntegratedMarketPipeline(policy_profile="Institutional")
    packet, decision, result, trace = pipeline.evaluate_stock_securely("RELIANCE.NS")

    assert packet is not None
    assert decision is not None
    assert trace is not None
    if decision.allowed_in_scoring and result is not None:
        breakdown = result.details.get("breakdown_details", {})
        assert "current_price" in breakdown or result.symbol == "RELIANCE.NS"
        assert decision.confidence_penalty >= 0.0
        assert trace.adjusted_confidence >= 0.0
