from __future__ import annotations

from backend.events.bus.event_bus import EnterpriseEventBus
from backend.market_data.analytics.streaming_analytics import StreamingAnalyticsEngine
from backend.market_data.failover.failover_manager import ProviderFailoverManager


def test_enterprise_event_bus_pub_sub() -> None:
    EnterpriseEventBus.clear()
    received_messages = []

    def mock_subscriber(payload: dict) -> None:
        received_messages.append(payload)

    EnterpriseEventBus.subscribe("market.quote", mock_subscriber)
    count = EnterpriseEventBus.publish("market.quote", {"symbol": "TCS.NS", "price": 3525.40})

    assert count == 1
    assert len(received_messages) == 1
    assert received_messages[0]["symbol"] == "TCS.NS"
    EnterpriseEventBus.clear()


def test_provider_failover_success_on_primary() -> None:
    manager = ProviderFailoverManager(["yahoo", "alphavantage"])
    quote = manager.get_quote_with_failover("RELIANCE.NS")
    assert quote["symbol"] == "RELIANCE.NS"
    assert quote["provider"] == "yahoo"


def test_provider_failover_triggers_secondary_on_failure() -> None:
    # 'nonexistent' fails, should fall back to 'alphavantage'
    manager = ProviderFailoverManager(["nonexistent", "alphavantage"])
    quote = manager.get_quote_with_failover("INFY.NS")
    assert quote["ticker"] == "INFY.NS"
    assert quote["provider"] == "alphavantage"


def test_streaming_analytics_engine() -> None:
    history = [3500.0, 3510.0, 3520.0]
    metrics = StreamingAnalyticsEngine.calculate_tick_metrics(history, 3525.40)
    assert metrics["current_price"] == 3525.40
    assert metrics["sma"] == 3513.85
    assert metrics["tick_count"] == 4
