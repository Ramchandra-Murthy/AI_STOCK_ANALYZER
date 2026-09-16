"""Streamlit UI for the AI market scanner.

Applies supported preferences saved by the Settings module. The scanner engine
currently ranks a fixed broad candidate list and returns its top results; exact
index-universe selection and volume filtering require engine/data changes.
"""

import streamlit as st

from scanner.market_scanner import BSE_CANDIDATES, DISPLAY_COUNT, NSE_CANDIDATES, market_scan


def show():
    st.title("📡 AI Market Scanner")
    st.caption("Professional Scanner")

    settings = st.session_state.get("app_settings", {})
    exchange_preference = settings.get("exchange", "NSE + BSE")
    min_price = float(settings.get("min_price", 0.0) or 0.0)
    min_volume = int(settings.get("min_volume", 0) or 0)
    exchange_names = {
        "NSE": "NSE",
        "BSE": "BSE",
        "NSE + BSE": "NSE + BSE",
    }
    selected_exchange = exchange_names.get(exchange_preference, "NSE + BSE")

    st.caption(
        f"Candidate pool: {len(NSE_CANDIDATES)} NSE + {len(BSE_CANDIDATES)} BSE symbols. "
        f"Selected exchange: {selected_exchange}; top {DISPLAY_COUNT} results are AI-ranked."
    )
    if min_price > 0:
        st.caption(f"Minimum price filter: ₹{min_price:,.2f}")
    if min_volume > 0:
        st.warning(
            "Minimum traded-volume preference is saved, but this scanner's current "
            "analysis output does not expose volume. The volume filter is not applied yet."
        )

    if st.button("Scan Market", use_container_width=True):
        with st.spinner("Scanning Stocks..."):
            df = market_scan()

        if df.empty:
            st.error("No stocks found.")
            return

        if selected_exchange in ("NSE", "BSE") and "Exchange" in df.columns:
            df = df.loc[df["Exchange"] == selected_exchange]
        if min_price > 0 and "Price" in df.columns:
            df = df.loc[df["Price"] >= min_price]

        if df.empty:
            st.warning("No ranked results match the selected exchange and minimum price filters.")
            return

        st.success(f"{len(df)} matching ranked stocks displayed")
        st.dataframe(df, use_container_width=True, height=600)

        csv = df.to_csv(index=False)
        st.download_button("⬇ Download CSV", csv, "market_scan.csv", "text/csv")
