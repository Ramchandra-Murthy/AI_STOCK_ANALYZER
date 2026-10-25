"""Streamlit UI for broad-market and personal-watchlist AI scanning."""

import math

import pandas as pd
import streamlit as st

from scanner.market_scanner import DISPLAY_COUNT, market_scan
from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES
from scanner.watchlist_scanner import scan_watchlist
from services.market_service import WATCHLIST
from services.watchlist_service import WatchlistError
from services.watchlist_ui import get_or_create_default_watchlist


@st.cache_data(ttl=300, show_spinner=False)
def _cached_market_scan(exchange_filter: str) -> pd.DataFrame:
    """Reuse broad-market scan results briefly instead of repeating provider downloads."""
    return market_scan(exchange_filter)


def _normalize_broad_market_confidence(df: pd.DataFrame) -> pd.DataFrame:
    """Prevent cached or legacy scanner rows from presenting scores as calibrated confidence."""
    result = df.copy()
    if "Confidence" in result.columns or "AI Score" in result.columns:
        result["Confidence"] = None
        result["Confidence Status"] = "Not calibrated"
    return result


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
    if "Sector" in df.columns:
        unclassified = df["Sector"].astype(str).str.casefold().eq("unclassified")
        count = int(unclassified.sum())
        if count:
            examples = ", ".join(df.loc[unclassified, "Symbol"].astype(str).head(8))
            st.warning(
                f"{count} returned stock(s) have no sector mapping. "
                f"Review classification before using sector-based comparisons. Examples: {examples}"
            )

    if "Avg Turnover (₹)" in df.columns:
        turnover = pd.to_numeric(df["Avg Turnover (₹)"], errors="coerce")
        low_liquidity = turnover.isna() | turnover.lt(1_000_000)
        count = int(low_liquidity.sum())
        if count:
            examples = ", ".join(df.loc[low_liquidity, "Symbol"].astype(str).head(8))
            st.warning(
                f"{count} returned stock(s) have missing or average daily turnover below ₹10 lakh. "
                f"Execution may be difficult and spreads/slippage may be high. Examples: {examples}"
            )

    st.caption(
        "These checks cover only rows returned by the scanner; they do not verify quote freshness or validate the underlying data provider."
    )



def _live_intraday_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Return only rows explicitly marked tick-live with a timestamp and live status."""
    required = {"Tick Live", "Observed At", "Observation Status", "Latest Observation Price"}
    if not required.issubset(df.columns):
        return df.iloc[0:0].copy()
    tick_live = df["Tick Live"].fillna(False).astype(bool)
    status = df["Observation Status"].astype(str).str.upper()
    observed_at = df["Observed At"].astype(str).str.strip()
    price = pd.to_numeric(df["Latest Observation Price"], errors="coerce")
    verified = (
        tick_live
        & status.str.contains("LIVE", regex=False)
        & ~observed_at.isin(["", "UNKNOWN", "NAT", "NONE"])
        & price.gt(0)
    )
    return df.loc[verified].copy()


def _show_coverage_summary(coverage_rows: list[dict]) -> None:
    """Summarize all pipeline stages before showing per-exchange diagnostics."""
    totals = {}
    for key in (
        "candidates", "mapped_tickers", "unmapped_symbols", "tickers_requested",
        "screen_chunks_requested", "screen_chunks_empty", "screen_tickers_with_data",
        "screen_tickers_missing_data", "histories_returned", "histories_rejected",
        "analysis_requested", "analysis_download_failed", "stale_data_rejected",
        "unknown_timestamp_rejected", "future_timestamp_rejected", "analyses_completed",
        "final_rows", "cached_failures_skipped", "provider_error_chunks",
    ):
        totals[key] = sum(int(row.get(key, 0) or 0) for row in coverage_rows)
    st.subheader("Pipeline totals")
    labels = [
        ("Universe candidates", "candidates"),
        ("Mapped symbols", "mapped_tickers"),
        ("Unmapped symbols", "unmapped_symbols"),
        ("Screen requests", "tickers_requested"),
        ("Usable screen histories", "histories_returned"),
        ("History rejected", "histories_rejected"),
        ("Analysis requested", "analysis_requested"),
        ("Analyses completed", "analyses_completed"),
        ("Final rows", "final_rows"),
    ]
    for start in range(0, len(labels), 3):
        cols = st.columns(3)
        for col, (label, key) in zip(cols, labels[start : start + 3]):
            col.metric(label, totals[key])
    rejection_rows = [
        {"Rejection / issue": label, "Count": totals[key]}
        for label, key in (
            ("Missing/invalid screen history", "screen_tickers_missing_data"),
            ("Empty screen chunks", "screen_chunks_empty"),
            ("Stale analysis history", "stale_data_rejected"),
            ("Unknown timestamp", "unknown_timestamp_rejected"),
            ("Future timestamp", "future_timestamp_rejected"),
            ("Analysis download failed", "analysis_download_failed"),
            ("Provider error chunks", "provider_error_chunks"),
            ("Recently failed tickers skipped", "cached_failures_skipped"),
        )
    ]
    st.caption(
        "Counts are pipeline events and can overlap; they are not necessarily unique-symbol totals."
    )
    st.dataframe(rejection_rows, width="stretch", hide_index=True)

def _show_price_divergence(df: pd.DataFrame) -> None:
    """Flag differences between daily analysis close and the latest market observation."""
    required = ("Price", "Latest Observation Price")
    if not all(column in df.columns for column in required):
        return

    daily_close = pd.to_numeric(df["Price"], errors="coerce")
    observation = pd.to_numeric(df["Latest Observation Price"], errors="coerce")
    valid = daily_close.gt(0) & observation.gt(0)
    comparison = df.loc[valid, ["Symbol", "Exchange", "Price", "Latest Observation Price"]].copy()
    if comparison.empty:
        return

    comparison["Difference %"] = (
        (observation.loc[valid] - daily_close.loc[valid]) / daily_close.loc[valid] * 100
    ).round(2)
    divergent = comparison.loc[comparison["Difference %"].abs() >= 0.5]
    if divergent.empty:
        return

    st.warning(
        f"{len(divergent)} stock(s) have a latest observation price differing from "
        "the daily analysis close by at least 0.5%. This can reflect different observation "
        "times; it is a review flag, not proof that either value is incorrect."
    )
    st.dataframe(divergent, width="stretch", hide_index=True)


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
        f"Broad candidate pool: {len(NSE_CANDIDATES)} NSE + {len(BSE_CANDIDATES)} BSE symbols. "
        f"Exchange preference: {selected_exchange}."
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
        min_turnover = st.number_input(
            "Minimum average daily turnover (₹; 0 = no limit)",
            min_value=0.0,
            value=1_000_000.0,
            step=250_000.0,
            help="Applied to Broad Market results only. This is a liquidity screen, not a guarantee of execution quality.",
        )
        trend_filter = st.selectbox("Trend", ["All", "Bullish", "Bearish", "Sideways"])

    try:
        _, _, watchlist = get_or_create_default_watchlist(
            None, [f"{symbol}.NS" for symbol in WATCHLIST]
        )
    except WatchlistError as exc:
        # A failed personal-watchlist backend must not crash the broad-market scanner.
        watchlist = [f"{symbol}.NS" for symbol in WATCHLIST]
        st.warning(
            "Personal watchlist storage is unavailable; using the built-in scanner "
            f"watchlist for this session. Details: {exc}"
        )

    if not watchlist:
        st.info("Your Personal Watchlist is empty. Add stocks in the Market page first.")

    scan_mode = st.radio("Scan", ["Personal Watchlist", "Broad Market"], horizontal=True)
    exchange_filter = st.selectbox(
        "Exchange",
        ["NSE + BSE", "NSE", "BSE"],
        help="NSE + BSE keeps opportunities from both exchanges in the candidate pool. "
        "Low-liquidity stocks are not removed; use the Risk and turnover information for judgment.",
    )
    if st.button("Scan", width="stretch"):
        with st.spinner("Scanning stocks..."):
            df = (
                scan_watchlist(watchlist)
                if scan_mode == "Personal Watchlist"
                else _cached_market_scan(exchange_filter)
            )
        scanner_coverage = df.attrs.get("scanner_coverage", {})

        if scan_mode == "Broad Market":
            # Streamlit cache/deployments can briefly retain legacy rows with numeric confidence.
            df = _normalize_broad_market_confidence(df)

        if scan_mode == "Broad Market" and scanner_coverage:
            with st.expander("Scan coverage diagnostics", expanded=True):
                st.caption(
                    "Coverage counts describe the broad-market scan pipeline. "
                    "History rejections include symbols without usable two-candle price/volume history."
                )
                coverage_rows = [
                    {"Exchange": exchange, **counts}
                    for exchange, counts in scanner_coverage.items()
                ]
                _show_coverage_summary(coverage_rows)
                st.subheader("Per-exchange diagnostics")
                st.dataframe(coverage_rows, width="stretch", hide_index=True)
                requested = sum(int(row.get("tickers_requested", 0)) for row in coverage_rows)
                usable = sum(int(row.get("histories_returned", 0)) for row in coverage_rows)
                coverage_pct = 100 * usable / max(1, requested)
                if coverage_pct < 50:
                    st.error(
                        f"Low market-history coverage: {usable}/{requested} mapped tickers "
                        f"({coverage_pct:.1f}%) returned usable two-candle history. "
                        "Treat the signal list as incomplete; verify prices independently before trading."
                    )
                elif coverage_pct < 80:
                    st.warning(
                        f"Partial market-history coverage: {usable}/{requested} mapped tickers "
                        f"({coverage_pct:.1f}%). Results may omit valid opportunities."
                    )
                if any(int(row.get("provider_error_chunks", 0)) for row in coverage_rows):
                    st.caption(
                        "Provider error chunks are counted separately; recently failed tickers are briefly skipped to avoid repeated requests."
                    )

        if df.empty:
            st.warning("No stocks could be analyzed for this scan.")
            return

        if exchange_filter in ("NSE", "BSE") and "Exchange" in df.columns:
            df = df.loc[df["Exchange"] == exchange_filter]
        if "Price" in df.columns:
            df = df.loc[df["Price"] >= max(min_price, settings_min_price)]
            if max_price > 0:
                df = df.loc[df["Price"] <= max_price]
        if "RSI" in df.columns:
            df = df.loc[df["RSI"].between(min_rsi, max_rsi)]
        if "AI Score" in df.columns:
            df = df.loc[df["AI Score"] >= min_ai_score]
        if scan_mode == "Broad Market" and min_turnover > 0 and "Avg Turnover (₹)" in df.columns:
            turnover = pd.to_numeric(df["Avg Turnover (₹)"], errors="coerce")
            df = df.loc[turnover.ge(min_turnover)]
        if trend_filter != "All" and "Trend" in df.columns:
            df = df.loc[df["Trend"].astype(str).str.casefold() == trend_filter.casefold()]

        if df.empty:
            st.warning(
                "No results match these filters. Widen the price, RSI, score, trend, or exchange settings and scan again."
            )
            return

        if scan_mode == "Broad Market" and "Data Status" in df.columns:
            st.caption(
                "Broad-market technical signals use daily candles, not tick-live quotes. "
                "Check each row's Last Data Date and Data Status before acting."
            )
        elif scan_mode == "Personal Watchlist" and "Observation Status" in df.columns:
            st.caption(
                "Price and indicators may come from different observation times. "
                "Check Observation Status, Observed At, and Tick Live before relying on a signal."
            )
        _show_price_divergence(df)
        _show_data_quality(df)

        if scan_mode == "Broad Market":
            st.subheader("Daily Technical Candidates")
            st.warning(
                "These are candidates derived from daily candles, not verified live intraday "
                "opportunities. "
                "No live entry price or executable quote is confirmed by this scan."
            )
            st.success(f"{len(df)} daily technical candidate(s) match the filters")
            displayed = df.head(DISPLAY_COUNT)
            st.dataframe(displayed, width="stretch", height=600)
            st.download_button(
                "⬇ Download daily candidates CSV",
                displayed.to_csv(index=False),
                "daily_technical_candidates.csv",
                "text/csv",
            )
            st.subheader("Verified Live Intraday Opportunities")
            st.info(
                "Broad Market results are not promoted to live opportunities. This section only "
                "accepts "
                "personal-watchlist rows explicitly marked Tick Live, with a live status, "
                "observation timestamp, "
                "and positive observation price."
            )
            st.caption(
                "A live label is a provider/status assertion, not a guarantee of exchange execution or quote accuracy."
            )
            st.warning(
                "No live intraday opportunity can be verified from the Broad Market daily-candle "
                "feed alone. "
                "Switch to Personal Watchlist to inspect qualifying live observations."
            )
        else:
            live_rows = _live_intraday_rows(df)
            daily_label = "Daily / non-live watchlist analysis"
            st.subheader(daily_label)
            st.caption(
                "Technical indicators are calculated from historical daily data. A separate "
                "observation may be intraday."
            )
            st.dataframe(df, width="stretch", height=600)
            st.download_button(
                "⬇ Download watchlist scan CSV", df.to_csv(index=False), "watchlist_scan.csv", "text/csv"
            )
            st.subheader("Verified Live Intraday Opportunities")
            if live_rows.empty:
                st.info(
                    "No watchlist row currently meets the strict live-observation checks. "
                    "Missing or non-live observations remain unverified, not assumed live."
                )
            else:
                st.success(f"{len(live_rows)} watchlist row(s) meet the live-observation checks")
                st.dataframe(live_rows, width="stretch", hide_index=True)
                st.download_button(
                    "⬇ Download live-observation candidates CSV",
                    live_rows.to_csv(index=False),
                    "live_intraday_observations.csv",
                    "text/csv",
                )
