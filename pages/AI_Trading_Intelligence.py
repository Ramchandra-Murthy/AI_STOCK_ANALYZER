"""Streamlit page for the separate AI trading intelligence module."""

from __future__ import annotations

import streamlit as st

from ai_trading.ai_scanner import scan_universe
from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES

st.set_page_config(page_title="AI Trading Intelligence", page_icon="🧠", layout="wide")

st.title("🧠 AI Trading Intelligence")
st.caption("AI-oriented market feature and signal research. No broker orders are submitted.")

left, right = st.columns(2)
with left:
    exchange = st.selectbox("Exchange", ["NSE", "BSE"])
    universe = NSE_CANDIDATES if exchange == "NSE" else BSE_CANDIDATES
    count = st.slider("Symbols to scan", 10, min(50, len(universe)), 20, 5)
with right:
    period = st.selectbox("Training / analysis history", ["6mo", "1y", "2y"], index=1)

if st.button("Run AI Trading Scan", type="primary"):
    with st.spinner(f"Analyzing {count} {exchange} symbols..."):
        result = scan_universe(universe[:count], exchange=exchange, period=period)

    if result.empty:
        st.warning("No usable market data was returned.")
        st.stop()

    st.success(f"Analyzed {len(result)} symbols.")
    st.subheader("AI Trading Opportunities")
    st.dataframe(result.head(10), use_container_width=True, hide_index=True)

    st.subheader("Signal distribution")
    st.bar_chart(result["signal"].value_counts())

    st.subheader("AI confidence")
    st.bar_chart(result.set_index("symbol")["confidence_pct"].head(10))

    st.info(
        "The current engine is a deterministic baseline built from market features. "
        "It is not yet a trained machine-learning model; model training and validation "
        "will be added as a separate stage."
    )
