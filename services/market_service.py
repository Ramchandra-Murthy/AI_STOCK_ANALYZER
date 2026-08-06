import pandas as pd
import yfinance as yf


def _get_last_change(ticker):
    """
    Returns latest close and % change.
    """
    try:
        hist = yf.Ticker(ticker).history(period="2d")

        latest = hist["Close"].iloc[-1]
        previous = hist["Close"].iloc[-2]

        change_pct = ((latest - previous) / previous) * 100

        return round(latest, 2), round(change_pct, 2)

    except Exception:
        return None, None


def get_market_indices():
    """
    Returns major market indicators.
    """

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

        value, change = _get_last_change(ticker)

        data[name] = {"value": value, "change": change}

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

        try:

            hist = yf.Ticker(symbol).history(period="2d")

            latest = hist["Close"].iloc[-1]
            previous = hist["Close"].iloc[-2]

            change = ((latest - previous) / previous) * 100

            rows.append(
                {
                    "Symbol": symbol.replace(".NS", ""),
                    "Price": round(latest, 2),
                    "Change %": round(change, 2),
                }
            )

        except Exception:
            pass

    df = pd.DataFrame(rows)

    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    gainers = df.sort_values("Change %", ascending=False).head(5)

    losers = df.sort_values("Change %", ascending=True).head(5)

    return gainers, losers
