from services.market_data.adapter import InstitutionalMarketDataAdapter, MarketDataPacket
from services.market_data.pipeline import RealMarketPipeline


def test_block23a_market_data_adapter():
    packet = InstitutionalMarketDataAdapter.fetch_market_data("RELIANCE.NS")
    assert isinstance(packet, MarketDataPacket)
    assert packet.symbol == "RELIANCE.NS"
    assert packet.current_price > 0.0
    assert len(packet.ohlcv_history) > 0
    assert packet.is_stale is False


def test_block23b_real_stock_pipeline_evaluation():
    pipeline = RealMarketPipeline(policy_profile="Institutional")
    symbols = ["RELIANCE.NS", "INFY.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS"]

    for sym in symbols:
        packet, result = pipeline.evaluate_real_stock(sym)
        assert packet.symbol == sym
        assert result.symbol == sym
        assert result.final_action in ["BUY", "STRONG BUY", "HOLD", "REDUCE", "SELL"]
        assert 0.0 <= result.adjusted_confidence <= 1.0
        assert result.details["engine_version"] == "EROS-3.0-BLOCK-18"
