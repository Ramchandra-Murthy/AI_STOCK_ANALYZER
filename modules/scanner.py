"""Streamlit UI for broad-market and personal-watchlist AI scanning."""

import streamlit as st

from scanner.market_scanner import BSE_CANDIDATES, DISPLAY_COUNT, NSE_CANDIDATES, market_scan
from scanner.watchlist_scanner import scan_watchlist


def show():
    st.title("📡 AI Market Scanner")
    st.caption("Professional Scanner")

    settings = st.session_state.get("app_settings", {})
    exchange_preference = settings.get("exchange", "NSE + BSE")
    min_price = float(settings.get("min_price", 0.0) or 0.0)
    min_volume = int(settings.get("min_volume", 0) or 0)
    selected_exchange = exchange_preference if exchange_preference in ("NSE", "BSE") else "NSE + BSE"

    st.caption(
        f"Broad candidate pool: {len(NSE_CANDIDATES)} NSE + {len(BSE_CANDIDATES)} BSE symbols. "
        f"Exchange preference: {selected_exchange}."
    )
    if min_price > 0:
        st.caption(f"Minimum price filter: ₹{min_price:,.2f}")
    if min_volume > 0:
        st.warning("Minimum volume is saved in Settings but is not applied: the analysis output does not currently expose traded volume.")

    watchlist = st.session_state.get("personal_watchlist", [])
    if not watchlist:
        st.info("Your Personal Watchlist is empty. Add stocks in the Indian Market Dashboard, then return here.")

    scan_mode = st.radio("Scan", ["Personal Watchlist", "Broad Market"], horizontal=True)
    if st.button("Scan", use_container_width=True):
        with st.spinner("Scanning stocks..."):
            if scan_mode == "Personal Watchlist":
                df = scan_watchlist(watchlist)
            else:
                df = market_scan()

        if df.empty:
            st.warning("No stocks could be analyzed for this scan.")
            return
        if selected_exchange in ("NSE", "BSE") and "Exchange" in df.columns:
            df = df.loc[df["Exchange"] == selected_exchange]
        if min_price > 0 and "Price" in df.columns:
            df = df.loc[df["Price"] >= min_price]
        if df.empty:
            st.warning("No results match the selected exchange and minimum-price filters.")
            return

        st.success(f"{len(df)} matching stocks displayed")
        st.dataframe(df.head(DISPLAY_COUNT) if scan_mode == "Broad Market" else df, use_container_width=True, height=600)
        st.download_button("⬇ Download CSV", df.to_csv(index=False), "market_scan.csv", "text/csv")
