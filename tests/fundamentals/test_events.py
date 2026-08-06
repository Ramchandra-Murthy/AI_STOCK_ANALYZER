from __future__ import annotations

import pytest
from services.fundamentals.events import FundamentalsDownloaded


def test_fundamentals_downloaded_event_contract() -> None:
    event = FundamentalsDownloaded(symbol="RELIANCE.NS", provider="YahooFinance")
    assert event.name == "fundamentals.downloaded"
    assert event.symbol == "RELIANCE.NS"
    assert event.provider == "YahooFinance"
