from datetime import date, datetime, timedelta

from services.market_calendar import (
    is_equity_calendar_year_supported,
    is_equity_market_holiday,
)


def describe_daily_history(history, today=None, stale_after_days=4):
    """Describe provenance and freshness of daily historical candles.

    RECENT means recent historical data, not a verified live quote. Freshness
    is measured in exchange weekdays only when every relevant calendar year is
    configured. Unsupported calendar ranges fail closed as UNKNOWN.
    """
    if today is None:
        today = date.today()
    elif isinstance(today, datetime):
        today = today.date()

    source = "Unknown"
    timestamp_value = None
    if history is not None:
        attrs = getattr(history, "attrs", {}) or {}
        source = attrs.get("data_source") or "Unknown"
        timestamp_value = attrs.get("last_bar_timestamp")
        if timestamp_value is None and not getattr(history, "empty", True):
            try:
                timestamp_value = history.index[-1]
            except (IndexError, TypeError, AttributeError):
                timestamp_value = None

    parsed_date = None
    if timestamp_value is not None:
        try:
            if isinstance(timestamp_value, datetime):
                parsed_date = timestamp_value.date()
            elif isinstance(timestamp_value, date):
                parsed_date = timestamp_value
            else:
                parsed_date = datetime.fromisoformat(
                    str(timestamp_value).replace("Z", "+00:00")
                ).date()
        except (TypeError, ValueError, OverflowError, AttributeError):
            parsed_date = None

    status = "UNKNOWN"
    timestamp = "Unknown"

    if parsed_date is not None and parsed_date <= today:
        timestamp = parsed_date.isoformat()
        years = range(parsed_date.year, today.year + 1)

        if all(is_equity_calendar_year_supported(year) for year in years):
            # A daily equity candle on a weekend or full-day holiday is not
            # accepted as a valid trading-session timestamp.
            if parsed_date.weekday() < 5 and not is_equity_market_holiday(
                parsed_date
            ):
                trading_days = 0
                current = parsed_date + timedelta(days=1)
                while current <= today:
                    if (
                        current.weekday() < 5
                        and not is_equity_market_holiday(current)
                    ):
                        trading_days += 1
                    current += timedelta(days=1)

                status = (
                    "STALE"
                    if trading_days > stale_after_days
                    else "RECENT"
                )

    return {
        "status": status,
        "source": source,
        "timestamp": timestamp,
        "is_verified_live": False,
    }
