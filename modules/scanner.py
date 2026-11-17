"""Streamlit UI for broad-market and personal-watchlist AI scanning."""

import math

import pandas as pd
import streamlit as st

from scanner.market_scanner import DISPLAY_COUNT, market_scan
from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES
from scanner.watchlist_scanner import scan_watchlist


def _normalize_broad_market_confidence(df: pd.DataFrame) -> pd.DataFrame:
    """Do not present legacy AI scores as calibrated confidence probabilities."""
    result = df.copy()
    if "Confidence" in result.columns or "AI Score" in result.columns:
        result["Confidence"] = None
        result["Confidence Status"] = "Not calibrated"
    return result


def _live_intraday_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only rows with an explicit, timestamped live quote and valid price."""
    required = {
        "Tick Live",
        "Observation Status",
        "Observed At",
        "Latest Observation Price",
    }
    if not required.issubset(df.columns):
        return df.iloc[0:0].copy()

    live = df["Tick Live"].map(
        lambda value: value is True or str(value).strip().casefold() == "true"
    )
    status = df["Observation Status"].astype(str).str.strip().str.upper().eq("LIVE QUOTE")
    observed = pd.to_datetime(df["Observed At"], errors="coerce", utc=True)
    price = pd.to_numeric(df["Latest Observation Price"], errors="coerce")
    valid = observed.notna() & price.gt(0) & price.map(math.isfinite)
    return df.loc[live & status & valid].copy()


def _show_data_quality(df: pd.DataFrame) -> None:
    """Show transparent checks for the rows returned by the scanner."""
    st.subheader("Data quality")
    required = [column for column in ("Symbol", "Price", "RSI", "AI Score") if column in df.columns]
    missing_cells = int(df[required].isna().sum().sum()) if required else 0
    duplicate_symbols = (
        int(df["Symbol"].astype(str).duplicated().sum()) if "Symbol" in df.columns else 0
    )
    invalid_numeric = 0
    for column in ("Price", "RSI", "AI Score"):
        if column in df.columns:
            values = pd.to_numeric(df[column], errors="coerce")
            invalid_numeric += int((values.isna() | ~values.map(math.isfinite)).sum())

    col1, col2, col3 = st.columns(3)
    col1.metric("Rows returned", len(df))
    col2.metric("Missing required cells", missing_cells)
    col3.metric("Duplicate symbols", duplicate_symbols)
    if invalid_numeric:
        st.warning(
            f"{invalid_numeric} numeric field value(s) are missing or invalid. Review the rows before relying on them."
        )
    elif missing_cells or duplicate_symbols:
        st.warning("Some returned data needs review. Check missing cells and duplicate symbols.")
    else:
        st.success("Returned rows passed the available completeness and numeric checks.")
    st.caption(
        "These checks cover only rows returned by the scanner; they do not verify quote freshness or validate the underlying data provider."
    )


def _show_scan_diagnostics(df: pd.DataFrame) -> None:
    """Show how much of the selected exchange universe was actually screened."""
    coverage = df.attrs.get("scanner_coverage", {})
    timings = df.attrs.get("scanner_timings", {})
    sources = df.attrs.get("scanner_universe_sources", {})
    mode = df.attrs.get("scanner_universe_mode", "unknown")

    with st.expander("Universe coverage and scan diagnostics", expanded=mode == "full"):
        st.caption(
            f"Scan mode: {mode}. These counts describe screening coverage, not just displayed rows."
        )
        for exchange, stats in coverage.items():
            st.markdown(f"**{exchange}**")
            cols = st.columns(4)
            cols[0].metric("Universe symbols", stats.get("candidates", 0))
            cols[1].metric("Yahoo tickers mapped", stats.get("tickers_requested", 0))
            cols[2].metric("Histories returned", stats.get("histories_returned", 0))
            cols[3].metric("Analyses completed", stats.get("analyses_completed", 0))
            if stats.get("source"):
                st.caption(
                    f"Source: {stats.get('source')} · "
                    f"Official source: {stats.get('source_status', 'not applicable')} · "
                    f"Unmapped: {stats.get('unmapped_symbols', 0)}"
                )
            if stats.get("latest_bar_at"):
                st.caption(
                    f"Latest {stats.get('screen_frequency', 'screen')} candle: "
                    f"{stats['latest_bar_at']} (Asia/Kolkata) · "
                    f"Stale histories rejected: {stats.get('stale_histories', 0)}"
                )
            reason = stats.get("source_reason")
            if reason:
                st.warning(
                    f"{exchange} official list unavailable: {reason}. Full-universe coverage was not claimed."
                )
        if timings:
            st.caption("Stage timings (seconds)")
            st.json(timings)
        if mode == "full" and sources:
            st.caption("Exchange-list source provenance")
            st.json(sources)


def show():
    st.title("📡 AI Market Scanner")
    st.caption("Professional Scanner")

    settings = st.session_state.get("app_settings", {})
    exchange_preference = settings.get("exchange", "NSE + BSE")
    settings_min_price = float(settings.get("min_price", 0.0) or 0.0)
    min_volume = int(settings.get("min_volume", 0) or 0)
    selected_exchange = (
        exchange_preference if exchange_preference in ("NSE", "BSE") else "NSE + BSE"
    )

    st.caption(
        f"Fast mode basket: {len(NSE_CANDIDATES)} NSE + {len(BSE_CANDIDATES)} BSE symbols. "
        f"Exchange preference: {selected_exchange}. Full mode retrieves the official active equity lists."
    )
    if min_volume > 0:
        st.warning(
            "Minimum volume is saved in Settings but is not applied: current analysis output does not expose traded volume."
        )

    with st.expander("Scanner filters", expanded=True):
        price_col1, price_col2 = st.columns(2)
        with price_col1:
            min_price = st.number_input(
                "Minimum price (₹)",
                min_value=0.0,
                value=settings_min_price,
                step=10.0,
                key="scanner_filter_min_price",
            )
        with price_col2:
            max_price = st.number_input(
                "Maximum price (₹; 0 = no limit)",
                min_value=0.0,
                value=0.0,
                step=10.0,
                key="scanner_filter_max_price",
            )
        rsi_col1, rsi_col2 = st.columns(2)
        with rsi_col1:
            min_rsi = st.number_input(
                "Minimum RSI", min_value=0.0, max_value=100.0, value=0.0, step=1.0
            )
        with rsi_col2:
            max_rsi = st.number_input(
                "Maximum RSI", min_value=0.0, max_value=100.0, value=100.0, step=1.0
            )
        min_ai_score = st.number_input(
            "Minimum AI score", min_value=-100.0, max_value=100.0, value=-100.0, step=1.0
        )
        trend_filter = st.selectbox("Trend", ["All", "Bullish", "Bearish", "Sideways"])

    watchlist = st.session_state.get("personal_watchlist", [])
    if not watchlist:
        st.info(
            "Your Personal Watchlist is empty. Add stocks in the Indian Market Dashboard, then return here."
        )

    scan_mode = st.radio(
        "Scan",
        ["Personal Watchlist", "Fast Market (Curated)", "Full NSE + BSE Universe"],
        horizontal=True,
        help="Full mode retrieves the official active equity lists and screens all symbols that Yahoo Finance can map. It can take longer.",
    )
    exchange_filter = st.selectbox(
        "Exchange",
        ["NSE + BSE", "NSE", "BSE"],
        index=["NSE + BSE", "NSE", "BSE"].index(selected_exchange),
        help="NSE + BSE keeps opportunities from both exchanges in the candidate pool. "
        "Low-liquidity stocks are not removed; use the Risk and turnover information for judgment.",
    )
    if st.button("Scan", use_container_width=True):
        with st.spinner("Scanning stocks..."):
            if scan_mode == "Personal Watchlist":
                df = scan_watchlist(watchlist)
            else:
                universe_mode = "full" if scan_mode == "Full NSE + BSE Universe" else "fast"
                df = market_scan(exchange_filter, universe_mode=universe_mode)

        if scan_mode != "Personal Watchlist":
            df = _normalize_broad_market_confidence(df)
        if scan_mode == "Full NSE + BSE Universe":
            st.warning(
                "Full-universe screening uses Yahoo Finance 5-minute candles and rejects bars older than 20 minutes. "
                "Detailed RSI, MACD, trend and AI score calculations still use daily candles. "
                "Yahoo data may be delayed; check the latest candle timestamp before trading."
            )
        _show_scan_diagnostics(df)

        if df.empty:
            st.warning("No stocks could be analyzed for this scan.")
            return

        if (
            scan_mode == "Personal Watchlist"
            and exchange_filter in ("NSE", "BSE")
            and "Exchange" in df.columns
        ):
            df = df.loc[df["Exchange"] == exchange_filter]

        if df.empty:
            st.warning("No stocks match the selected exchange.")
            return

        _show_data_quality(df)

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
            st.warning(
                "No results match these filters. Widen the price, RSI, score, trend, or exchange settings and scan again."
            )
            return

        st.success(f"{len(df)} matching stocks displayed")
        st.dataframe(
            df.head(DISPLAY_COUNT) if scan_mode != "Personal Watchlist" else df,
            use_container_width=True,
            height=600,
        )
        st.download_button("⬇ Download CSV", df.to_csv(index=False), "market_scan.csv", "text/csv")
