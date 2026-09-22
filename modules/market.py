import pandas as pd
import streamlit as st

from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES
from services.market_service import (
    WATCHLIST,
    get_company_name,
    get_latest_available_price,
    get_market_indices,
    scan_market_universe,
)

SECTOR_STOCKS = {
    "Financials": ["HDFCBANK", "ICICIBANK", "SBIN"],
    "Information Technology": ["TCS", "INFY"],
    "Energy": ["RELIANCE"],
    "Industrials": ["LT"],
    "Consumer Staples": ["ITC", "HINDUNILVR"],
    "Telecommunications": ["BHARTIARTL"],
}

NSE_UNIVERSE = NSE_CANDIDATES
BSE_UNIVERSE = BSE_CANDIDATES
DEFAULT_WATCHLIST = [f"{symbol}.NS" for symbol in WATCHLIST]


def metric_card(title, value, change):
    if value is None:
        st.metric(title, "N/A", "-")
        return
    delta = f"{change:+.2f}%" if isinstance(change, (int, float)) else None
    st.metric(title, value, delta)


def normalize_symbol(symbol, exchange):
    normalized = symbol.strip().upper()
    if not normalized:
        return normalized
    if normalized.endswith((".NS", ".BO")):
        return normalized
    suffix = ".BO" if exchange == "BSE" else ".NS"
    return f"{normalized}{suffix}"


def get_sector_performance():
    rows = []
    for sector, symbols in SECTOR_STOCKS.items():
        changes = []
        for symbol in symbols:
            change = get_latest_available_price(symbol).get("change_pct")
            if isinstance(change, (int, float)):
                changes.append(change)
        average = round(sum(changes) / len(changes), 2) if changes else None
        rows.append(
            {
                "Sector": sector,
                "Average Change %": average,
                "Stocks Available": len(changes),
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values("Average Change %", ascending=False, na_position="last")
        .reset_index(drop=True)
    )


def get_personal_watchlist(symbols):
    rows = []
    for symbol in symbols:
        quote = get_latest_available_price(symbol)
        rows.append(
            {
                "Symbol": symbol,
                "Name": get_company_name(quote.get("symbol", symbol)),
                "Exchange": quote.get("exchange"),
                "Price": quote.get("price"),
                "Change %": quote.get("change_pct"),
                "Observed": quote.get("observed_at"),
                "Frequency": quote.get("frequency"),
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "Symbol",
            "Name",
            "Exchange",
            "Price",
            "Change %",
            "Observed",
            "Frequency",
        ],
    )


def scanner_universe(exchange):
    if exchange == "NSE":
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
    overview = [
        ("NIFTY 50", "NIFTY 50"),
        ("SENSEX", "SENSEX"),
        ("BANK NIFTY", "BANK NIFTY"),
        ("INDIA VIX", "INDIA VIX"),
        ("USD / INR", "USD/INR"),
        ("GOLD", "GOLD"),
    ]
    columns = st.columns(3)
    for index, (label, key) in enumerate(overview):
        with columns[index % 3]:
            metric_card(label, market[key]["value"], market[key]["change"])

    st.divider()
    st.subheader("Exchange")
    selected_exchange = st.radio(
        "Select exchange",
        ["NSE", "BSE"],
        horizontal=True,
        index=0,
    )

    scanner = scan_market_universe(scanner_universe(selected_exchange), top_n=10)
    if scanner.empty:
        gainers = pd.DataFrame()
        losers = pd.DataFrame()
    else:
        gainers = scanner[scanner["Change %"] >= 0].sort_values("Change %", ascending=False).head(5)
        losers = scanner[scanner["Change %"] < 0].sort_values("Change %", ascending=True).head(5)

    display_columns = ["Symbol", "Name", "Exchange", "Price", "Change %"]
    gainers = gainers[[c for c in display_columns if c in gainers.columns]]
    losers = losers[[c for c in display_columns if c in losers.columns]]

    left, right = st.columns(2)
    with left:
        st.subheader("📈 Top Gainers")
        st.dataframe(gainers, hide_index=True, use_container_width=True)
    with right:
        st.subheader("📉 Top Losers")
        st.dataframe(losers, hide_index=True, use_container_width=True)
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
    st.dataframe(get_sector_performance(), hide_index=True, use_container_width=True)

    st.divider()
    st.subheader("⭐ Personal Watchlist")
    st.caption(
        "Your list is kept in this Streamlit browser session. "
        "It is not permanently saved across sessions."
    )
    if "personal_watchlist" not in st.session_state:
        st.session_state.personal_watchlist = DEFAULT_WATCHLIST.copy()

    with st.form("add_personal_watchlist_symbol"):
        placeholder = (
            "e.g. TATAMOTORS or TATAMOTORS.NS"
            if selected_exchange == "NSE"
            else "e.g. 500570 or 500570.BO"
        )
        symbol_input = st.text_input(f"Add a {selected_exchange} symbol", placeholder=placeholder)
        submitted = st.form_submit_button("Add to watchlist")

    if submitted:
        symbol = normalize_symbol(symbol_input, selected_exchange)
        if not symbol:
            st.warning("Enter a stock symbol first.")
        elif symbol in st.session_state.personal_watchlist:
            st.info(f"{symbol} is already in your watchlist.")
        else:
            st.session_state.personal_watchlist.append(symbol)
            st.rerun()

    saved_symbols = st.session_state.personal_watchlist
    if not saved_symbols:
        st.info("Your personal watchlist is empty. Add a symbol above.")
        return

    st.dataframe(
        get_personal_watchlist(saved_symbols),
        hide_index=True,
        use_container_width=True,
    )
    remove_symbol = st.selectbox(
        "Remove a saved symbol",
        options=[""] + saved_symbols,
        format_func=lambda value: "Select a symbol" if value == "" else value,
    )
    if st.button("Remove selected symbol", disabled=not remove_symbol):
        st.session_state.personal_watchlist.remove(remove_symbol)
        st.rerun()
