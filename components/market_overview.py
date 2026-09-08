import streamlit as st

from services.market_service import get_market_indices


def _format_change(change):
    """Format a percentage change without assuming it is available."""
    if isinstance(change, (int, float)):
        return f"{change:+.2f}%"
    return None


def show_market_overview():
    """
    Display major market indices with explicit data freshness.

    The canonical market service currently supplies latest available
    daily Yahoo Finance observations, not exchange-tick live prices.
    """
    st.subheader("🌍 Market Overview")

    data = get_market_indices()

    if not data:
        st.warning("Market data is currently unavailable.")
        return

    cols = st.columns(len(data))

    for col, (name, info) in zip(cols, data.items(), strict=False):
        value = info.get("value")
        change = info.get("change")
        observed_at = info.get("observed_at")
        frequency = info.get("frequency", "unknown")
        is_tick_live = bool(info.get("is_tick_live", False))

        if value is None:
            col.metric(label=name, value="N/A")
        else:
            delta = _format_change(change)
            col.metric(label=name, value=value, delta=delta)

        if observed_at:
            freshness_label = "Tick live" if is_tick_live else f"Latest {frequency}"
            col.caption(f"{freshness_label} • {observed_at}")
        else:
            col.caption("Observation time unavailable")
