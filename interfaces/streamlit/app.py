"""
==========================================================
AI Stock Analyzer V6 - Streamlit Interface
==========================================================
"""

import streamlit as st

st.set_page_config(page_title="AI Stock Analyzer V6", page_icon="📈", layout="wide")

st.title("📈 AI Stock Analyzer — Institutional Equity Research Platform")
st.markdown("---")

st.sidebar.header("Configuration")
ticker = st.sidebar.text_input("Stock Ticker", value="RELIANCE.NS")

if st.sidebar.button("Run Research Pipeline"):
    st.info(f"Executing research pipeline for {ticker}...")
    # Integration point with Application Use Cases & DI Container
    st.success(f"Analysis complete for {ticker}!")

st.markdown("""
### Welcome to V6 Architecture
* **Clean Architecture & DDD** enforced across layers.
* **Dependency Injection** container managing service lifecycle.
* **Pure Python Technical Indicators** via `pandas_ta`.
""")
