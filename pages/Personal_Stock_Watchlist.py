"""Personal stock watchlist page inspired by the supplied reference screenshot."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
import yfinance as yf

from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES
from services.watchlist_service import (
    OWNER_ID,
    WatchlistError,
    add_symbol,
    list_stock_records,
    remove_symbol,
    update_stock_details,
)
from services.watchlist_ui import get_or_create_default_watchlist

EXCHANGES = {"NSE": ".NS", "BSE": ".BO"}
STATUSES = ["Watching", "Bought", "Sold", "Avoid"]
INVESTMENT_TYPES = ["Delivery", "Swing", "Intraday", "Investment", "Options", "Other"]


def _market_session_open() -> bool:
    """Approximate NSE/BSE cash session; exchange holidays are not inferred."""
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    return now.weekday() < 5 and time(9, 15) <= now.time() <= time(15, 30)


def _quote_table(records: list[dict[str, Any]], exchange: str) -> pd.DataFrame:
    """Fetch recent intraday Yahoo observations; provider data may be delayed/unavailable."""
    rows: list[dict[str, Any]] = []
    for record in records:
        symbol = str(record["symbol"])
        ticker = symbol if symbol.endswith((".NS", ".BO")) else symbol + EXCHANGES[exchange]
        try:
            stock = yf.Ticker(ticker)
            intraday = stock.history(period="1d", interval="1m", auto_adjust=False)
            daily = stock.history(period="5d", interval="1d", auto_adjust=False)
            source = intraday if not intraday.empty and "Close" in intraday else daily
            if source.empty or "Close" not in source:
                raise ValueError("No recent price observations")
            close = pd.to_numeric(source["Close"], errors="coerce").dropna()
            volume = pd.to_numeric(source["Volume"], errors="coerce").dropna()
            last = float(close.iloc[-1])
            daily_close = (
                pd.to_numeric(daily["Close"], errors="coerce").dropna()
                if not daily.empty and "Close" in daily
                else pd.Series(dtype=float)
            )
            previous = float(daily_close.iloc[-2]) if len(daily_close) > 1 else None
            change = last - previous if previous is not None else None
            change_pct = (change / previous * 100) if previous else None
            if change is not None and change > 0:
                price_display = f"▲ ₹{last:,.2f}"
                trend = "Up"
            elif change is not None and change < 0:
                price_display = f"▼ ₹{last:,.2f}"
                trend = "Down"
            else:
                price_display = f"→ ₹{last:,.2f}"
                trend = "Flat/unknown"

            target = float(record.get("target_price") or 0)
            stop_loss = float(record.get("stop_loss") or 0)
            entry = float(record.get("entry_price") or 0)
            if target > 0 and last >= target:
                alert = f"🎯 TARGET ACHIEVED — ₹{last:,.2f} reached target ₹{target:,.2f}"
            elif stop_loss > 0 and last <= stop_loss:
                alert = f"🚨 STOP-LOSS BREACHED — ₹{last:,.2f} is at/below ₹{stop_loss:,.2f}"
            elif entry > 0 and last < entry:
                alert = f"⚠️ LOSING — ₹{last:,.2f} is below entry ₹{entry:,.2f}"
            elif trend == "Down":
                alert = "⚠️ PRICE FALLING today"
            else:
                alert = "No target/loss alert"

            # Show total session volume when intraday bars are available.
            # Abbreviate large values so the watchlist is easy to scan (e.g. 12500 -> 12.5K).
            if source is intraday and len(volume):
                volume_value = int(volume.sum())
            else:
                volume_value = int(volume.iloc[-1]) if len(volume) else None

            if volume_value is None:
                volume_display = "—"
            elif volume_value >= 1_000_000_000:
                volume_display = f"{volume_value / 1_000_000_000:.1f}B"
            elif volume_value >= 1_000_000:
                volume_display = f"{volume_value / 1_000_000:.1f}M"
            elif volume_value >= 1_000:
                volume_display = f"{volume_value / 1_000:.1f}K"
            else:
                volume_display = f"{volume_value:,}"

            rows.append(
                {
                    "Symbol": symbol,
                    "Current price": price_display,
                    "Price trend": trend,
                    "Alert": alert,
                    "Change today (₹)": round(change, 2) if change is not None else None,
                    "Change today (%)": round(change_pct, 2) if change_pct is not None else None,
                    "Volume": volume_display,
                    "Data": "Intraday (provider may delay)" if source is intraday else "Daily close (fallback)",
                }
            )
        except Exception:
            rows.append(
                {
                    "Symbol": symbol,
                    "Current price": "Unavailable",
                    "Price trend": "Unknown",
                    "Alert": "Price unavailable — cannot check target or loss",
                    "Change today (₹)": None,
                    "Change today (%)": None,
                    "Volume": None,
                    "Data": "Unavailable",
                }
            )
    return pd.DataFrame(rows)


def _market_gainers(exchange: str, cap_segment: str, limit: int = 10) -> pd.DataFrame:
    """Rank a bounded candidate universe by today's move and label cap only from provider data."""
    candidates = NSE_CANDIDATES if exchange == "NSE" else BSE_CANDIDATES
    suffix = EXCHANGES[exchange]
    tickers = [f"{symbol}{suffix}" for symbol in candidates[:100]]
    if not tickers:
        return pd.DataFrame()

    try:
        intraday = yf.download(
            tickers=tickers,
            period="1d",
            interval="5m",
            group_by="ticker",
            auto_adjust=False,
            progress=False,
            threads=True,
            timeout=20,
        )
        daily = yf.download(
            tickers=tickers,
            period="5d",
            interval="1d",
            group_by="ticker",
            auto_adjust=False,
            progress=False,
            threads=True,
            timeout=20,
        )
    except Exception:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    for ticker in tickers:
        try:
            def series_from(
                frame: pd.DataFrame, field: str, symbol: str = ticker
            ) -> pd.Series:
                if frame.empty:
                    return pd.Series(dtype=float)
                if isinstance(frame.columns, pd.MultiIndex):
                    for level in range(frame.columns.nlevels):
                        if symbol in frame.columns.get_level_values(level):
                            selected = frame.xs(symbol, axis=1, level=level)
                            if field in selected.columns:
                                return pd.to_numeric(selected[field], errors="coerce").dropna()
                    return pd.Series(dtype=float)
                if field in frame.columns:
                    return pd.to_numeric(frame[field], errors="coerce").dropna()
                return pd.Series(dtype=float)

            intraday_close = series_from(intraday, "Close")
            daily_close = series_from(daily, "Close")
            daily_volume = series_from(daily, "Volume")
            if daily_close.empty or len(daily_close) < 2:
                continue
            last = float(intraday_close.iloc[-1]) if not intraday_close.empty else float(daily_close.iloc[-1])
            previous = float(daily_close.iloc[-2])
            if previous <= 0:
                continue
            change_pct = (last / previous - 1) * 100
            # Market-cap data is fetched only for positive movers to limit requests.
            rows.append({
                "Symbol": ticker.removesuffix(suffix),
                "Ticker": ticker,
                "Price": last,
                "Change (%)": change_pct,
                "Volume": int(daily_volume.iloc[-1]) if not daily_volume.empty else None,
                "Market cap (₹)": None,
                "Cap segment": "Unverified",
            })
        except (KeyError, TypeError, ValueError, IndexError):
            continue

    if not rows:
        return pd.DataFrame()
    rows.sort(key=lambda row: row["Change (%)"], reverse=True)

    # Classify the strongest gainers only where Yahoo supplies market cap.
    for row in rows[:30]:
        try:
            market_cap_value = yf.Ticker(row["Ticker"]).fast_info.get("market_cap")
            if market_cap_value:
                # Yahoo market cap is expected in the listing currency; keep labels unverified otherwise.
                market_cap_inr = float(market_cap_value)
                row["Market cap (₹)"] = market_cap_inr
                if market_cap_inr >= 200_000_000_000:
                    row["Cap segment"] = "Large-cap"
                elif market_cap_inr >= 50_000_000_000:
                    row["Cap segment"] = "Mid-cap"
                else:
                    row["Cap segment"] = "Small-cap"
        except Exception:
            continue

    frame = pd.DataFrame(rows)
    if cap_segment != "All":
        frame = frame.loc[frame["Cap segment"] == cap_segment]
    frame = frame.loc[frame["Change (%)"] > 0].head(limit).copy()
    if frame.empty:
        return frame
    frame["Price"] = frame["Price"].map(lambda value: f"₹{value:,.2f}")
    frame["Change (%)"] = frame["Change (%)"].map(lambda value: f"+{value:.2f}%")
    frame["Volume"] = frame["Volume"].map(
        lambda value: "—" if pd.isna(value) else (
            f"{value / 1_000_000:.1f}M" if value >= 1_000_000 else
            f"{value / 1_000:.1f}K" if value >= 1_000 else f"{int(value):,}"
        )
    )
    frame["Market cap"] = frame["Market cap (₹)"].map(
        lambda value: "Unverified" if pd.isna(value) else (
            f"₹{value / 1_000_000_000_000:.2f}T" if value >= 1_000_000_000_000 else
            f"₹{value / 1_000_000_000:.1f}B"
        )
    )
    return frame[["Symbol", "Price", "Change (%)", "Volume", "Cap segment", "Market cap"]].reset_index(drop=True)


def show() -> None:
    st.markdown(
        """
        <style>
        .watchlist-header {font-size:2.1rem;font-weight:750;letter-spacing:-.04em;margin-bottom:.1rem}
        .watchlist-subtitle {color:#64748b;margin-bottom:1rem}
        div[data-testid="stDataFrame"] {border:1px solid #e2e8f0;border-radius:8px}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="watchlist-header">Stocks Watchlist</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="watchlist-subtitle">Personal watchlist · saved investment details · market data when available</div>',
        unsafe_allow_html=True,
    )

    category = st.tabs(["Stocks / F&O", "Mutual Funds", "Commodity", "Currency"])
    with category[1]:
        st.info("Mutual-fund tracking is not connected to this stock-symbol table yet.")
    with category[2]:
        st.info("Commodity tracking is not connected to this stock-symbol table yet.")
    with category[3]:
        st.info("Currency tracking is not connected to this stock-symbol table yet.")

    with category[0]:
        try:
            _, watchlist_id, _ = get_or_create_default_watchlist()
        except WatchlistError as exc:
            st.error("Personal watchlist storage is unavailable.")
            st.warning(str(exc))
            st.info(
                "Check the SUPABASE_URL in Streamlit Secrets and confirm that the "
                "project URL is copied exactly from the Supabase dashboard. "
                "The rest of the app should remain available."
            )
            return

        selected_type = st.radio(
            "Instrument",
            ["Stock", "Futures", "Options"],
            horizontal=True,
            key="personal_watchlist_instrument",
        )
        if selected_type != "Stock":
            st.info(
                f"{selected_type} entries need contract-specific fields (expiry, strike and lot size). "
                "For safety, add only cash-equity symbols here until that support is implemented."
            )

        with st.expander("ADD", expanded=True):
            # Keep the symbol input outside the form so Streamlit updates its
            # session state immediately while the user types. Form widgets do not
            # trigger a rerun until submit, which caused empty/stale symbols on
            # some client sessions.
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.text_input(
                "Stock symbol",
                placeholder="e.g. RELIANCE",
                key="personal_watchlist_add_symbol",
            )
            with st.form("personal_watchlist_add", clear_on_submit=False):
                exchange = col2.selectbox("Exchange", ["NSE", "BSE"])
                investment_type = col3.selectbox("Type", INVESTMENT_TYPES)
                col4, col5, col6 = st.columns(3)
                entry_price = col4.number_input(
                    "Entry price (₹)", min_value=0.0, value=0.0, step=1.0
                )
                target_price = col5.number_input("Target (₹)", min_value=0.0, value=0.0, step=1.0)
                stop_loss = col6.number_input("Stop-loss (₹)", min_value=0.0, value=0.0, step=1.0)
                col7, col8 = st.columns(2)
                quantity = col7.number_input("Quantity", min_value=0, value=0, step=1)
                purchase_date = col8.date_input("Purchase date", value=date.today())
                notes = st.text_input("Notes")
                submitted = st.form_submit_button("＋ Add to watchlist", use_container_width=True)

            if submitted:
                submitted_symbol = st.session_state.get("personal_watchlist_add_symbol", "")
                normalized = str(submitted_symbol or "").strip().upper()
                if not normalized:
                    st.error(
                        "Enter a stock symbol in the Stock symbol field, then "
                        "click ＋ Add to watchlist."
                    )
                else:
                    if not normalized.endswith((".NS", ".BO")):
                        normalized += EXCHANGES[exchange]
                    details = {
                        "investment_type": investment_type,
                        "entry_price": entry_price or None,
                        "target_price": target_price or None,
                        "stop_loss": stop_loss or None,
                        "quantity": quantity or None,
                        "purchase_date": purchase_date.isoformat(),
                        "notes": notes.strip(),
                        "status": "Watching",
                    }
                    try:
                        added = add_symbol(OWNER_ID, watchlist_id, normalized, details)
                        if added:
                            st.success(f"Added {normalized}.")
                        else:
                            st.warning(f"{normalized} is already in this watchlist.")
                        st.rerun()
                    except WatchlistError as exc:
                        st.error(str(exc))

        try:
            records = list_stock_records(OWNER_ID, watchlist_id)
        except WatchlistError as exc:
            st.error(f"Could not load saved watchlist: {exc}")
            return

        filter_mode = st.radio("Filter", ["All", "Gainers", "Losers"], horizontal=True)

        with st.expander("📈 Intraday Market Gainers — large, mid and small caps", expanded=True):
            st.caption(
                "Screens a bounded list of NSE/BSE candidates. Market-cap labels are shown only when "
                "the data provider supplies a value; quotes may be delayed and are not exchange-certified."
            )
            gain_cols = st.columns([1, 1, 1])
            gain_exchange = gain_cols[0].selectbox("Exchange", ["NSE", "BSE"], key="gainers_exchange")
            gain_segment = gain_cols[1].selectbox(
                "Market cap", ["All", "Large-cap", "Mid-cap", "Small-cap", "Unverified"],
                key="gainers_cap_segment",
            )
            gain_count = gain_cols[2].selectbox("Show", [10, 20, 30], index=0, key="gainers_count")
            if st.button("Scan market gainers", key="scan_market_gainers", type="primary"):
                with st.spinner("Scanning available market data…"):
                    st.session_state["personal_market_gainers_result"] = _market_gainers(
                        gain_exchange, gain_segment, int(gain_count)
                    )
                    st.session_state["personal_market_gainers_exchange"] = gain_exchange
            gainers = st.session_state.get("personal_market_gainers_result")
            if isinstance(gainers, pd.DataFrame):
                if gainers.empty:
                    st.warning(
                        "No gainers could be verified for this selection. Try another cap segment or "
                        "scan again when the market is open."
                    )
                else:
                    st.dataframe(gainers, use_container_width=True, hide_index=True)
                    choices = gainers["Symbol"].astype(str).tolist()
                    selected_gainer = st.selectbox(
                        "Choose a gainer to add", choices, key="personal_gainer_to_add"
                    )
                    add_col, entry_col, target_col, stop_col = st.columns(4)
                    add_entry = entry_col.number_input(
                        "Entry (₹)", min_value=0.0, value=0.0, step=1.0, key="gainer_entry"
                    )
                    add_target = target_col.number_input(
                        "Target (₹)", min_value=0.0, value=0.0, step=1.0, key="gainer_target"
                    )
                    add_stop = stop_col.number_input(
                        "Stop-loss (₹)", min_value=0.0, value=0.0, step=1.0, key="gainer_stop"
                    )
                    if add_col.button("＋ Add to my watchlist", key="add_selected_gainer"):
                        suffix = EXCHANGES.get(
                            st.session_state.get("personal_market_gainers_exchange", "NSE"), ".NS"
                        )
                        selected_ticker = selected_gainer + suffix
                        existing_symbols = {str(item.get("symbol", "")).upper() for item in records}
                        if selected_ticker.upper() in existing_symbols:
                            st.info(f"{selected_ticker} is already in your watchlist.")
                        else:
                            try:
                                add_symbol(
                                    OWNER_ID, watchlist_id, selected_ticker,
                                    {
                                        "investment_type": "Intraday",
                                        "entry_price": add_entry or None,
                                        "target_price": add_target or None,
                                        "stop_loss": add_stop or None,
                                        "status": "Watching",
                                        "notes": "Added from Intraday Market Gainers panel",
                                    },
                                )
                                st.success(f"Added {selected_ticker} to your watchlist.")
                                st.rerun()
                            except WatchlistError as exc:
                                st.error(f"Could not add {selected_ticker}: {exc}")

        if not records:
            st.info("Your watchlist is empty. Add your first stock above.")
        else:
            st.caption(
                "Prices refresh automatically about every 60 seconds during the weekday "
                "09:15–15:30 IST session. Yahoo Finance data can be delayed or unavailable; "
                "exchange holidays are not inferred and this is not a guaranteed real-time feed."
            )

            @st.fragment(run_every="60s" if _market_session_open() else None)
            def render_live_quotes() -> None:
                try:
                    quotes = _quote_table(records, "NSE")
                    if filter_mode == "Gainers" and "Change today (%)" in quotes:
                        quotes = quotes.loc[quotes["Change today (%)"] > 0]
                    elif filter_mode == "Losers" and "Change today (%)" in quotes:
                        quotes = quotes.loc[quotes["Change today (%)"] < 0]
                    def color_price_direction(row: pd.Series) -> list[str]:
                        trend = row.get("Price trend")
                        if trend == "Up":
                            return [
                                "color: #15803d; font-weight: 700" if col == "Current price"
                                else "color: #15803d" if col == "Price trend"
                                else ""
                                for col in row.index
                            ]
                        if trend == "Down":
                            return [
                                "color: #dc2626; font-weight: 700" if col == "Current price"
                                else "color: #dc2626" if col == "Price trend"
                                else ""
                                for col in row.index
                            ]
                        return ["" for _ in row.index]

                    styled_quotes = quotes.style.apply(color_price_direction, axis=1)
                    st.dataframe(styled_quotes, use_container_width=True, hide_index=True)
                    now = datetime.now(ZoneInfo("Asia/Kolkata")).strftime("%H:%M:%S IST")
                    st.caption(f"Last quote check: {now}")
                except Exception as exc:
                    st.warning(f"Price refresh failed; the rest of your watchlist remains available. {exc}")

            render_live_quotes()

            with st.expander("Investment diary — edit saved details"):
                symbols = [str(record["symbol"]) for record in records]
                selected = st.selectbox("Select stock", symbols)
                record = next(item for item in records if item["symbol"] == selected)
                with st.form("personal_watchlist_edit"):
                    cols = st.columns(3)
                    entry = cols[0].number_input(
                        "Entry price (₹)",
                        min_value=0.0,
                        value=float(record.get("entry_price") or 0.0),
                        key=f"edit_entry_{selected}",
                    )
                    target = cols[1].number_input(
                        "Target (₹)",
                        min_value=0.0,
                        value=float(record.get("target_price") or 0.0),
                        key=f"edit_target_{selected}",
                    )
                    stop = cols[2].number_input(
                        "Stop-loss (₹)",
                        min_value=0.0,
                        value=float(record.get("stop_loss") or 0.0),
                        key=f"edit_stop_{selected}",
                    )
                    cols2 = st.columns(3)
                    qty = cols2[0].number_input(
                        "Quantity",
                        min_value=0,
                        value=int(record.get("quantity") or 0),
                        step=1,
                        key=f"edit_qty_{selected}",
                    )
                    kind = cols2[1].selectbox(
                        "Investment type",
                        INVESTMENT_TYPES,
                        index=(
                            INVESTMENT_TYPES.index(record.get("investment_type") or "Other")
                            if record.get("investment_type") in INVESTMENT_TYPES
                            else INVESTMENT_TYPES.index("Other")
                        ),
                        key=f"edit_type_{selected}",
                    )
                    status = cols2[2].selectbox(
                        "Status",
                        STATUSES,
                        index=(
                            STATUSES.index(record.get("status") or "Watching")
                            if record.get("status") in STATUSES
                            else 0
                        ),
                        key=f"edit_status_{selected}",
                    )
                    note = st.text_area(
                        "Notes", value=str(record.get("notes") or ""), key="edit_notes"
                    )
                    save = st.form_submit_button("Save investment details")
                    if save:
                        try:
                            update_stock_details(
                                OWNER_ID,
                                watchlist_id,
                                selected,
                                {
                                    "entry_price": entry or None,
                                    "target_price": target or None,
                                    "stop_loss": stop or None,
                                    "quantity": qty or None,
                                    "investment_type": kind,
                                    "purchase_date": record.get("purchase_date"),
                                    "notes": note,
                                    "status": status,
                                },
                            )
                            st.success("Investment details saved.")
                            st.rerun()
                        except WatchlistError as exc:
                            st.error(str(exc))

                pending_delete_key = "personal_watchlist_pending_delete"
                if st.button(
                    "Remove selected stock",
                    type="secondary",
                    key=f"remove_stock_{selected}",
                ):
                    # Set the pending target and render the confirmation immediately
                    # in this run; do not rerun before the prompt becomes visible.
                    st.session_state[pending_delete_key] = selected

                if st.session_state.get(pending_delete_key) == selected:
                    st.warning(
                        f"Are you sure you want to delete {selected} from your watchlist? "
                        "This cannot be undone."
                    )
                    confirm_col, cancel_col = st.columns(2)
                    with confirm_col:
                        if st.button(
                            f"Yes, delete {selected}",
                            type="primary",
                            key=f"confirm_delete_{selected}",
                        ):
                            try:
                                removed = remove_symbol(OWNER_ID, watchlist_id, selected)
                                st.session_state.pop(pending_delete_key, None)
                                if removed:
                                    st.session_state.pop(cache_key, None)
                                    st.success(f"Removed {selected}.")
                                    st.rerun()
                                else:
                                    st.warning("Stock was not found.")
                            except WatchlistError as exc:
                                st.error(f"Could not remove {selected}: {exc}")
                    with cancel_col:
                        if st.button("No, keep stock", key=f"cancel_delete_{selected}"):
                            st.session_state.pop(pending_delete_key, None)
                            st.rerun()


show()
