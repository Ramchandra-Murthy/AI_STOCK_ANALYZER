from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
import yfinance as yf

from scanner.institutional_flow import fetch_fii_dii_flow
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

    nifty_1m = nifty_5m = nifty_today = None
    try:
        benchmark = yf.download(
            "^NSEI",
            period="5d",
            interval="1m",
            progress=False,
            auto_adjust=False,
        )
        benchmark_frame = _frame_from_board_download(benchmark, "^NSEI")
        benchmark_close = pd.to_numeric(benchmark_frame["Close"], errors="coerce").dropna()
        if len(benchmark_close) >= 2:
            nifty_1m = (float(benchmark_close.iloc[-1]) / float(benchmark_close.iloc[-2]) - 1) * 100
        if len(benchmark_close) >= 6:
            nifty_5m = (float(benchmark_close.iloc[-1]) / float(benchmark_close.iloc[-6]) - 1) * 100
        daily_benchmark = yf.download(
            "^NSEI",
            period="5d",
            interval="1d",
            progress=False,
            auto_adjust=False,
        )
        daily_frame = _frame_from_board_download(daily_benchmark, "^NSEI")
        daily_close = pd.to_numeric(daily_frame["Close"], errors="coerce").dropna()
        if len(daily_close) >= 2:
            nifty_today = (float(benchmark_close.iloc[-1]) / float(daily_close.iloc[-2]) - 1) * 100
    except (KeyError, TypeError, ValueError, IndexError):
        pass

    board["vs NIFTY 1-min %"] = board["1-min change %"] - nifty_1m if nifty_1m is not None else None
    board["vs NIFTY 5-min %"] = board["5-min change %"] - nifty_5m if nifty_5m is not None else None
    board["vs NIFTY Today %"] = (
        board["Today change %"] - nifty_today if nifty_today is not None else None
    )
    sector_avg = board.groupby("Sector")["Today change %"].transform("mean")
    board["vs Sector Today %"] = board["Today change %"] - sector_avg
    board["Relative Strength"] = (
        board["vs NIFTY Today %"].fillna(0) + board["vs Sector Today %"].fillna(0)
    ) / 2

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
            (signals["2-min change %"].fillna(0) / 0.75)
            .clip(lower=0)
            .combine(
                (signals["3-min change %"].fillna(0) / 1.0).clip(lower=0),
                max,
            )
            .combine(
                (signals["5-min change %"].fillna(0) / 1.5).clip(lower=0),
                max,
            )
            .combine(
                (signals["10-min change %"].fillna(0) / 2.0).clip(lower=0),
                max,
            )
            .combine(
                (signals["15-min change %"].fillna(0) / 2.5).clip(lower=0),
                max,
            )
            .combine(
                (signals["Volume surge x"].fillna(0) / 1.5).clip(lower=0),
                max,
            )
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
            ["Relative Strength", "1-min change %", "Today change %"],
            ascending=[False, False, False],
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

        st.subheader("💪 Relative Strength vs NIFTY & Sector")
        st.caption(
            "Descriptive comparison: stock return minus NIFTY 50 return and minus its current "
            "board-sector average. It is a screening metric, not a trade instruction."
        )
        st.dataframe(
            board[
                [
                    "Symbol",
                    "Exchange",
                    "Sector",
                    "Price",
                    "vs NIFTY 1-min %",
                    "vs NIFTY 5-min %",
                    "vs NIFTY Today %",
                    "vs Sector Today %",
                    "Relative Strength",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Price": st.column_config.NumberColumn("Price (₹)", format="₹ %.2f"),
                "vs NIFTY 1-min %": st.column_config.NumberColumn(
                    "vs NIFTY 1-min", format="%.2f%%"
                ),
                "vs NIFTY 5-min %": st.column_config.NumberColumn(
                    "vs NIFTY 5-min", format="%.2f%%"
                ),
                "vs NIFTY Today %": st.column_config.NumberColumn(
                    "vs NIFTY today", format="%.2f%%"
                ),
                "vs Sector Today %": st.column_config.NumberColumn(
                    "vs sector today", format="%.2f%%"
                ),
                "Relative Strength": st.column_config.NumberColumn(
                    "Relative strength", format="%.2f"
                ),
            },
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
            now_text = now.strftime("%d %b %Y, %H:%M:%S IST")
            active_history = {}
            signal_events = st.session_state.get("live_signal_events", [])
            display = signals.copy()

            for _, row in display.iterrows():
                symbol = row["Symbol"]
                score = float(row["Momentum score"])
                previous = previous_history.get(symbol)
                if previous is None:
                    status = "NEW"
                    first_seen = now_text
                elif score < float(previous.get("score", score)) * 0.90:
                    status = "WEAKENING"
                    first_seen = previous.get("first_seen", now_text)
                else:
                    status = "CONTINUING"
                    first_seen = previous.get("first_seen", now_text)
                active_history[symbol] = {
                    "score": score,
                    "signal": row["Signal"],
                    "first_seen": first_seen,
                    "last_seen": now_text,
                }
                display.loc[display["Symbol"] == symbol, "Status"] = status
                signal_events.append(
                    {
                        "Time": now_text,
                        "Status": status,
                        "Symbol": symbol,
                        "Exchange": row["Exchange"],
                        "Sector": row["Sector"],
                        "Price": float(row["Price"]),
                        "Momentum score": score,
                        "Relative Strength": float(row["Relative Strength"]),
                        "Volume surge x": (
                            float(row["Volume surge x"])
                            if pd.notna(row["Volume surge x"])
                            else None
                        ),
                        "Signal": row["Signal"],
                        "First seen": first_seen,
                    }
                )

            exited = sorted(set(previous_history) - current)
            history_rows = [
                {
                    "Status": "EXITED",
                    "Symbol": symbol,
                    "Signal": previous_history[symbol].get("signal", "—"),
                    "Momentum score": round(float(previous_history[symbol].get("score", 0)), 2),
                    "First seen": previous_history[symbol].get("first_seen", "—"),
                    "Last seen": previous_history[symbol].get("last_seen", "—"),
                }
                for symbol in exited
            ]
            for row in history_rows:
                signal_events.append(
                    {
                        "Time": now_text,
                        "Status": "EXITED",
                        "Symbol": row["Symbol"],
                        "Exchange": "—",
                        "Sector": "—",
                        "Price": None,
                        "Momentum score": row["Momentum score"],
                        "Relative Strength": None,
                        "Volume surge x": None,
                        "Signal": row["Signal"],
                        "First seen": row["First seen"],
                    }
                )

            st.session_state["live_signal_history"] = active_history
            st.session_state["live_signal_events"] = signal_events[-300:]
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
                st.caption(
                    "Signals that disappeared since the previous refresh are retained below as EXITED."
                )
                st.dataframe(
                    pd.DataFrame(history_rows),
                    use_container_width=True,
                    hide_index=True,
                )

            events = pd.DataFrame(st.session_state.get("live_signal_events", []))
            if not events.empty:
                st.subheader("📊 Intraday Signal History & Analytics")
                st.caption(
                    "Session history records each refresh while the app is running. "
                    "It resets when the Streamlit session ends."
                )
                active_events = events[events["Status"] != "EXITED"]
                frequent = (
                    active_events["Symbol"]
                    .value_counts()
                    .rename_axis("Symbol")
                    .reset_index(name="Refreshes seen")
                    .head(10)
                )
                counts = (
                    events.groupby("Status")["Symbol"].count().rename("Observations").reset_index()
                )
                h1, h2 = st.columns(2)
                with h1:
                    st.caption("Most frequently observed signals")
                    st.dataframe(frequent, use_container_width=True, hide_index=True)
                with h2:
                    st.caption("Signal status observations")
                    st.dataframe(counts, use_container_width=True, hide_index=True)
                st.dataframe(
                    events.sort_values("Time", ascending=False).head(100),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Price": st.column_config.NumberColumn("Price (₹)", format="₹ %.2f"),
                        "Momentum score": st.column_config.NumberColumn("Momentum", format="%.2f"),
                        "Relative Strength": st.column_config.NumberColumn(
                            "Relative strength", format="%.2f"
                        ),
                        "Volume surge x": st.column_config.NumberColumn("Volume x", format="%.2fx"),
                    },
                )
                st.download_button(
                    "Download signal history CSV",
                    events.to_csv(index=False).encode("utf-8"),
                    file_name="intraday_signal_history.csv",
                    mime="text/csv",
                    key="download_signal_history",
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

    st.subheader("🏦 Institutional Flow — FII/FPI & DII")
    st.caption(
        "Latest NSE cash-market institutional activity. NSE states these figures are "
        "provisional and may change after custodial confirmation."
    )
    if st.button("Refresh FII/DII flow", key="refresh_institutional_flow"):
        try:
            flow = fetch_fii_dii_flow()
            st.session_state["institutional_flow"] = flow
            st.session_state["institutional_flow_time"] = datetime.now(IST).strftime(
                "%d %b %Y, %H:%M IST"
            )
        except Exception as exc:
            st.error(f"Institutional flow could not be loaded: {exc}")

    flow = st.session_state.get("institutional_flow")
    if flow is not None and not flow.empty:
        fii = flow[
            flow["Category"].astype(str).str.contains("FII", case=False, na=False)
        ]["Net Value (₹ Cr)"].sum()
        dii = flow[
            flow["Category"].astype(str).str.contains("DII", case=False, na=False)
        ]["Net Value (₹ Cr)"].sum()