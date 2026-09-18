from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
import yfinance as yf

from scanner.price_jump import scan_price_jumps
from scanner.unusual_activity import scan_unusual_activity

IST = ZoneInfo("Asia/Kolkata")


def _ticker(symbol: str, exchange: str) -> str:
    cleaned = symbol.strip().upper()
    suffix = ".NS" if exchange == "NSE" else ".BO"
    return cleaned if cleaned.endswith((".NS", ".BO")) else f"{cleaned}{suffix}"


def _rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    loss = -delta.clip(upper=0).ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = gain / loss.replace(0, float("nan"))
    return 100 - (100 / (1 + rs))


def _prepare(intraday: pd.DataFrame) -> pd.DataFrame:
    data = intraday.copy()
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    required = {"Open", "High", "Low", "Close", "Volume"}
    if not required.issubset(data.columns):
        raise ValueError("The data provider did not return all required OHLCV fields.")
    data = data.dropna(subset=list(required)).sort_index()
    data = data[~data.index.duplicated(keep="last")]
    if data.empty:
        return data
    data["EMA 9"] = data["Close"].ewm(span=9, adjust=False).mean()
    data["EMA 21"] = data["Close"].ewm(span=21, adjust=False).mean()
    data["RSI 14"] = _rsi(data["Close"])
    ema12 = data["Close"].ewm(span=12, adjust=False).mean()
    ema26 = data["Close"].ewm(span=26, adjust=False).mean()
    data["MACD"] = ema12 - ema26
    data["MACD signal"] = data["MACD"].ewm(span=9, adjust=False).mean()
    typical = (data["High"] + data["Low"] + data["Close"]) / 3
    session = pd.Series(data.index.date, index=data.index)
    data["VWAP"] = (typical * data["Volume"]).groupby(session).cumsum() / data["Volume"].groupby(
        session
    ).cumsum().replace(0, float("nan"))
    return data


# Dynamic market board settings.
LIVE_BOARD_REFRESH_SECONDS = 120
LIVE_BOARD_CHUNK_SIZE = 10

# Broad sector labels for the NSE universe. BSE scrips without a verified
# mapping are shown as "Unclassified" rather than inventing a sector.
SECTOR_BY_SYMBOL = {
    "RELIANCE": "Energy",
    "TCS": "IT",
    "INFY": "IT",
    "HCLTECH": "IT",
    "WIPRO": "IT",
    "TECHM": "IT",
    "HDFCBANK": "Financials",
    "ICICIBANK": "Financials",
    "SBIN": "Financials",
    "KOTAKBANK": "Financials",
    "AXISBANK": "Financials",
    "BAJFINANCE": "Financials",
    "BAJAJFINSV": "Financials",
    "INDUSINDBK": "Financials",
    "BANKBARODA": "Financials",
    "CANBK": "Financials",
    "IDFCFIRSTB": "Financials",
    "PNB": "Financials",
    "ICICIGI": "Financials",
    "SBILIFE": "Financials",
    "HDFCLIFE": "Financials",
    "LICI": "Financials",
    "LT": "Industrials",
    "BEL": "Industrials",
    "HAL": "Industrials",
    "SIEMENS": "Industrials",
    "ABB": "Industrials",
    "ADANIENT": "Industrials",
    "ADANIPORTS": "Industrials",
    "IRFC": "Industrials",
    "RVNL": "Industrials",
    "ITC": "Consumer",
    "HINDUNILVR": "Consumer",
    "NESTLEIND": "Consumer",
    "BRITANNIA": "Consumer",
    "TATACONSUM": "Consumer",
    "DABUR": "Consumer",
    "GODREJCP": "Consumer",
    "COLPAL": "Consumer",
    "TITAN": "Consumer",
    "TRENT": "Consumer",
    "DMART": "Consumer",
    "NYKAA": "Consumer",
    "MARUTI": "Automobiles",
    "M&M": "Automobiles",
    "TATAMOTORS": "Automobiles",
    "EICHERMOT": "Automobiles",
    "HEROMOTOCO": "Automobiles",
    "BAJAJ-AUTO": "Automobiles",
    "TVSMOTOR": "Automobiles",
    "ASHOKLEY": "Automobiles",
    "MOTHERSON": "Automobiles",
    "SUNPHARMA": "Pharma",
    "CIPLA": "Pharma",
    "DRREDDY": "Pharma",
    "DIVISLAB": "Pharma",
    "APOLLOHOSP": "Healthcare",
    "ULTRACEMCO": "Cement",
    "GRASIM": "Diversified",
    "HINDALCO": "Metals",
    "TATASTEEL": "Metals",
    "JSWSTEEL": "Metals",
    "VEDL": "Metals",
    "COALINDIA": "Mining",
    "ONGC": "Energy",
    "BPCL": "Energy",
    "IOC": "Energy",
    "GAIL": "Energy",
    "NTPC": "Utilities",
    "POWERGRID": "Utilities",
    "ASIANPAINT": "Materials",
    "PIDILITIND": "Materials",
    "HAVELLS": "Consumer Durables",
    "BHARTIARTL": "Telecom",
    "INDIGO": "Airlines",
    "LODHA": "Real Estate",
    "ZOMATO": "Internet",
    "PAYTM": "Financial Technology",
    "JIOFIN": "Financials",
}


def _live_board_ticker(symbol: str, exchange: str) -> str:
    cleaned = str(symbol).strip().upper()
    suffix = ".NS" if exchange == "NSE" else ".BO"
    return cleaned if cleaned.endswith((".NS", ".BO")) else f"{cleaned}{suffix}"


def _frame_from_board_download(history: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if history is None or history.empty:
        return pd.DataFrame()
    if isinstance(history.columns, pd.MultiIndex):
        if ticker not in history.columns.get_level_values(0):
            return pd.DataFrame()
        frame = history[ticker].copy()
    else:
        frame = history.copy()
    required = {"Close"}
    if not required.issubset(frame.columns):
        return pd.DataFrame()
    frame = frame.dropna(subset=["Close"]).sort_index()
    return frame[~frame.index.duplicated(keep="last")]


def _fetch_live_board() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, int]]:
    """Build a dynamic 20-stock board from the broad NSE+BSE universe."""
    from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES

    candidates = [(symbol, "NSE") for symbol in NSE_CANDIDATES] + [
        (symbol, "BSE") for symbol in BSE_CANDIDATES
    ]
    rows: list[dict[str, object]] = []
    stats = {"candidates": len(candidates), "usable": 0, "failed_chunks": 0}

    for exchange in ("NSE", "BSE"):
        symbols = [symbol for symbol, venue in candidates if venue == exchange]
        tickers = [_live_board_ticker(symbol, exchange) for symbol in symbols]
        for start in range(0, len(tickers), LIVE_BOARD_CHUNK_SIZE):
            chunk = tickers[start : start + LIVE_BOARD_CHUNK_SIZE]
            try:
                history = yf.download(
                    tickers=chunk,
                    period="5d",
                    interval="1m",
                    progress=False,
                    auto_adjust=False,
                    group_by="ticker",
                    threads=False,
                )
                daily_history = yf.download(
                    tickers=chunk,
                    period="5d",
                    interval="1d",
                    progress=False,
                    auto_adjust=False,
                    group_by="ticker",
                    threads=False,
                )
            except Exception:
                stats["failed_chunks"] += 1
                continue

            for ticker in chunk:
                frame = _frame_from_board_download(history, ticker)
                if len(frame) < 2:
                    continue
                stats["usable"] += 1
                close = pd.to_numeric(frame["Close"], errors="coerce").dropna()
                if len(close) < 2:
                    continue
                price = float(close.iloc[-1])
                previous_bar = float(close.iloc[-2])
                change_2m = (price / float(close.iloc[-3]) - 1.0) * 100 if len(close) >= 3 else None
                change_3m = (price / float(close.iloc[-4]) - 1.0) * 100 if len(close) >= 4 else None
                change_5m = (price / float(close.iloc[-6]) - 1.0) * 100 if len(close) >= 6 else None
                change_10m = (
                    (price / float(close.iloc[-11]) - 1.0) * 100 if len(close) >= 11 else None
                )
                change_15m = (
                    (price / float(close.iloc[-16]) - 1.0) * 100 if len(close) >= 16 else None
                )
                volume_surge = None
                if "Volume" in frame.columns:
                    volumes = pd.to_numeric(frame["Volume"], errors="coerce").dropna()
                    if len(volumes) >= 6 and float(volumes.iloc[-1]) > 0:
                        baseline = (
                            float(volumes.iloc[-21:-1].median())
                            if len(volumes) >= 21
                            else float(volumes.iloc[:-1].median())
                        )
                        if baseline > 0:
                            volume_surge = float(volumes.iloc[-1] / baseline)
                breakout = False
                if "High" in frame.columns and len(frame) >= 21:
                    highs = pd.to_numeric(frame["High"], errors="coerce").dropna()
                    if len(highs) >= 21:
                        breakout = price > float(highs.iloc[-21:-1].max())
                if price <= 0 or previous_bar <= 0:
                    continue

                today_change = None
                try:
                    daily_frame = _frame_from_board_download(daily_history, ticker)
                    daily_close = pd.to_numeric(daily_frame["Close"], errors="coerce").dropna()
                    if len(daily_close) >= 2 and float(daily_close.iloc[-2]) > 0:
                        today_change = (price / float(daily_close.iloc[-2]) - 1.0) * 100
                except (KeyError, TypeError, ValueError, IndexError):
                    today_change = None

                symbol = ticker.rsplit(".", 1)[0]
                rows.append(
                    {
                        "Symbol": symbol,
                        "Exchange": exchange,
                        "Sector": SECTOR_BY_SYMBOL.get(symbol, "Unclassified"),
                        "Price": round(price, 2),
                        "1-min change %": round((price / previous_bar - 1.0) * 100, 2),
                        "2-min change %": round(change_2m, 2) if change_2m is not None else None,
                        "3-min change %": round(change_3m, 2) if change_3m is not None else None,
                        "5-min change %": round(change_5m, 2) if change_5m is not None else None,
                        "10-min change %": (
                            round(change_10m, 2) if change_10m is not None else None
                        ),
                        "15-min change %": (
                            round(change_15m, 2) if change_15m is not None else None
                        ),
                        "Volume surge x": (
                            round(volume_surge, 2) if volume_surge is not None else None
                        ),
                        "Breakout": "YES" if breakout else "—",
                        "Today change %": (
                            round(today_change, 2) if today_change is not None else None
                        ),
                        "Last update": str(close.index[-1]),
                    }
                )

    board = pd.DataFrame(rows)
    if board.empty:
        return board, pd.DataFrame(), pd.DataFrame(), stats

    sector_summary = (
        board.groupby("Sector", dropna=False)
        .agg(
            Stocks=("Symbol", "count"),
            Advancers=("Today change %", lambda values: int((values > 0).sum())),
            Decliners=("Today change %", lambda values: int((values < 0).sum())),
            Avg_change_pct=("Today change %", "mean"),
            Avg_1min_pct=("1-min change %", "mean"),
        )
        .reset_index()
        .rename(columns={"Avg_change_pct": "Avg change %", "Avg_1min_pct": "Avg 1-min %"})
    )
    sector_summary["Breadth"] = sector_summary["Advancers"] - sector_summary["Decliners"]
    sector_summary = sector_summary.sort_values(
        ["Breadth", "Avg change %", "Stocks"],
        ascending=[False, False, False],
    ).reset_index(drop=True)

    signals = board[
        (board["2-min change %"].fillna(-999) >= 0.75)
        | (board["3-min change %"].fillna(-999) >= 1.0)
        | (board["Volume surge x"].fillna(0) >= 1.5)
        | (board["Breakout"] == "YES")
    ].copy()
    if not signals.empty:
        signals["Signal"] = "PRICE JUMP"
        signals.loc[signals["Volume surge x"].fillna(0) >= 1.5, "Signal"] = "VOLUME + PRICE"
        signals.loc[signals["Breakout"] == "YES", "Signal"] = "BREAKOUT"
        signals["Momentum score"] = (
            (signals["2-min change %"].fillna(0) / 0.75).clip(lower=0)
            .combine((signals["3-min change %"].fillna(0) / 1.0).clip(lower=0), max)
            .combine((signals["5-min change %"].fillna(0) / 1.5).clip(lower=0), max)
            .combine((signals["10-min change %"].fillna(0) / 2.0).clip(lower=0), max)
            .combine((signals["15-min change %"].fillna(0) / 2.5).clip(lower=0), max)
            .combine((signals["Volume surge x"].fillna(0) / 1.5).clip(lower=0), max)
        )
        signals.loc[signals["Breakout"] == "YES", "Momentum score"] = signals[
            "Momentum score"
        ].clip(lower=1.0)
        signals = signals.sort_values(
            ["Momentum score", "3-min change %", "2-min change %"],
            ascending=[False, False, False],
            na_position="last",
        ).reset_index(drop=True)

    board = (
        board.sort_values(
            ["1-min change %", "Today change %"],
            ascending=[False, False],
            na_position="last",
        )
        .head(20)
        .reset_index(drop=True)
    )
    board.insert(0, "Rank", range(1, len(board) + 1))
    return board, signals, sector_summary, stats


def _show_live_20_panel() -> None:
    st.subheader("📈 Live 20-Stock Market Board")
    st.caption(
        "Top 20 positive movers selected dynamically from the current NSE+BSE candidate universe across sectors. "
        "Prices use Yahoo Finance 1-minute candles and refresh about every 2 minutes; this is not a tick-by-tick exchange feed."
    )

    @st.fragment(run_every=LIVE_BOARD_REFRESH_SECONDS)
    def _live_board_fragment() -> None:
        board, signals, sector_summary, stats = _fetch_live_board()
        if board.empty:
            st.warning(
                "No live board data is currently available. Try again during market hours or check the data provider."
            )
            return

        now = datetime.now(IST)
        st.caption(
            f"Updated: {now:%d %b %Y, %H:%M:%S IST} · "
            f"Universe checked: {stats['candidates']} · Usable symbols: {stats['usable']} · "
            f"Refresh: ~{LIVE_BOARD_REFRESH_SECONDS // 60} min"
        )
        st.dataframe(
            board,
            use_container_width=True,
            hide_index=True,
            height=620,
            column_config={
                "Price": st.column_config.NumberColumn("Price (₹)", format="₹ %.2f"),
                "1-min change %": st.column_config.NumberColumn("1-min %", format="%.2f%%"),
                "Today change %": st.column_config.NumberColumn("Today %", format="%.2f%%"),
            },
        )

        st.subheader("🏭 Sector Momentum & Market Breadth")
        st.caption(
            "Sector figures use symbols with usable Yahoo Finance data from the current NSE+BSE candidate universe."
        )
        total = int(sector_summary["Stocks"].sum())
        advances = int(sector_summary["Advancers"].sum())
        declines = int(sector_summary["Decliners"].sum())
        unchanged = max(total - advances - declines, 0)
        breadth_ratio = advances / declines if declines else float("inf")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Stocks", total)
        col2.metric("Advancing", advances)
        col3.metric("Declining", declines)
        col4.metric("A/D ratio", "∞" if declines == 0 else f"{breadth_ratio:.2f}")

        st.dataframe(
            sector_summary[
                [
                    "Sector",
                    "Stocks",
                    "Advancers",
                    "Decliners",
                    "Breadth",
                    "Avg change %",
                    "Avg 1-min %",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Avg change %": st.column_config.NumberColumn("Avg today %", format="%.2f%%"),
                "Avg 1-min %": st.column_config.NumberColumn("Avg 1-min %", format="%.2f%%"),
            },
        )
        st.caption(
            f"Universe breadth: {advances} advancing · {declines} declining · {unchanged} unchanged/unknown."
        )

        st.subheader("⚡ Intraday Price-Jump & Breakout Signals")
        st.caption(
            "Dynamic screen from the same NSE+BSE universe. Signals use 2-minute ≥0.75%, "
            "3-minute ≥1.0%, 5-minute ≥1.5%, 10-minute ≥2.0%, 15-minute ≥2.5%, "
            "volume ≥1.5× recent intraday median, or a prior-20-bar breakout. "
            "Signal status tracks NEW, CONTINUING, WEAKENING, and EXITED across refreshes. "
            "These are screening conditions, not trade instructions."
        )
        if signals.empty:
            st.info(
                "No price-jump, volume-surge, or breakout conditions detected in the current universe."
            )
        else:
            previous_history = st.session_state.get("live_signal_history", {})
            current = set(signals["Symbol"])
            now = datetime.now(IST)
            active_history = {}
            display = signals.copy()

            for _, row in display.iterrows():
                symbol = row["Symbol"]
                score = float(row["Momentum score"])
                previous = previous_history.get(symbol)
                if previous is None:
                    status = "NEW"
                elif score < float(previous.get("score", score)) * 0.90:
                    status = "WEAKENING"
                else:
                    status = "CONTINUING"
                active_history[symbol] = {
                    "score": score,
                    "signal": row["Signal"],
                    "last_seen": now.strftime("%d %b %Y, %H:%M:%S IST"),
                }
                display.loc[display["Symbol"] == symbol, "Status"] = status

            exited = sorted(set(previous_history) - current)
            history_rows = [
                {
                    "Status": "EXITED",
                    "Symbol": symbol,
                    "Signal": previous_history[symbol].get("signal", "—"),
                    "Momentum score": round(float(previous_history[symbol].get("score", 0)), 2),
                    "Last seen": previous_history[symbol].get("last_seen", "—"),
                }
                for symbol in exited
            ]

            st.session_state["live_signal_history"] = active_history
            display = display.sort_values(
                ["Momentum score", "3-min change %", "2-min change %"],
                ascending=[False, False, False],
                na_position="last",
            ).head(20)
            display.insert(0, "Status", display.pop("Status"))
            st.dataframe(
                display[
                    [
                        "Status",
                        "Symbol",
                        "Exchange",
                        "Sector",
                        "Price",
                        "1-min change %",
                        "2-min change %",
                        "3-min change %",
                        "5-min change %",
                        "10-min change %",
                        "15-min change %",
                        "Today change %",
                        "Volume surge x",
                        "Breakout",
                        "Signal",
                        "Last update",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Price": st.column_config.NumberColumn("Price (₹)", format="₹ %.2f"),
                    "1-min change %": st.column_config.NumberColumn("1-min %", format="%.2f%%"),
                    "2-min change %": st.column_config.NumberColumn("2-min %", format="%.2f%%"),
                    "3-min change %": st.column_config.NumberColumn("3-min %", format="%.2f%%"),
                    "5-min change %": st.column_config.NumberColumn("5-min %", format="%.2f%%"),
                    "10-min change %": st.column_config.NumberColumn("10-min %", format="%.2f%%"),
                    "15-min change %": st.column_config.NumberColumn("15-min %", format="%.2f%%"),
                    "Today change %": st.column_config.NumberColumn("Today %", format="%.2f%%"),
                    "Volume surge x": st.column_config.NumberColumn("Volume x", format="%.2fx"),
                },
            )

            if history_rows:
                st.caption("Signals that disappeared since the previous refresh are retained below as EXITED.")
                st.dataframe(
                    pd.DataFrame(history_rows),
                    use_container_width=True,
                    hide_index=True,
                )

    _live_board_fragment()


def show() -> None:
    st.title("⏱️ Intraday Trading")
    st.caption("Technical analysis and paper-trading review — no orders are placed.")

    _show_live_20_panel()
    st.divider()

    st.subheader("Price jump scanner")
    st.caption(
        "Screens candidate stocks for price rises over the selected lookback. The 2- and 3-minute choices use Yahoo Finance 1-minute candles; longer lookbacks use 5-minute candles. This is a retrospective candle screen, not a live tick alert; Yahoo coverage and delays vary."
    )
    jump_exchange = st.selectbox(
        "Exchange for price jumps",
        ["Both", "NSE", "BSE"],
        key="jump_exchange",
        format_func=lambda value: "NSE + BSE" if value == "Both" else value,
    )
    jump_cap = st.selectbox(
        "Market-cap basket for price jumps",
        ["All caps", "Large cap", "Mid cap", "Small cap"],
        key="jump_cap",
    )
    jump_window = st.selectbox(
        "Jump lookback",
        [2, 3, 5, 10, 15, 30],
        index=2,
        format_func=lambda value: f"{value} minutes",
        key="jump_window",
    )
    jump_threshold = st.selectbox(
        "Minimum price rise",
        [0.5, 1.0, 1.5, 2.0, 3.0],
        index=1,
        format_func=lambda value: f"{value:.1f}%",
        key="jump_threshold",
    )
    jump_limit = st.selectbox(
        "Maximum price-jump results", [10, 20, 30, 50], index=1, key="jump_limit"
    )
    if st.button("Scan for price jumps", key="run_price_jump"):
        with st.spinner(f"Checking {jump_exchange} · {jump_cap.lower()} candidates…"):
            try:
                result = scan_price_jumps(
                    jump_limit, jump_cap, jump_exchange, jump_window, jump_threshold
                )
                st.session_state["price_jump_results"] = result
                st.session_state["price_jump_scan_time"] = datetime.now(IST).strftime(
                    "%d %b %Y, %H:%M IST"
                )
                st.session_state["price_jump_scan_exchange"] = jump_exchange
                st.session_state["price_jump_scan_cap"] = jump_cap
                st.session_state["price_jump_scan_window"] = jump_window
            except Exception as exc:
                st.error(f"Price-jump scan could not complete: {exc}")
    jump_results = st.session_state.get("price_jump_results")
    if jump_results is not None:
        st.caption(
            f"Last scan: {st.session_state.get('price_jump_scan_time', 'unknown')} · Exchange: {st.session_state.get('price_jump_scan_exchange', 'unknown')} · Basket: {st.session_state.get('price_jump_scan_cap', 'unknown')} · Lookback: {st.session_state.get('price_jump_scan_window', 'unknown')} min · Candidate list is limited, not exchange-wide."
        )
        if jump_results.empty:
            st.info(
                "No candidates met this threshold, or the provider returned insufficient candles. Try a lower threshold or scan during market hours."
            )
        else:
            st.dataframe(jump_results, use_container_width=True, hide_index=True)
            st.download_button(
                "Download price-jump CSV",
                jump_results.to_csv(index=False).encode("utf-8"),
                file_name="price_jumps.csv",
                mime="text/csv",
                key="download_price_jumps",
            )

    st.subheader("Unusual activity scanner")
    st.caption(
        "Screens candidate stocks for positive intraday moves and latest 5-minute volume at least 1.5× the average volume of the same time slot in up to four prior sessions. Yahoo Finance coverage and delays may vary."
    )
    exchange_category = st.selectbox(
        "Exchange",
        ["Both", "NSE", "BSE"],
        key="unusual_exchange_category",
        format_func=lambda value: "NSE + BSE" if value == "Both" else value,
    )
    cap_category = st.selectbox(
        "Market-cap basket",
        ["All caps", "Large cap", "Mid cap", "Small cap"],
        key="unusual_cap_category",
    )
    if cap_category == "All caps":
        st.caption(
            "All caps includes the existing NSE and BSE candidate lists. Cap-specific baskets currently screen representative NSE symbols only; they are not exhaustive or official live market-cap classifications."
        )
    else:
        st.caption(
            "Cap-specific baskets screen representative NSE symbols only. BSE scrip codes are not included because the app does not maintain a verified cap-category mapping for them. Constituents and market-cap ranks can change."
        )
    scan_limit = st.selectbox(
        "Maximum results", [10, 20, 30, 50], index=1, key="unusual_scan_limit"
    )
    if st.button("Scan for unusual activity", key="run_unusual_scan"):
        with st.spinner(f"Scanning {exchange_category} · {cap_category.lower()}…"):
            try:
                scan_results = scan_unusual_activity(scan_limit, cap_category, exchange_category)
                st.session_state["unusual_activity_results"] = scan_results
                st.session_state["unusual_activity_scan_category"] = cap_category
                st.session_state["unusual_activity_scan_exchange"] = exchange_category
                st.session_state["unusual_activity_scan_time"] = datetime.now(IST).strftime(
                    "%d %b %Y, %H:%M IST"
                )
            except Exception as exc:
                st.error(f"Scanner could not complete: {exc}")
    scan_results = st.session_state.get("unusual_activity_results")
    if scan_results is not None:
        st.caption(
            f"Last scan: {st.session_state.get('unusual_activity_scan_time', 'unknown')} · Exchange: {st.session_state.get('unusual_activity_scan_exchange', 'unknown')} · Basket: {st.session_state.get('unusual_activity_scan_category', 'unknown')} · Candidate universe is limited; not an exhaustive exchange-wide scan."
        )
        if scan_results.empty:
            st.info(
                "No candidates met the screening conditions, or the data provider returned insufficient data. Try again during market hours."
            )
        else:
            st.dataframe(scan_results, use_container_width=True, hide_index=True)
            st.download_button(
                "Download unusual activity CSV",
                scan_results.to_csv(index=False).encode("utf-8"),
                file_name="unusual_activity.csv",
                mime="text/csv",
                key="download_unusual_activity",
            )

    st.divider()
    left, right = st.columns([2, 1])
    with left:
        symbol = st.text_input(
            "Stock symbol",
            value="RELIANCE",
            help="Enter the NSE/BSE trading symbol without an exchange suffix.",
        )
    with right:
        exchange = st.selectbox("Exchange", ["NSE", "BSE"])
    interval = st.selectbox("Candle timeframe", ["5m", "15m", "30m"], index=1)
    orb_minutes = st.selectbox("Opening range duration", [15, 30], index=0)

    if not st.button("Analyze intraday", type="primary"):
        st.info("Enter a symbol and select Analyze intraday to load recent candles.")
        return
    if not symbol.strip():
        st.warning("Please enter a stock symbol.")
        return

    ticker = _ticker(symbol, exchange)
    with st.spinner(f"Loading recent {interval} candles for {ticker}…"):
        try:
            intraday = yf.download(
                ticker, period="5d", interval=interval, progress=False, auto_adjust=False
            )
            daily = yf.download(
                ticker, period="5d", interval="1d", progress=False, auto_adjust=False
            )
        except Exception as exc:
            st.error(f"Could not retrieve market data: {exc}")
            return
    if intraday is None or intraday.empty:
        st.error(
            "No intraday candles were returned. Verify the symbol/exchange and try again during market hours."
        )
        return
    try:
        data = _prepare(intraday)
    except ValueError as exc:
        st.error(str(exc))
        return
    if data.empty:
        st.error("The provider returned no complete OHLCV candles.")
        return

    timestamp = pd.Timestamp(data.index[-1])
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    timestamp_ist = timestamp.tz_convert(IST)
    now_ist = datetime.now(IST)
    age_minutes = max(0, (now_ist - timestamp_ist.to_pydatetime()).total_seconds() / 60)
    st.caption(
        f"Latest candle: {timestamp_ist:%d %b %Y, %H:%M IST} · Retrieved: {now_ist:%d %b %Y, %H:%M IST}"
    )
    if age_minutes > max(60, int(interval[:-1]) * 3):
        st.warning(
            "Data freshness check: the latest candle is older than expected. This may be normal outside market hours; verify provider timestamps."
        )
    else:
        st.success(
            "Data freshness check: latest candle is recent relative to the selected interval."
        )
    missing = (
        intraday[[c for c in ["Open", "High", "Low", "Close", "Volume"] if c in intraday.columns]]
        .isna()
        .sum()
        .sum()
        if not isinstance(intraday.columns, pd.MultiIndex)
        else 0
    )
    st.caption(
        f"Data quality: {len(data)} complete candles after removing missing OHLCV rows and duplicate timestamps; missing cells detected: {int(missing)}. This does not prove quote accuracy or completeness of the trading session."
    )

    latest = data.iloc[-1]
    metrics = st.columns(4)
    metrics[0].metric("Last close", f"₹{latest['Close']:,.2f}")
    metrics[1].metric("VWAP", f"₹{latest['VWAP']:,.2f}" if pd.notna(latest["VWAP"]) else "—")
    metrics[2].metric("RSI (14)", f"{latest['RSI 14']:.1f}" if pd.notna(latest["RSI 14"]) else "—")
    metrics[3].metric("EMA 9 / 21", f"{latest['EMA 9']:.2f} / {latest['EMA 21']:.2f}")

    bars_needed = max(1, orb_minutes // int(interval[:-1]))
    session_dates = pd.Series(data.index.date, index=data.index)
    today = session_dates.iloc[-1]
    today_data = data.loc[session_dates == today]
    opening = today_data.head(bars_needed)
    st.subheader(f"Opening Range Breakout ({orb_minutes} minutes)")
    if len(opening) < bars_needed:
        st.info(
            f"Opening range is still forming: need {bars_needed} complete {interval} candles; have {len(opening)}."
        )
    else:
        orb_high, orb_low = opening["High"].max(), opening["Low"].min()
        st.caption(
            f"Range high: ₹{orb_high:,.2f} · Range low: ₹{orb_low:,.2f} · Based on first {len(opening)} candles of the latest date in returned data."
        )
        if latest["Close"] > orb_high:
            st.info(
                "Price is above the opening-range high. Treat as a condition to review, not an entry instruction."
            )
        elif latest["Close"] < orb_low:
            st.info(
                "Price is below the opening-range low. Treat as a condition to review, not an entry instruction."
            )
        else:
            st.info("Price remains inside the opening range.")

    if not daily.empty:
        daily_clean = daily.copy()
        if isinstance(daily_clean.columns, pd.MultiIndex):
            daily_clean.columns = daily_clean.columns.get_level_values(0)
        if {"High", "Low", "Close"}.issubset(daily_clean.columns):
            prior = daily_clean.dropna(subset=["High", "Low", "Close"])
            if len(prior) >= 2:
                previous = prior.iloc[-2]
                pivot = (previous["High"] + previous["Low"] + previous["Close"]) / 3
                st.subheader("Previous-session pivot levels")
                p1, p2, p3 = st.columns(3)
                p1.metric("Pivot", f"₹{pivot:,.2f}")
                p2.metric("R1", f"₹{(2 * pivot - previous['Low']):,.2f}")
                p3.metric("S1", f"₹{(2 * pivot - previous['High']):,.2f}")

    bullish = (
        latest["Close"] > latest["VWAP"]
        and latest["EMA 9"] > latest["EMA 21"]
        and latest["MACD"] > latest["MACD signal"]
    )
    bearish = (
        latest["Close"] < latest["VWAP"]
        and latest["EMA 9"] < latest["EMA 21"]
        and latest["MACD"] < latest["MACD signal"]
    )
    st.subheader("Technical conditions (not trade instructions)")
    if bullish:
        st.success(
            "Bullish conditions: close above VWAP, EMA 9 above EMA 21, and MACD above its signal line."
        )
    elif bearish:
        st.warning(
            "Bearish conditions: close below VWAP, EMA 9 below EMA 21, and MACD below its signal line."
        )
    else:
        st.info("Mixed conditions: the selected indicators do not align in one direction.")

    st.subheader("Recent candles and indicators")
    st.line_chart(data[["Close", "VWAP", "EMA 9", "EMA 21"]].tail(120))
    st.line_chart(data[["RSI 14"]].tail(120))
    st.dataframe(data.tail(20).sort_index(ascending=False), use_container_width=True)
    st.download_button(
        "Download analysis CSV",
        data.to_csv().encode("utf-8"),
        file_name=f"{ticker.replace('.', '_')}_{interval}_analysis.csv",
        mime="text/csv",
    )
    st.warning(
        "For education and paper trading only. Indicators can lag; this module does not calculate guaranteed entries, stop-losses, or targets and does not place trades."
    )
