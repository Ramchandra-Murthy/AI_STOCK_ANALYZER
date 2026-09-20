import pandas as pd
import streamlit as st

from services.market_service import get_market_indices
from services.market_status import describe_market_status


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

    items = list(data.items())

    observed_times = [info.get("observed_at") for _, info in items if info.get("observed_at")]
    if observed_times:
        latest_observed = max(observed_times, key=lambda value: pd.Timestamp(value))
        status = describe_market_status(latest_observed)
        st.info(f"**{status['label']}**\n\n{status['message']}")
    else:
        st.warning("Market status cannot be determined because observation timestamps are unavailable.")

    # Show three readable index cards per row.
    for start in range(0, len(items), 3):
        row_items = items[start : start + 3]
        cols = st.columns(3)

        for col, (name, info) in zip(cols, row_items, strict=False):
            value = info.get("value")
            change = info.get("change")
            observed_at = info.get("observed_at")
            frequency = info.get("frequency", "unknown")
            is_tick_live = bool(info.get("is_tick_live", False))

            if value is None:
                col.metric(label=name, value="N/A")
            else:
                col.metric(
                    label=name,
                    value=value,
                    delta=_format_change(change),
                )

            if observed_at:
                freshness_label = "Tick live" if is_tick_live else f"Latest {frequency}"
                col.caption(f"{freshness_label} • {observed_at}")
            else:
                col.caption("Observation time unavailable")
