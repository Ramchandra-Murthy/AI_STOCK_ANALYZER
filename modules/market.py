import pandas as pd
import streamlit as st

from services.market_service import (
    WATCHLIST,
    get_latest_available_price,
    get_market_indices,
    scan_market_universe,
)

# Representative stocks from the existing dashboard universe.
SECTOR_STOCKS = {
    "Financials": ["HDFCBANK", "ICICIBANK", "SBIN"],
    "Information Technology": ["TCS", "INFY"],
    "Energy": ["RELIANCE"],
    "Industrials": ["LT"],
    "Consumer Staples": ["ITC", "HINDUNILVR"],
    "Telecommunications": ["BHARTIARTL"],
}

# Built-in baseline universe. The scanner evaluates the configured exchange
# universe dynamically on every refresh; it does not hard-code the winners.
NSE_UNIVERSE = [
    "RELIANCE",
    "TCS",
    "INFY",
    "HDFCBANK",
    "ICICIBANK",
    "SBIN",
    "LT",
    "ITC",
    "BHARTIARTL",
    "HINDUNILVR",
]
BSE_UNIVERSE = [
    "500325",
    "532540",
    "500209",
    "500180",
    "532174",
    "500112",
    "500510",
    "500875",
    "532454",
    "500696",
]
DEFAULT_WATCHLIST = [f"{symbol}.NS" for symbol in WATCHLIST]


def metric_card(title, value, change):
    if value is None:
        st.metric(title, "N/A", "-")
    else:
        delta = f"{change:+.2f}%" if isinstance(change, (int, float)) else None
        st.metric(title, value, delta)


def _normalize_symbol(symbol, exchange="NSE"):
    normalized = symbol.strip().upper()
    if not normalized:
        return normalized
    if normalized.endswith((".NS", ".BO")):
        return normalized
    suffix = ".BO" if exchange == "BSE" else ".NS"
    return f"{normalized}{suffix}"


def _get_sector_performance():
    rows = []

    for sector, symbols in SECTOR_STOCKS.items():
        changes = []

        for symbol in symbols:
            quote = get_latest_available_price(symbol)
            change = quote.get("change_pct")

            if isinstance(change, (int, float)):
                changes.append(change)

        rows.append(
            {
                "Sector": sector,
                "Average Change %": (
                    round(sum(changes) / len(changes), 2) if changes else None
                ),
                "Stocks Available": len(changes),
            }
        )

    frame = pd.DataFrame(rows)
    return frame.sort_values(
        "Average Change %",
        ascending=False,
        na_position="last",
    ).reset_index(drop=True)


def _get_personal_watchlist(symbols):
    rows = []

    for symbol in symbols:
        quote = get_latest_available_price(symbol)
        rows.append(
            {
                "Symbol": symbol,
                "Exchange": quote.get("exchange"),
                "Price": quote.get("price"),
                "Change %": quote.get("change_pct"),
                "Observed": quote.get("observed_at"),
                "Frequency": quote.get("frequency"),
            }
        )

    return pd.DataFrame(
        rows,
        columns=["Symbol", "Exchange", "Price", "Change %", "Observed", "Frequency"],
    )


def _get_scanner_universe(selected_exchange):
    if selected_exchange == "NSE":
        return {"NSE": NSE_UNIVERSE}
    return {"BSE": BSE_UNIVERSE}


def show():
    st.title("📈 Indian Market Dashboard")

    market = get_market_indices()

    st.caption(
        "Prices are the latest available Yahoo Finance observations. "
        "Intraday data is provider-sourced 1-minute data, not exchange-tick live data; "
        "percentage change is measured against the prior daily close."
    )

    st.subheader("Market Overview")

    c1, c2, c3 = st.columns(3)

    with c1:
        metric_card(
            "NIFTY 50",
            market["NIFTY 50"]["value"],
            market["NIFTY 50"]["change"],
        )

    with c2:
        metric_card(
            "SENSEX",
            market["SENSEX"]["value"],
            market["SENSEX"]["change"],
        )

    with c3:
        metric_card(
            "BANK NIFTY",
            market["BANK NIFTY"]["value"],
            market["BANK NIFTY"]["change"],
        )

    c4, c5, c6 = st.columns(3)

    with c4:
        metric_card(
            "INDIA VIX",
            market["INDIA VIX"]["value"],
            market["INDIA VIX"]["change"],
        )
    with c5:
        metric_card(
            "USD / INR",
            market["USD/INR"]["value"],
            market["USD/INR"]["change"],
        )
    with c6:
        metric_card("GOLD", market["GOLD"]["value"], market["GOLD"]["change"])

    st.divider()

    st.subheader("Exchange")
    selected_exchange = st.radio(
        "Select exchange",
        options=["NSE", "BSE"],
        horizontal=True,
        index=0,
    )

    scanner = scan_market_universe(_get_scanner_universe(selected_exchange), top_n=10)
    if scanner.empty:
        gainers = pd.DataFrame()
        losers = pd.DataFrame()
    else:
        gainers = (
            scanner[scanner["Change %"] >= 0]
            .sort_values("Change %", ascending=False)
            .head(5)
        )
        losers = (
            scanner[scanner["Change %"] < 0]
            .sort_values("Change %", ascending=True)
            .head(5)
        )

    mover_columns = ["Symbol", "Exchange", "Price", "Change %"]
    gainers_display = gainers[[c for c in mover_columns if c in gainers.columns]]
    losers_display = losers[[c for c in mover_columns if c in losers.columns]]

    left, right = st.columns(2)
    with left:
        st.subheader("📈 Top Gainers")
        st.dataframe(gainers_display, hide_index=True, use_container_width=True)
    with right:
        st.subheader("📉 Top Losers")
        st.dataframe(losers_display, hide_index=True, use_container_width=True)

    st.caption(
        f"Scanner universe: {selected_exchange}. "
        "Candidates are re-evaluated from the configured exchange universe on refresh."
    )

    st.divider()

    st.subheader("🔥 Sector Performance")
    st.caption(
        "Average percentage change of the mapped dashboard stocks in each sector. "
        "This is not official NSE sector-index performance."
    )
    sectors = _get_sector_performance()
    st.dataframe(sectors, hide_index=True, use_container_width=True)

    st.divider()

    st.subheader("⭐ Personal Watchlist")
    st.caption(
        "Your list is kept in this Streamlit browser session. "
        "It is not permanently saved across sessions."
    )

    if "personal_watchlist" not in st.session_state:
        st.session_state.personal_watchlist = DEFAULT_WATCHLIST.copy()

    with st.form("add_personal_watchlist_symbol"):
        symbol_input = st.text_input(
            f"Add a {selected_exchange} symbol",
            placeholder=(
                "e.g. TATAMOTORS or TATAMOTORS.NS"
                if selected_exchange == "NSE"
                else "e.g. 500570 or 500570.BO"
            ),
        )
        submitted = st.form_submit_button("Add to watchlist")

    if submitted:
        symbol = _normalize_symbol(symbol_input, selected_exchange)
        if not symbol:
            st.warning("Enter a stock symbol first.")
        elif symbol in st.session_state.personal_watchlist:
            st.info(f"{symbol} is already in your watchlist.")
        else:
            st.session_state.personal_watchlist.append(symbol)
            st.rerun()

    saved_symbols = st.session_state.personal_watchlist
    if saved_symbols:
        watchlist_df = _get_personal_watchlist(saved_symbols)
        st.dataframe(watchlist_df, hide_index=True, use_container_width=True)
        remove_symbol = st.selectbox(
            "Remove a saved symbol",
            options=[""] + saved_symbols,
            format_func=lambda value: "Select a symbol" if value == "" else value,
        )
        if st.button("Remove selected symbol", disabled=not remove_symbol):
            st.session_state.personal_watchlist.remove(remove_symbol)
            st.rerun()
    else:
        st.info("Your personal watchlist is empty. Add a symbol above.")
