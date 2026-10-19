import streamlit as st

from services.market_service import get_market_indices, market_session_status

FRESHNESS_WARNING_STATUSES = {
    "DATA UNAVAILABLE",
    "DATA TIMESTAMP UNAVAILABLE",
    "FUTURE-DATED MARKET DATA",
    "STALE INTRADAY DATA",
    "DAILY DATA ONLY · INTRADAY UNAVAILABLE",
    "MARKET CALENDAR UNAVAILABLE",
}


@st.cache_data(ttl=30, show_spinner=False)
def _get_cached_market_indices():
    """Refresh market observations at most once every 30 seconds."""
    return get_market_indices()


def _format_change(name, change, change_points):
    """Show point and percentage moves for equity indices when available."""
    if name in {"NIFTY 50", "SENSEX", "BANK NIFTY"}:
        if isinstance(change_points, (int, float)) and isinstance(change, (int, float)):
            return f"{change_points:+,.2f} pts · {change:+.2f}%"
        if isinstance(change_points, (int, float)):
            return f"{change_points:+,.2f} pts"
    if isinstance(change, (int, float)):
        return f"{change:+.2f}%"
    return None


def _market_status_banner(statuses):
    """Choose a dashboard banner from every index status, not just the newest timestamp."""
    warnings = [
        (name, status)
        for name, status in statuses
        if status["status"] in FRESHNESS_WARNING_STATUSES
    ]
    if warnings:
        details = "; ".join(f"{name}: {status['status']}" for name, status in warnings)
        return "warning", f"⚠️ MARKET DATA FRESHNESS WARNING — {details}"

    if statuses and all(status["status"].startswith("INTRADAY DATA") for _, status in statuses):
        return (
            "success",
            "🟢 INTRADAY DATA AVAILABLE — each index's timestamp and status are shown below; "
            "Yahoo Finance is not exchange-tick live.",
        )

    details = "; ".join(f"{name}: {status['status']}" for name, status in statuses)
    return "info", f"ℹ️ MARKET SESSION / DATA STATUS — {details}"


def _show_market_status(items):
    """Show freshness based on all index observations, including stale or daily-only fallbacks."""
    if not any(info.get("observed_at") for _name, info in items):
        st.warning("⚠️ MARKET DATA UNAVAILABLE — no observation timestamps were returned.")
        return

    statuses = [
        (
            name,
            market_session_status(info.get("observed_at"), info.get("frequency", "unknown")),
        )
        for name, info in items
    ]
    level, message = _market_status_banner(statuses)
    getattr(st, level)(message)

    st.caption(
        "Source: Yahoo Finance • Data is latest available, not exchange-tick live. "
        "Dashboard cache refreshes every 30 seconds."
    )


def show_market_overview():
    """
    Display major market indices with explicit per-index data freshness.

    The canonical market service supplies latest available Yahoo Finance
    observations, not exchange-tick live prices.
    """
    st.subheader("🌍 Market Overview")

    data = _get_cached_market_indices()

    if not data:
        st.warning("Market data is currently unavailable.")
        return

    items = list(data.items())
    _show_market_status(items)

    # Show three readable index cards per row.
    for start in range(0, len(items), 3):
        row_items = items[start : start + 3]
        cols = st.columns(3)

        for col, (name, info) in zip(cols, row_items, strict=False):
            value = info.get("value")
            change = info.get("change")
            change_points = info.get("change_points")
            observed_at = info.get("observed_at")
            frequency = info.get("frequency", "unknown")
            is_tick_live = bool(info.get("is_tick_live", False))

            if value is None:
                col.metric(label=name, value="N/A")
            else:
                col.metric(
                    label=name,
                    value=value,
                    delta=_format_change(name, change, change_points),
                )

            if observed_at:
                freshness_label = "Tick live" if is_tick_live else f"Latest {frequency}"
                col.caption(f"{freshness_label} • {observed_at}")
                status = market_session_status(observed_at, frequency)
                col.caption(f"Data status: {status['status']}")
            else:
                col.caption("Observation time unavailable")
                col.caption("Data status: DATA UNAVAILABLE")
