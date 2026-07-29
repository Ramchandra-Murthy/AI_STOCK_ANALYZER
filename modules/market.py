import streamlit as st

from services.market_service import (
    get_market_indices,
    get_top_movers
)


def metric_card(title, value, change):

    if value is None:
        st.metric(title, "N/A", "-")
    else:
        st.metric(
            title,
            value,
            f"{change}%"
        )


def show():

    st.title("📈 Indian Market Dashboard")

    market = get_market_indices()

    st.subheader("Market Overview")

    c1, c2, c3 = st.columns(3)

    with c1:
        metric_card(
            "NIFTY 50",
            market["NIFTY 50"]["value"],
            market["NIFTY 50"]["change"]
        )

    with c2:
        metric_card(
            "SENSEX",
            market["SENSEX"]["value"],
            market["SENSEX"]["change"]
        )

    with c3:
        metric_card(
            "BANK NIFTY",
            market["BANK NIFTY"]["value"],
            market["BANK NIFTY"]["change"]
        )

    c4, c5, c6 = st.columns(3)

    with c4:
        metric_card(
            "INDIA VIX",
            market["INDIA VIX"]["value"],
            market["INDIA VIX"]["change"]
        )

    with c5:
        metric_card(
            "USD / INR",
            market["USD/INR"]["value"],
            market["USD/INR"]["change"]
        )

    with c6:
        metric_card(
            "GOLD",
            market["GOLD"]["value"],
            market["GOLD"]["change"]
        )

    st.divider()

    gainers, losers = get_top_movers()

    left, right = st.columns(2)

    with left:
        st.subheader("📈 Top Gainers")
        st.dataframe(
            gainers,
            hide_index=True,
            use_container_width=True
        )

    with right:
        st.subheader("📉 Top Losers")
        st.dataframe(
            losers,
            hide_index=True,
            use_container_width=True
        )

    st.divider()

    st.subheader("🔥 Sector Performance")
    st.info("Coming in Version 2.2")

    st.divider()

    st.subheader("⭐ Personal Watchlist")
    st.info("Coming in Version 2.2")