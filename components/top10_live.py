"""Live Top-10 market scanner UI with one-minute automatic refresh."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from components.integrated_workflow import show_live_integrated_scanner
from scanner.top10_integrated import scan_top10_integrated

TOP10_REFRESH_SECONDS = 60


@st.fragment(run_every=f"{TOP10_REFRESH_SECONDS}s")
def show_live_top10_scanner(*, period: str = "6mo", interval: str = "1d") -> None:
    """Render the Top-10 scanner and refresh its market snapshot every minute."""
    st.subheader("🔄 Live Top-10 Market Scanner")
    st.caption(
        f"Automatic refresh: every {TOP10_REFRESH_SECONDS} seconds · "
        f"Last refresh: {datetime.now().strftime('%H:%M:%S')}"
    )

    if st.button("Refresh Top-10 now", key="top10_manual_refresh"):
        st.rerun(scope="fragment")

    with st.spinner("Refreshing Top-10 market movers..."):
        top10 = scan_top10_integrated(period=period, interval=interval)

    if top10.empty:
        st.warning("No Top-10 market movers were returned.")
        return

    show_live_integrated_scanner(top10)
