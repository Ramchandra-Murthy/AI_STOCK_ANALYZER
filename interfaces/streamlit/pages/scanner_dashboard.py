"""Operational Streamlit dashboard for the shared NSE/BSE scanner services."""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from components.top10_live import show_live_top10_scanner
from engine.live_integrated_scanner import DEFAULT_TICKERS, scan_integrated_tickers
from services.market_calendar import equity_market_session_status
from services.resilient_market_data import (
    MAX_PROVIDER_REQUESTS_IN_FLIGHT,
    market_data_cache_stats,
)

IST = ZoneInfo("Asia/Kolkata")

st.set_page_config(
    page_title="Scanner Operations | AI Stock Analyzer",
    page_icon="📈",
    layout="wide",
)

now_ist = datetime.now(IST)
market_status = equity_market_session_status(now_ist)
cache_stats = market_data_cache_stats()

st.title("NSE/BSE Scanner Operations")
st.caption(
    "Operational view of the shared market-data pipeline. Yahoo Finance data is "
    "for research and paper trading, not exchange-tick execution."
)

status_col, time_col, cache_col, provider_col = st.columns(4)
with status_col:
    status_label = {
        "OPEN": "OPEN",
        "HOLIDAY": "HOLIDAY",
        "CLOSED": "CLOSED",
        "CALENDAR_UNAVAILABLE": "CALENDAR UNAVAILABLE",
    }.get(market_status, market_status)
    st.metric("Equity session", status_label)
with time_col:
    st.metric("India time", now_ist.strftime("%d %b %Y · %H:%M:%S"))
with cache_col:
    st.metric("Cached market frames", f"{cache_stats['entries']:,}")
    st.caption(f"Bounded capacity: {cache_stats['max_entries']:,}")
with provider_col:
    st.metric("Provider concurrency cap", MAX_PROVIDER_REQUESTS_IN_FLIGHT)
    st.caption("Shared across market-data service calls")

if market_status == "OPEN":
    st.success("The configured calendar confirms the regular NSE/BSE equity session is open.")
elif market_status == "HOLIDAY":
    st.warning("Exchange holiday: regular live scanning is gated.")
elif market_status == "CALENDAR_UNAVAILABLE":
    st.error(
        "The holiday calendar for this year is not configured. Live scanning must remain "
        "closed until an exchange-verified calendar is added."
    )
else:
    st.info(
        "Regular equity session is closed. The live Top-10 component will not fetch live quotes."
    )

st.divider()
st.subheader("Live Top-10 scanner")
st.write(
    "This uses the existing bounded Top-10 scanner, including its own session gating, "
    "refresh cadence, stale-data handling and partial-coverage safeguards."
)
show_live_top10_scanner()

st.divider()
st.subheader("Integrated research scan")
st.caption(
    "Runs the existing integrated daily-data pipeline on the configured default universe. "
    "This is a research scan and may run outside market hours using the shared cache/provider controls."
)

universe_label = st.selectbox(
    "Universe",
    ["Default NSE research universe", "Custom ticker list"],
)
if universe_label == "Custom ticker list":
    ticker_text = st.text_area(
        "Yahoo Finance symbols",
        value=", ".join(DEFAULT_TICKERS),
        help="Use exchange suffixes such as RELIANCE.NS or a BSE .BO symbol.",
    )
    tickers = [item.strip().upper() for item in ticker_text.split(",") if item.strip()]
else:
    tickers = list(DEFAULT_TICKERS)

if st.button("Run integrated research scan", type="primary", disabled=not tickers):
    with st.spinner(f"Running integrated analytics for {len(tickers)} symbols..."):
        results = scan_integrated_tickers(tickers, period="6mo", interval="1d")
    st.session_state["scanner_dashboard_results"] = results
    st.session_state["scanner_dashboard_scanned_at"] = datetime.now(IST).isoformat()

results = st.session_state.get("scanner_dashboard_results")
scanned_at = st.session_state.get("scanner_dashboard_scanned_at")
if isinstance(results, pd.DataFrame):
    if scanned_at:
        st.caption(f"Last completed research scan: {scanned_at}")
    if results.empty:
        st.warning(
            "No symbols produced a valid integrated result. Check provider availability and symbol coverage."
        )
    else:
        st.success(f"Integrated results available for {len(results)} symbols.")
        st.dataframe(results, use_container_width=True, hide_index=True)
        st.download_button(
            "Download research results (CSV)",
            data=results.to_csv(index=False).encode("utf-8"),
            file_name=f"integrated_scan_{now_ist:%Y%m%d_%H%M%S}.csv",
            mime="text/csv",
        )

st.divider()
st.subheader("Backend capability status")
capability_rows = [
    {
        "Capability": "IST market calendar and fail-closed gating",
        "Status": "Connected",
        "Implementation": "services.market_calendar",
    },
    {
        "Capability": "Shared interval-aware cache and bounded provider concurrency",
        "Status": "Connected",
        "Implementation": "services.resilient_market_data",
    },
    {
        "Capability": "Top-10 refresh, stale-data and coverage safeguards",
        "Status": "Connected",
        "Implementation": "components.top10_live",
    },
    {
        "Capability": "Dedicated HTTP 429 circuit-breaker telemetry",
        "Status": "Not yet integrated",
        "Implementation": "Do not infer breaker state from provider errors",
    },
    {
        "Capability": "Asynchronous Supabase scan-result batch writer",
        "Status": "Not yet integrated",
        "Implementation": "No synchronous database writes in this dashboard",
    },
]
st.dataframe(pd.DataFrame(capability_rows), use_container_width=True, hide_index=True)
