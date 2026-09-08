from datetime import datetime, timezone

import math

import yfinance as yf


def _valid_number(value):
    try:
        value = float(value)
        return math.isfinite(value) and value > 0
    except (TypeError, ValueError):
        return False


def _snapshot(symbol):
    """Return an observed market snapshot without manufacturing missing values."""
    try:
        hist = yf.Ticker(symbol).history(period="5d", auto_adjust=False)

        if hist is None or hist.empty or "Close" not in hist:
            return None

        closes = hist["Close"].dropna()
        if len(closes) < 2:
            return None

        current = float(closes.iloc[-1])
        previous = float(closes.iloc[-2])

        if not _valid_number(current) or not _valid_number(previous):
            return None

        change = current - previous
        pct = (change / previous) * 100

        timestamp = hist.index[-1]
        if hasattr(timestamp, "to_pydatetime"):
            timestamp = timestamp.to_pydatetime()
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        return {
            "price": round(current, 4),
            "change": round(change, 4),
            "percent": round(pct, 4),
            "as_of": timestamp.isoformat(),
            "source": "yfinance",
            "status": "OBSERVED",
        }

    except Exception:
        return None


def get_market_indices():
    """Fetch observed Indian market index snapshots.

    A failed or incomplete provider response remains unavailable; it is
    never converted into zero, 50, or another synthetic market value.
    """
    indices = {
        "NIFTY 50": "^NSEI",
        "SENSEX": "^BSESN",
        "BANK NIFTY": "^NSEBANK",
        "INDIA VIX": "^INDIAVIX",
    }

    return {name: _snapshot(symbol) for name, symbol in indices.items()}
