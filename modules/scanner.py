"""Streamlit UI for broad-market and personal-watchlist AI scanning."""

import streamlit as st

from scanner.market_scanner import BSE_CANDIDATES, DISPLAY_COUNT, NSE_CANDIDATES, market_scan
from scanner.watchlist_scanner import scan_watchlist


def show():
    st.title("📡 AI Market Scanner")
    st.caption("Professional Scanner")

    settings = st.session_state.get("app_settings", {})
    exchange_preference = settings.get("exchange", "NSE + BSE")
    settings_min_price = float(settings.get("min_price", 0.0) or 0.0)
    min_volume = int(settings.get("min_volume", 0) or 0)
    selected_exchange = exchange_preference if exchange_preference in ("NSE", "BSE") else "NSE + BSE"

    st.caption(
        f"Broad candidate pool: {len(NSE_CANDIDATES)} NSE + {len(BSE_CANDIDATES)} BSE symbols. "
        f"Exchange preference: {selected_exchange}."
    )
    if min_volume > 0:
        st.warning("Minimum volume is saved in Settings but is not applied: current analysis output does not expose traded volume.")

    with st.expander("Scanner filters", expanded=True):
        price_col1, price_col2 = st.columns(2)
        with price_col1:
            min_price = st.number_input(
                "Minimum price (₹)", min_value=0.0, value=settings_min_price,
                step=10.0, key="scanner_filter_min_price",
            )
        with price_col2:
            max_price = st.number_input(
                "Maximum price (₹; 0 = no limit)", min_value=0.0, value=0.0,
                step=10.0, key="scanner_filter_max_price",
            )
        rsi_col1, rsi_col2 = st.columns(2)
        with rsi_col1:
            min_rsi = st.number_input("Minimum RSI", min_value=0.0, max_value=100.0, value=0.0, step=1.0)
        with rsi_col2:
            max_rsi = st.number_input("Maximum RSI", min_value=0.0, max_value=100.0, value=100.0, step=1.0)
        min_ai_score = st.number_input("Minimum AI score", min_value=-100.0, max_value=100.0, value=-100.0, step=1.0)
        trend_filter = st.selectbox("Trend", ["All", "Bullish", "Bearish", "Sideways"])

    watchlist = st.session_state.get("personal_watchlist", [])
    if not watchlist:
        st.info("Your Personal Watchlist is empty. Add stocks in the Indian Market Dashboard, then return here.")

    scan_mode = st.radio("Scan", ["Personal Watchlist", "Broad Market"], horizontal=True)
    if st.button("Scan", use_container_width=True):
        with st.spinner("Scanning stocks..."):
            df = scan_watchlist(watchlist) if scan_mode == "Personal Watchlist" else market_scan()

        if df.empty:
            st.warning("No stocks could be analyzed for this scan.")
            return

        if selected_exchange in ("NSE", "BSE") and "Exchange" in df.columns:
            df = df.loc[df["Exchange"] == selected_exchange]
        if "Price" in df.columns:
            df = df.loc[df["Price"] >= max(min_price, settings_min_price)]
            if max_price > 0:
                df = df.loc[df["Price"] <= max_price]
        if "RSI" in df.columns:
            df = df.loc[df["RSI"].between(min_rsi, max_rsi)]
        if "AI Score" in df.columns:
            df = df.loc[df["AI Score"] >= min_ai_score]
        if trend_filter != "All" and "Trend" in df.columns:
            df = df.loc[df["Trend"].astype(str).str.casefold() == trend_filter.casefold()]

        if df.empty:
            st.warning("No results match these filters. Widen the price, RSI, score, trend, or exchange settings and scan again.")
            return

        st.success(f"{len(df)} matching stocks displayed")
        st.dataframe(df.head(DISPLAY_COUNT) if scan_mode == "Broad Market" else df, use_container_width=True, height=600)
        st.download_button("⬇ Download CSV", df.to_csv(index=False), "market_scan.csv", "text/csv")
