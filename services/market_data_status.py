from datetime import date, datetime

def describe_daily_history(history, today=None, stale_after_days=4):
    """Describe the provenance and age of daily historical candles.

    This labels the data as historical, never as a live quote. Daily bars
    older than stale_after_days calendar days are conservatively flagged stale.
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
            if hasattr(timestamp_value, "date"):
                parsed_date = timestamp_value.date()
            else:
                parsed_date = datetime.fromisoformat(
                    str(timestamp_value).replace("Z", "+00:00")
                ).date()
        except (TypeError, ValueError, OverflowError):
            parsed_date = None

    if parsed_date is None or parsed_date > today:
        status = "UNKNOWN"
        timestamp = "Unknown"
    else:
        age = (today - parsed_date).days
        status = "STALE" if age > stale_after_days else "RECENT"
        timestamp = parsed_date.isoformat()

    return {"status": status, "source": source, "timestamp": timestamp}
