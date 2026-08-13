from services.market_data.provider import YahooFinanceDataProvider
from services.market_data.adapter import MarketDataPacket

def test_block23c_yahoo_provider_execution():
    symbols = ["RELIANCE.NS", "INFY.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
    for sym in symbols:
        packet = YahooFinanceDataProvider.fetch_live_market_data(sym)
        assert isinstance(packet, MarketDataPacket)
        assert packet.symbol == sym
        assert packet.current_price > 0.0
        assert len(packet.ohlcv_history) > 0
        assert "source" in packet.details

def test_block23c_provider_fallback_handling():
    # Test invalid ticker triggers fallback safely without raising exception
    packet = YahooFinanceDataProvider.fetch_live_market_data("INVALID_TICKER_XYZ.NS")
    assert isinstance(packet, MarketDataPacket)
    assert packet.symbol == "INVALID_TICKER_XYZ.NS"
    assert packet.current_price > 0.0
    assert packet.is_stale is True
    assert "fallback" in packet.details["source"]
