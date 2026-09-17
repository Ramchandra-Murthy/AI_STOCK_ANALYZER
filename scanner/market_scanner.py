from typing import Any

import pandas as pd
import yfinance as yf

from services.analyzer import analyze_stock

# Broad, liquid candidate universe. The scanner ranks this universe on every scan;
# the displayed ten stocks therefore change with current market conditions.
NSE_CANDIDATES = [
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
    "KOTAKBANK",
    "AXISBANK",
    "MARUTI",
    "M&M",
    "TITAN",
    "SUNPHARMA",
    "ADANIENT",
    "ADANIPORTS",
    "HCLTECH",
    "WIPRO",
    "ULTRACEMCO",
    "NTPC",
    "POWERGRID",
    "ONGC",
    "COALINDIA",
    "TATASTEEL",
    "JSWSTEEL",
    "BAJFINANCE",
    "BAJAJFINSV",
    "ASIANPAINT",
    "NESTLEIND",
    "TECHM",
    "TATAMOTORS",
    "TATACONSUM",
    "CIPLA",
    "DRREDDY",
    "DIVISLAB",
    "APOLLOHOSP",
    "GRASIM",
    "EICHERMOT",
    "HEROMOTOCO",
    "BAJAJ-AUTO",
    "BRITANNIA",
    "HINDALCO",
    "BPCL",
    "IOC",
    "GAIL",
    "INDUSINDBK",
    "BANKBARODA",
    "CANBK",
    "IDFCFIRSTB",
    "PNB",
    "DLF",
    "BEL",
    "HAL",
    "IRFC",
    "RVNL",
    "ZOMATO",
    "NYKAA",
    "PAYTM",
    "JIOFIN",
    "SIEMENS",
    "ABB",
    "VEDL",
    "HAVELLS",
    "DABUR",
    "GODREJCP",
    "PIDILITIND",
    "COLPAL",
    "TRENT",
    "MOTHERSON",
    "TVSMOTOR",
    "ASHOKLEY",
    "INDIGO",
    "DMART",
    "LODHA",
    "ICICIGI",
    "SBILIFE",
    "HDFCLIFE",
    "LICI",
]

# BSE scrip codes; unavailable symbols are skipped.
BSE_CANDIDATES = [
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
    "500247",
    "532215",
    "532500",
    "500520",
    "500114",
    "524715",
    "512599",
    "532921",
    "532281",
    "507685",
    "532538",
    "532555",
    "532898",
    "500312",
    "533278",
    "500470",
    "500228",
    "500034",
    "532978",
    "500820",
    "500790",
    "532755",
    "500570",
    "500800",
    "500087",
    "500124",
    "532488",
    "508869",
    "500300",
    "505200",
    "500182",
    "532977",
    "500825",
    "513349",
    "500547",
    "530965",
    "532155",
    "532187",
    "532134",
    "532483",
    "539437",
    "532461",
    "532868",
    "500049",
    "541154",
    "543257",
    "542649",
    "543320",
    "543384",
    "543396",
    "543940",
    "500550",
    "500002",
    "500295",
    "517354",
    "500096",
    "532424",
    "500331",
    "500830",
    "500251",
    "517334",
    "532343",
    "500477",
    "539448",
    "540376",
    "543287",
    "540133",
    "540719",
    "540777",
    "543526",
]

TOP_CANDIDATES_TO_ANALYZE = 14
DISPLAY_COUNT = 10
DOWNLOAD_CHUNK_SIZE = 10


def _ticker(symbol: str, exchange: str) -> str:
    suffix = "NS" if exchange == "NSE" else "BO"
    return f"{symbol}.{suffix}"


def _batch_change_screen(candidates: dict[str, list[str]]) -> list[tuple[str, str, float]]:
    """Rank candidates in small batches to limit Yahoo Finance batch failures."""
    ranked: list[tuple[str, str, float]] = []
    for exchange, symbols in candidates.items():
        tickers = [_ticker(symbol, exchange) for symbol in symbols]
        for start in range(0, len(tickers), DOWNLOAD_CHUNK_SIZE):
            chunk = tickers[start : start + DOWNLOAD_CHUNK_SIZE]
            try:
                history = yf.download(
                    tickers=chunk,
                    period="5d",
                    interval="1d",
                    auto_adjust=True,
                    progress=False,
                    group_by="ticker",
                    threads=False,
                )
            except Exception:
                continue
            if history is None or history.empty:
                continue

            for ticker in chunk:
                try:
                    if isinstance(history.columns, pd.MultiIndex):
                        if ticker not in history.columns.get_level_values(0):
                            continue
                        close = pd.to_numeric(history[ticker]["Close"], errors="coerce").dropna()
                    else:
                        # yfinance returns flat columns for a single-symbol chunk.
                        close = pd.to_numeric(history["Close"], errors="coerce").dropna()
                    if len(close) < 2:
                        continue
                    latest, previous = float(close.iloc[-1]), float(close.iloc[-2])
                    if previous == 0:
                        continue
                    ranked.append((ticker, exchange, ((latest - previous) / previous) * 100))
                except (KeyError, TypeError, ValueError, IndexError):
                    continue

    ranked.sort(key=lambda row: abs(row[2]), reverse=True)
    return ranked


def _analyze_candidate(ticker: str) -> dict[str, Any] | None:
    try:
        result = analyze_stock(ticker)
        last = result["last"]
        signal = result["signal"]
        trend = result["trend"]
        exchange = "BSE" if ticker.endswith(".BO") else "NSE"
        return {
            "Symbol": ticker.removesuffix(".NS").removesuffix(".BO"),
            "Exchange": exchange,
            "Price": round(float(last["Close"]), 2),
            "Trend": trend["Trend"],
            "RSI": round(float(last["RSI_14"]), 2),
            "MACD": round(float(last["MACD"]), 2),
            "ATR": round(float(last["ATR"]), 2),
            "AI Score": signal["Score"],
            "Confidence": abs(signal["Score"]),
            "Risk": "Medium",
            "Recommendation": signal["Recommendation"],
        }
    except Exception:
        # Unavailable symbols should not flood Streamlit logs or stop other analyses.
        return None


def market_scan() -> pd.DataFrame:
    """Rank a broad NSE+BSE candidate universe and return the top AI-scored stocks."""
    candidates = {"NSE": NSE_CANDIDATES, "BSE": BSE_CANDIDATES}
    movers = _batch_change_screen(candidates)
    if not movers:
        return pd.DataFrame()

    analysis_tickers: list[str] = []
    seen: set[str] = set()
    for ticker, _exchange, _change in movers:
        if ticker not in seen:
            analysis_tickers.append(ticker)
            seen.add(ticker)
        if len(analysis_tickers) >= TOP_CANDIDATES_TO_ANALYZE:
            break

    rows: list[dict[str, Any]] = []
    for ticker in analysis_tickers:
        row = _analyze_candidate(ticker)
        if row is not None:
            rows.append(row)

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return (
        df.sort_values(by=["AI Score", "Confidence"], ascending=[False, False])
        .head(DISPLAY_COUNT)
        .reset_index(drop=True)
    )
