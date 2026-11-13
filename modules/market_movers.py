"""Lightweight NSE+BSE market-movers view backed by the shared market service."""

from __future__ import annotations

import streamlit as st

from services.market_service import WATCHLIST, get_top_movers


def _market_watchlist() -> dict[str, str]:
    """Build a small, curated NSE+BSE list without downloading exchange universes."""
    watchlist = dict(WATCHLIST)
    for name, ticker in WATCHLIST.items():
        bse_ticker = ticker.removesuffix(".NS") + ".BO"
        watchlist[f"{name} (BSE)"] = bse_ticker
    return watchlist


def show() -> None:
    """Display the top gainers and losers from a curated NSE+BSE watchlist."""
    st.title("Market Movers")
    st.caption(
        "Top 10 gainers and losers from a curated list of 10 NSE and 10 BSE large-cap listings. "
        "Uses the shared Yahoo Finance quote cache; intraday quotes are indicative, not tick-live."
    )

    try:
        gainers, losers = get_top_movers(_market_watchlist())
    except Exception as exc:
        st.error(f"Market movers are temporarily unavailable: {exc}")
        return

    if gainers.empty and losers.empty:
        st.info("No market-mover quotes are currently available. Try refreshing later.")
        return

    left, right = st.columns(2)
    with left:
        st.subheader("Top 10 Gainers")
        if gainers.empty:
            st.info("No gainers available.")
        else:
            st.dataframe(gainers, hide_index=True, use_container_width=True)
    with right:
        st.subheader("Top 10 Losers")
        if losers.empty:
            st.info("No losers available.")
        else:
            st.dataframe(losers, hide_index=True, use_container_width=True)

    st.caption(
        "Quotes use the shared market-data service. During market hours, one-minute data may be "
        "available; otherwise the service can fall back to the latest daily observation. "
        "Verify prices with your broker before trading."
    )
