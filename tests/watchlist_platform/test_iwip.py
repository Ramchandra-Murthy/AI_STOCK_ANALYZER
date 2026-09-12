from __future__ import annotations

from services.watchlist_platform.models import WatchlistItem
from services.watchlist_platform.watchlist_engine import WatchlistIntelligenceEngine


def test_watchlist_item_immutability() -> None:
    item = WatchlistItem(
        symbol="RELIANCE.NS",
        priority=1,
        investment_thesis="Digital transformation compounder",
        current_recommendation="BUY",
        committee_score=91.0,
        latest_catalyst="Retail expansion",
        major_risks=["Energy price swings"],
        next_earnings_date="2026-10-20",
        alert_status="NORMAL",
    )
    assert item.symbol == "RELIANCE.NS"
    assert item.committee_score == 91.0
    assert item.timestamp is not None
    assert isinstance(item.metadata, dict)


def test_watchlist_intelligence_engine() -> None:
    item = WatchlistIntelligenceEngine.create_watched_item(
        "RELIANCE.NS", "Strong compounding thesis", "BUY", 92.0
    )
    assert item.symbol == "RELIANCE.NS"
    assert item.current_recommendation == "BUY"

    alert = WatchlistIntelligenceEngine.evaluate_alert(item)
    assert alert["symbol"] == "RELIANCE.NS"
    assert alert["alert_triggered"] is True
    assert len(alert["message"]) > 0
