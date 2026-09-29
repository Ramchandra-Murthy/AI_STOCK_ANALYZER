"""AI Stock Analyzer V6 - Streamlit interface."""

import pandas as pd
import streamlit as st
import yfinance as yf

from components.integrated_workflow import (
    show_integrated_workflow,
    show_live_integrated_scanner,
)
from engine.live_integrated_scanner import DEFAULT_TICKERS, scan_integrated_tickers
from engine.trading_pipeline import integrated_trade_frame

st.set_page_config(page_title="AI Stock Analyzer V6", page_icon="📈", layout="wide")

st.title("📈 AI Stock Analyzer — Institutional Equity Research Platform")
st.markdown("---")

if st.sidebar.button("Run Integrated Scanner"):
    tickers = [symbol.strip() for symbol in scanner_tickers.split(",") if symbol.strip()]
    with st.spinner("Refreshing integrated scanner data..."):
        scanner = scan_integrated_tickers(tickers, period=period, interval=interval)
    show_live_integrated_scanner(scanner)


st.sidebar.header("Configuration")
ticker = st.sidebar.text_input("Stock Ticker", value="RELIANCE.NS")
period = st.sidebar.selectbox("History", ["3mo", "6mo", "1y", "2y"], index=1)
interval = st.sidebar.selectbox("Interval", ["1d"], index=0)
scanner_tickers = st.sidebar.text_area(
    "Scanner Tickers",
    value=", ".join(DEFAULT_TICKERS),
    help="Comma-separated NSE/BSE Yahoo Finance tickers.",
)

if st.sidebar.button("Run Research Pipeline"):
    with st.spinner(f"Loading {ticker} market data..."):
        prices = yf.download(
            ticker,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
        )

    if prices.empty:
        st.error(f"No market data returned for {ticker}.")
    else:
        if isinstance(prices.columns, pd.MultiIndex):
            prices.columns = prices.columns.get_level_values(0)

        try:
            workflow = integrated_trade_frame(prices)
        except (KeyError, ValueError) as exc:
            st.error(str(exc))
        else:
            show_integrated_workflow(workflow)
            st.success(f"Analysis complete for {ticker}.")

st.markdown("""
### Chapter 4-10 Integrated Workflow

The dashboard now exposes the shared analytics pipeline:

**Price → Regime → Edge → Risk-ready workflow output**

The panel is analytics-only and does not place trades.
""")
