from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from services.market_data.packet import MarketDataPacket
from services.market_data.provider import YahooFinanceDataProvider


class FakeTicker:
    def history(self, **kwargs):
        now = datetime.now(timezone.utc)
        return pd.DataFrame(
            {
                "Open": [3490.0, 3500.0],
                "High": [3510.0, 3525.0],
                "Low": [3480.0, 3495.0],
                "Close": [3505.0, 3520.0],
                "Volume": [10000, 12000],
            },
            index=pd.DatetimeIndex(
                [now.replace(second=0, microsecond=0), now]
            ),
        )

    @property
    def fast_info(self):
        return {
            "last_price": 3520.0,
            "previous_close": 3505.0,
        }


def fake_ticker_factory(symbol: str):
    assert symbol == "TCS.NS"
    return FakeTicker()


def failing_ticker_factory(symbol: str):
    raise RuntimeError("provider unavailable")


def test_block23c_provider_uses_real_provider_contract():
    packet = YahooFinanceDataProvider.fetch_live_market_data(
        "TCS.NS",
        ticker_factory=fake_ticker_factory,
    )
    assert isinstance(packet, MarketDataPacket)
    assert packet.symbol == "TCS.NS"
    assert packet.current_price == 3520.0
    assert packet.previous_close == 3505.0
    assert len(packet.ohlcv_history) == 2
    assert packet.details["source"] == "yfinance-live-api"
    assert packet.is_stale is False


def test_block23c_provider_never_invents_fallback_price():
    packet = YahooFinanceDataProvider.fetch_live_market_data(
        "INVALID_TICKER_XYZ.NS",
        ticker_factory=failing_ticker_factory,
    )
    assert isinstance(packet, MarketDataPacket)
    assert packet.symbol == "INVALID_TICKER_XYZ.NS"
    assert packet.current_price == 0.0
    assert packet.previous_close == 0.0
    assert packet.ohlcv_history == []
    assert packet.is_stale is True
    assert packet.details["source"] == "market-data-unavailable"
