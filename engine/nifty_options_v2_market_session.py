"""NIFTY V2 market-session safety checks."""

from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

from services.market_calendar import equity_market_session_status

IST = ZoneInfo("Asia/Kolkata")
MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)


def market_session_ready(now: datetime) -> bool:
    """Return whether automatic paper processing is allowed in regular NSE hours."""
    current = now.astimezone(IST)
    return equity_market_session_status(current, MARKET_OPEN, MARKET_CLOSE) == "OPEN"
