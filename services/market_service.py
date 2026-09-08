from datetime import timezone
import math

import pandas as pd
import yfinance as yf


def _snapshot(ticker):
    """Return observed latest/previous close plus provider timestamp."""
    try:
        hist = yf.Ticker(ticker).history(period="5d", auto_adjust=False)
        if hist is None or hist.empty or "Close" not in hist:
            return None, None, None

        closes = hist["Close"].dropna()
        if len(closes) < 2:
            return None, None, None

        latest = float(closes.iloc[-1])
        previous = float(closes.iloc[-2])

        if not (math.isfinite(latest) and math.isfinite(previous)):
            return None, None, None
        if latest <= 0 or previous <= 0:
            return None, None, None

        change_pct = ((latest - previous) / previous) * 100

        timestamp = hist.index[-1]
        if hasattr(timestamp, "to_pydatetime"):
            timestamp = timestamp.to_pydatetime()
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        return round(latest, 2), round(change_pct, 2), timestamp.isoformat()

    except Exception:
        return None, None, None


def _get_last_change(ticker):
    return _snapshot(ticker)[:2]


def get_market_indices():
    """Returns observed major market indicators with provenance."""
    symbols = {
        "NIFTY 50": "^NSEI",
        "SENSEX": "^BSESN",
        "BANK NIFTY": "^NSEBANK",
        "INDIA VIX": "^INDIAVIX",
        "USD/INR": "INR=X",
        "GOLD": "GC=F",
    }

    data = {}
    for name, ticker in symbols.items():
        value, change, as_of = _snapshot(ticker)
        data[name] = {
            "value": value,
            "change": change,
            "as_of": as_of,
            "source": "yfinance" if value is not None else None,
            "status": "OBSERVED" if value is not None else "UNAVAILABLE",
        }

    return data


def get_top_movers():
    symbols = [
        "RELIANCE.NS",
        "TCS.NS",
        "INFY.NS",
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "SBIN.NS",
        "LT.NS",
        "ITC.NS",
        "BHARTIARTL.NS",
        "AXISBANK.NS",
    ]

    rows = []
    for symbol in symbols:
        price, change, as_of = _snapshot(symbol)
        if price is None:
            continue
        rows.append(
            {
                "Symbol": symbol.replace(".NS", ""),
                "Price": price,
                "Change %": change,
                "As Of": as_of,
                "Source": "yfinance",
                "Status": "OBSERVED",
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    gainers = df.sort_values("Change %", ascending=False).head(5)
    losers = df.sort_values("Change %", ascending=True).head(5)
    return gainers, losers
