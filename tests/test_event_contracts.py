from __future__ import annotations

import pytest

from core.events.event import BaseDomainEvent
from services.forecast.events import ForecastCompleted
from services.market_data.events import MarketDataDownloaded
from services.report.events import ReportCompleted
from services.research.events import ResearchCompleted
from services.valuation.events import ValuationCompleted


@pytest.mark.parametrize(
    "event_class, event_name",
    [
        (MarketDataDownloaded, "market.data.downloaded"),
        (ForecastCompleted, "forecast.completed"),
        (ValuationCompleted, "valuation.completed"),
        (ResearchCompleted, "research.completed"),
        (ReportCompleted, "report.completed"),
    ],
)
def test_domain_event_contract(event_class: type[BaseDomainEvent], event_name: str) -> None:
    """Verify that every domain event adheres strictly to the BaseDomainEvent contract."""
    event = event_class(symbol="RELIANCE.NS", payload={"test_key": "test_value"})

    assert isinstance(event.event_id, str)
    assert event.event_id != ""
    assert isinstance(event.timestamp, float)
    assert event.timestamp > 0.0
    assert event.name == event_name
    assert isinstance(event.symbol, str)
    assert event.symbol == "RELIANCE.NS"
    assert isinstance(event.payload, dict)
    assert event.payload["test_key"] == "test_value"


def test_event_runtime_assertions() -> None:
    """Verify that invalid symbols or payloads trigger immediate assertion errors."""
    with pytest.raises(AssertionError):
        MarketDataDownloaded(symbol="", payload={})

    with pytest.raises(AssertionError):
        MarketDataDownloaded(symbol=123, payload={})  # type: ignore[arg-type]

    with pytest.raises(AssertionError):
        MarketDataDownloaded(symbol="RELIANCE.NS", payload="not-a-dict")  # type: ignore[arg-type]
