import yfinance as yf


def get_market_indices():
    """
    Fetch live Indian market indices.
    """

    indices = {
        "NIFTY 50": "^NSEI",
        "SENSEX": "^BSESN",
        "BANK NIFTY": "^NSEBANK",
        "INDIA VIX": "^INDIAVIX",
    }

    data = {}

    for name, symbol in indices.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2d")

            if len(hist) >= 2:
                current = hist["Close"].iloc[-1]
                previous = hist["Close"].iloc[-2]

                change = current - previous
                pct = (change / previous) * 100

                data[name] = {
                    "price": current,
                    "change": change,
                    "percent": pct,
                }

        except Exception:
            data[name] = None

    return data
