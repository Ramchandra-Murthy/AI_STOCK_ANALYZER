"""Live Top-10 market scanner UI with one-minute automatic refresh."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import streamlit as st

from components.integrated_workflow import show_live_integrated_scanner
from scanner.top10_integrated import scan_top10_integrated

TOP10_REFRESH_SECONDS = 60
TOP10_CACHE_SECONDS = 50
TOP10_TIMEZONE = "Asia/Kolkata"
_IST = ZoneInfo(TOP10_TIMEZONE)


@st.cache_data(ttl=TOP10_CACHE_SECONDS, show_spinner=False)
def _load_top10(period: str, interval: str):
    """Cache one Top-10 snapshot to avoid duplicate network scans."""
    return scan_top10_integrated(period=period, interval=interval)


@st.fragment(run_every=f"{TOP10_REFRESH_SECONDS}s")
def show_live_top10_scanner(*, period: str = "6mo", interval: str = "1d") -> None:
    """Render the Top-10 scanner and refresh its market snapshot every minute."""
    st.subheader("🔄 Live Top-10 Market Scanner")

    if st.button("Refresh Top-10 now", key="top10_manual_refresh"):
        _load_top10.clear()
        st.rerun(scope="fragment")

    with st.spinner("Refreshing Top-10 market movers..."):
        top10 = _load_top10(period, interval)

    completed_at = datetime.now(_IST)
    next_refresh = completed_at + timedelta(seconds=TOP10_REFRESH_SECONDS)
    st.caption(
        f"Automatic refresh: every {TOP10_REFRESH_SECONDS} seconds · "
        f"Last refresh: {completed_at.strftime('%H:%M:%S')} IST · "
        f"Next refresh: {next_refresh.strftime('%H:%M:%S')} IST · "
        "Status: 🟢 LIVE"
    )

    if top10.empty:
        st.warning("No Top-10 market movers were returned.")
        return

    show_live_integrated_scanner(top10)
