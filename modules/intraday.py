from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
import yfinance as yf


IST = ZoneInfo("Asia/Kolkata")


def _ticker(symbol: str, exchange: str) -> str:
    cleaned = symbol.strip().upper()
    suffix = ".NS" if exchange == "NSE" else ".BO"
    if cleaned.endswith((".NS", ".BO")):
        return cleaned
    return f"{cleaned}{suffix}"


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
    data = data.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
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
    cumulative_pv = (typical * data["Volume"]).groupby(session).cumsum()
    cumulative_volume = data["Volume"].groupby(session).cumsum().replace(0, float("nan"))
    data["VWAP"] = cumulative_pv / cumulative_volume
    return data


def show() -> None:
    st.title("⏱️ Intraday Trading")
    st.caption("Technical analysis and paper-trading review — no orders are placed.")

    left, right = st.columns([2, 1])
    with left:
        symbol = st.text_input("Stock symbol", value="RELIANCE", help="Enter the NSE/BSE trading symbol without an exchange suffix.")
    with right:
        exchange = st.selectbox("Exchange", ["NSE", "BSE"])
    interval = st.selectbox("Candle timeframe", ["5m", "15m", "30m"], index=1)

    if not st.button("Analyze intraday", type="primary"):
        st.info("Enter a symbol and select Analyze intraday to load recent candles.")
        return
    if not symbol.strip():
        st.warning("Please enter a stock symbol.")
        return

    ticker = _ticker(symbol, exchange)
    with st.spinner(f"Loading recent {interval} candles for {ticker}…"):
        try:
            intraday = yf.download(ticker, period="5d", interval=interval, progress=False, auto_adjust=False)
            daily = yf.download(ticker, period="5d", interval="1d", progress=False, auto_adjust=False)
        except Exception as exc:  # Provider/network errors vary by symbol and session.
            st.error(f"Could not retrieve market data: {exc}")
            return

    if intraday is None or intraday.empty:
        st.error("No intraday candles were returned. Verify the symbol/exchange and try again during market hours.")
        return

    try:
        data = _prepare(intraday)
    except ValueError as exc:
        st.error(str(exc))
        return
    if data.empty:
        st.error("The provider returned no complete OHLCV candles.")
        return

    latest = data.iloc[-1]
    timestamp = pd.Timestamp(data.index[-1])
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    timestamp_ist = timestamp.tz_convert(IST)
    now_ist = datetime.now(IST)
    st.caption(f"Latest candle: {timestamp_ist:%d %b %Y, %H:%M IST} · Retrieved: {now_ist:%d %b %Y, %H:%M IST}")
    st.caption("Provider timestamps and delayed/partial candles may vary; verify quotes independently before acting.")

    metrics = st.columns(4)
    metrics[0].metric("Last close", f"₹{latest['Close']:,.2f}")
    metrics[1].metric("VWAP", f"₹{latest['VWAP']:,.2f}" if pd.notna(latest["VWAP"]) else "—")
    metrics[2].metric("RSI (14)", f"{latest['RSI 14']:.1f}" if pd.notna(latest["RSI 14"]) else "—")
    metrics[3].metric("EMA 9 / 21", f"{latest['EMA 9']:.2f} / {latest['EMA 21']:.2f}")

    if not daily.empty:
        daily_clean = daily.copy()
        if isinstance(daily_clean.columns, pd.MultiIndex):
            daily_clean.columns = daily_clean.columns.get_level_values(0)
        prior = daily_clean.dropna(subset=["High", "Low", "Close"])
        if len(prior) >= 2:
            previous = prior.iloc[-2]
            pivot = (previous["High"] + previous["Low"] + previous["Close"]) / 3
            st.subheader("Previous-session pivot levels")
            p1, p2, p3 = st.columns(3)
            p1.metric("Pivot", f"₹{pivot:,.2f}")
            p2.metric("R1", f"₹{(2 * pivot - previous['Low']):,.2f}")
            p3.metric("S1", f"₹{(2 * pivot - previous['High']):,.2f}")

    bullish = latest["Close"] > latest["VWAP"] and latest["EMA 9"] > latest["EMA 21"] and latest["MACD"] > latest["MACD signal"]
    bearish = latest["Close"] < latest["VWAP"] and latest["EMA 9"] < latest["EMA 21"] and latest["MACD"] < latest["MACD signal"]
    st.subheader("Technical conditions (not trade instructions)")
    if bullish:
        st.success("Bullish conditions: close above VWAP, EMA 9 above EMA 21, and MACD above its signal line.")
    elif bearish:
        st.warning("Bearish conditions: close below VWAP, EMA 9 below EMA 21, and MACD below its signal line.")
    else:
        st.info("Mixed conditions: the selected indicators do not align in one direction.")

    st.subheader("Recent candles and indicators")
    st.line_chart(data[["Close", "VWAP", "EMA 9", "EMA 21"]].tail(120))
    st.line_chart(data[["RSI 14"]].tail(120))
    st.dataframe(data.tail(20).sort_index(ascending=False), use_container_width=True)
    st.download_button("Download analysis CSV", data.to_csv().encode("utf-8"), file_name=f"{ticker.replace('.', '_')}_{interval}_analysis.csv", mime="text/csv")
    st.warning("For education and paper trading only. Indicators can lag; this module does not calculate guaranteed entries, stop-losses, or targets and does not place trades.")
