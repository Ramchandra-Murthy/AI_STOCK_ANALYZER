from __future__ import annotations

from typing import Any

import pandas as pd
import yfinance as yf

from scanner.market_scanner import BSE_CANDIDATES, NSE_CANDIDATES

CHUNK_SIZE = 10


def _ticker(symbol: str, exchange: str) -> str:
    return f"{symbol}.{ 'NS' if exchange == 'NSE' else 'BO'}"


def _frame_for(history: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if isinstance(history.columns, pd.MultiIndex):
        if ticker not in history.columns.get_level_values(0):
            return pd.DataFrame()
        frame = history[ticker].copy()
    else:
        frame = history.copy()
    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = frame.columns.get_level_values(0)
    return frame


def scan_unusual_activity(limit: int = 20) -> pd.DataFrame:
    """Find positive intraday movers whose latest bar volume is unusually high.

    Uses Yahoo Finance 5-minute candles and the existing broad NSE/BSE candidate
    lists. Relative volume compares the latest bar with the same time-of-day bar
    on up to four preceding sessions; it is a screening signal, not a live-feed
    guarantee.
    """
    rows: list[dict[str, Any]] = []
    universe = [(symbol, "NSE") for symbol in NSE_CANDIDATES] + [
        (symbol, "BSE") for symbol in BSE_CANDIDATES
    ]
    for exchange in ("NSE", "BSE"):
        symbols = NSE_CANDIDATES if exchange == "NSE" else BSE_CANDIDATES
        tickers = [_ticker(symbol, exchange) for symbol in symbols]
        for start in range(0, len(tickers), CHUNK_SIZE):
            chunk = tickers[start : start + CHUNK_SIZE]
            try:
                history = yf.download(
                    tickers=chunk, period="5d", interval="5m", progress=False,
                    auto_adjust=False, group_by="ticker", threads=False,
                )
            except Exception:
                continue
            if history is None or history.empty:
                continue
            for ticker in chunk:
                try:
                    frame = _frame_for(history, ticker)
                    required = {"Open", "High", "Low", "Close", "Volume"}
                    if frame.empty or not required.issubset(frame.columns):
                        continue
                    frame = frame.dropna(subset=list(required)).sort_index()
                    frame = frame[~frame.index.duplicated(keep="last")]
                    if len(frame) < 3:
                        continue
                    dates = pd.Series(frame.index.date, index=frame.index)
                    session_date = dates.iloc[-1]
                    current = frame.loc[dates == session_date]
                    previous = frame.loc[dates != session_date]
                    if current.empty or previous.empty:
                        continue
                    latest = current.iloc[-1]
                    opening_price = float(current.iloc[0]["Open"])
                    price = float(latest["Close"])
                    if opening_price <= 0 or price <= opening_price:
                        continue
                    clock = pd.Timestamp(current.index[-1]).strftime("%H:%M")
                    same_time = previous.loc[previous.index.strftime("%H:%M") == clock, "Volume"]
                    baseline = float(same_time.tail(4).mean()) if not same_time.empty else float("nan")
                    volume = float(latest["Volume"])
                    if pd.isna(baseline) or baseline <= 0:
                        continue
                    relative_volume = volume / baseline
                    if relative_volume < 1.5:
                        continue
                    rows.append({
                        "Symbol": ticker.rsplit(".", 1)[0],
                        "Exchange": exchange,
                        "Last price": round(price, 2),
                        "Session change %": round((price / opening_price - 1) * 100, 2),
                        "Latest bar volume": int(volume),
                        "Relative volume": round(relative_volume, 2),
                        "Latest candle (provider time)": str(current.index[-1]),
                    })
                except (KeyError, TypeError, ValueError, IndexError):
                    continue
    if not rows:
        return pd.DataFrame()
    result = pd.DataFrame(rows)
    return result.sort_values(
        ["Relative volume", "Session change %"], ascending=[False, False]
    ).head(max(1, min(int(limit), 100))).reset_index(drop=True)
