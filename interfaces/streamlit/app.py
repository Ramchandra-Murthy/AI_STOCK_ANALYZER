from __future__ import annotations

import streamlit as st

from core.container import ServiceKey, bootstrap_container, container


st.set_page_config(page_title="AI Stock Analyzer — EROS 3.0", page_icon="📈", layout="wide")
st.title("📈 AI Stock Analyzer — EROS 3.0")
st.markdown("---")

st.sidebar.header("Configuration")
ticker = st.sidebar.text_input("Stock Ticker", value="RELIANCE.NS").strip().upper()

if st.sidebar.button("Run Research Pipeline"):
    try:
        bootstrap_container()
        service = container.resolve(ServiceKey.RESEARCH)
        with st.spinner(f"Running EROS research pipeline for {ticker}..."):
            result = service.run_pipeline(ticker)

        if result.get("status") == "OK":
            st.success(f"EROS analysis complete for {result.get('symbol', ticker)}")
        else:
            st.warning(f"EROS completed with status: {result.get('status', 'UNKNOWN')}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Investment Score", result.get("investment_score", "N/A"))
        c2.metric("Fundamental Score", result.get("fundamental_score", "N/A"))
        c3.metric("Technical Score", result.get("technical_score", "N/A"))

        if result.get("recommendation"):
            st.subheader("Recommendation")
            st.json(result["recommendation"])
        if result.get("valuation_v43"):
            st.subheader("Valuation V4.3")
            st.json(result["valuation_v43"])
        if result.get("errors"):
            st.subheader("Pipeline Stage Errors")
            for error in result["errors"]:
                st.warning(error)
    except Exception as exc:
        st.error(f"EROS pipeline failed: {exc}")
