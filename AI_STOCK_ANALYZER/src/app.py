import pandas as pd
import streamlit as st

from src.database import DatabaseManager
from src.risk_manager import RiskManager
from src.scanner import batch_scan_stocks

st.set_page_config(page_title="AI Stock Analyzer", layout="wide")

st.title("?? AI Stock Analyzer Dashboard")
st.markdown(
    "Institutional-grade screening for Volatility Contraction Patterns (VCP), CPR Compression, and Automated Risk Management."
)

# Sidebar Controls
st.sidebar.header("Scan Parameters")
default_watchlist = (
    "RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS, ITC.NS, TMPV.NS, SBIN.NS, BHARTIARTL.NS"
)
watchlist_input = st.sidebar.text_area(
    "Watchlist Tickers (comma separated)", value=default_watchlist
)
capital = st.sidebar.number_input("Trading Capital (?)", value=500000.0, step=50000.0)
risk_pct = st.sidebar.slider(
    "Max Risk Per Trade (%)", min_value=0.5, max_value=3.0, value=1.0, step=0.25
)

tickers = [t.strip().upper() for t in watchlist_input.split(",") if t.strip()]

if st.sidebar.button("Run Market Scan", type="primary"):
    with st.spinner("Downloading historical data and scanning setups..."):
        signals_df = batch_scan_stocks(tickers)

        if not signals_df.empty:
            db = DatabaseManager()
            db.save_signals(signals_df)
            st.session_state["signals"] = signals_df
            st.success(f"Scan complete! Found {len(signals_df)} matching setups.")
        else:
            st.warning("No stocks matched the criteria today.")
            st.session_state["signals"] = pd.DataFrame()

# Display Results
if "signals" in st.session_state and not st.session_state["signals"].empty:
    st.subheader("?? Detected Technical Setups")
    st.dataframe(st.session_state["signals"], use_container_width=True)

    st.markdown("---")
    st.subheader("??? Automated Position Sizing & Risk Calculator")

    selected_ticker = st.selectbox(
        "Select Ticker for Risk Plan", st.session_state["signals"]["Ticker"].tolist()
    )
    selected_row = st.session_state["signals"][
        st.session_state["signals"]["Ticker"] == selected_ticker
    ].iloc[0]

    rm = RiskManager(capital=capital, max_risk_pct=risk_pct)
    sizing = rm.calculate_position_size(entry_price=selected_row["Close"], atr=selected_row["ATR"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Entry Price", f"?{sizing.get('Entry Price', 0)}")
    col2.metric("Stop Loss (2x ATR)", f"?{sizing.get('Stop Loss', 0)}")
    col3.metric("Shares to Buy", sizing.get("Shares to Buy", 0))
    col4.metric("Capital Committed", f"?{sizing.get('Total Capital Committed', 0)}")
else:
    st.info("Configure your watchlist on the sidebar and click **Run Market Scan** to begin.")
