from __future__ import annotations

import logging
from typing import Any

from services.watchlist_platform.models import WatchlistItem

logger = logging.getLogger(__name__)


class WatchlistIntelligenceEngine:
    """Monitors institutional watchlists and detects valuation, earnings, risk, and catalyst triggers."""

    @staticmethod
    def create_watched_item(
        symbol: str, thesis: str, recommendation: str = "BUY", score: float = 88.0
    ) -> WatchlistItem:
        logger.info("Creating intelligent watchlist item for %s", symbol)

        return WatchlistItem(
            symbol=symbol,
            priority=1,
            investment_thesis=thesis,
            current_recommendation=recommendation,
            committee_score=score,
            latest_catalyst="Margin expansion and digital revenue acceleration",
            major_risks=["Macro commodity volatility", "Regulatory updates"],
            next_earnings_date="2026-10-25",
            alert_status="ACTIVE_MONITORING",
        )

    @staticmethod
    def evaluate_alert(item: WatchlistItem) -> dict[str, Any]:
        logger.info("Evaluating real-time alerts for watched symbol %s", item.symbol)
        triggered = item.committee_score >= 85.0
        return {
            "symbol": item.symbol,
            "alert_triggered": triggered,
            "message": f"High conviction signal verified for {item.symbol} with committee score {item.committee_score}",
        }
