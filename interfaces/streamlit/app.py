from __future__ import annotations

import streamlit as st

from core.container import ServiceKey, bootstrap_container, container


st.set_page_config(
    page_title="AI Stock Analyzer V6",
    page_icon="📈",
    layout="wide",
)

st.title("📈 AI Stock Analyzer — Institutional Equity Research Platform")
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
            st.warning(
                f"EROS completed with status: {result.get('status', 'UNKNOWN')}"
            )

        st.subheader("Research Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Investment Score", result.get("investment_score", "N/A"))
        col2.metric("Fundamental Score", result.get("fundamental_score", "N/A"))
        col3.metric("Technical Score", result.get("technical_score", "N/A"))

        recommendation = result.get("recommendation", {})
        if recommendation:
            st.subheader("Recommendation")
            st.json(recommendation)

        valuation = result.get("valuation_v43", {})
        if valuation:
            st.subheader("Valuation V4.3")
            st.json(valuation)

        errors = result.get("errors", [])
        if errors:
            st.subheader("Pipeline Warnings")
            for error in errors:
                st.warning(error)

    except Exception as exc:
        st.error(f"EROS pipeline failed: {exc}")

st.markdown(
    """
    ### EROS V6
    The Streamlit interface now calls the same application service as the CLI,
    so the UI no longer reports a successful analysis without executing the
    research pipeline.
    """
)
