from services.market_data.adapter import MarketDataPacket
from services.market_data.integrity import MarketDataIntegrityGate, MarketDataValidationReport
from services.market_data.provider_resilience import ResilientMarketDataProvider

def test_block23d_integrity_gate_live():
    packet = MarketDataPacket(
        symbol="RELIANCE.NS",
        current_price=2500.0,
        previous_close=2480.0,
        volume=2000000,
        ohlcv_history=[{"date": "2026-06-03", "close": 2500.0, "volume": 2000000}],
        is_stale=False,
        details={"source": "yfinance-live-api"}
    )
    report = MarketDataIntegrityGate.validate_packet(packet)
    assert isinstance(report, MarketDataValidationReport)
    assert report.data_state == "LIVE"
    assert report.is_valid is True
    assert len(report.errors) == 0

def test_block23d_integrity_gate_invalid():
    packet = MarketDataPacket(
        symbol="BAD.NS",
        current_price=-10.0,
        previous_close=100.0,
        volume=-500,
        ohlcv_history=[],
        is_stale=False,
        details={"source": "test"}
    )
    report = MarketDataIntegrityGate.validate_packet(packet)
    assert report.data_state == "INVALID"
    assert report.is_valid is False
    assert len(report.errors) >= 2

def test_block23e_resilient_provider_workflow():
    packet, report = ResilientMarketDataProvider.get_validated_market_data("TCS.NS")
    assert packet.symbol == "TCS.NS"
    assert report.symbol == "TCS.NS"
    assert report.data_state in ["LIVE", "FALLBACK", "STALE"]
    assert report.details["engine_version"] == "EROS-3.0-BLOCK-23D"
