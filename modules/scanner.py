import streamlit as st

from scanner.market_scanner import BSE_CANDIDATES, DISPLAY_COUNT, NSE_CANDIDATES, market_scan


def show():
    st.title("📡 AI Market Scanner")
    st.caption("Professional Scanner")
    st.caption(
        f"Dynamic universe: {len(NSE_CANDIDATES)} NSE + "
        f"{len(BSE_CANDIDATES)} BSE candidates; top {DISPLAY_COUNT} are AI-ranked after each scan."
    )

    if st.button("Scan Market", use_container_width=True):
        with st.spinner("Scanning Stocks..."):
            df = market_scan()

        if df.empty:
            st.error("No stocks found.")
            return

        st.success(f"{len(df)} Stocks Scanned")
        st.dataframe(df, use_container_width=True, height=600)

        csv = df.to_csv(index=False)
        st.download_button("⬇ Download CSV", csv, "market_scan.csv", "text/csv")
