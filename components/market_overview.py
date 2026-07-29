import streamlit as st

from services.market_service import get_market_indices


def show_market_overview():
    """
    Display major market indices as KPI cards.
    """

    st.subheader("🌍 Market Overview")

    data = get_market_indices()

    cols = st.columns(len(data))

    for col, (name, info) in zip(cols, data.items()):

        value = info.get("value")
        change = info.get("change")

        if value is None:
            value = "N/A"
            delta = ""
        else:
            delta = f"{change:+.2f}%"

        col.metric(
            label=name,
            value=value,
            delta=delta
        )