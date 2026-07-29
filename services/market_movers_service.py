import yfinance as yf

WATCHLIST = {
    "RELIANCE": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "ICICIBANK": "ICICIBANK.NS",
    "SBIN": "SBIN.NS",
    "LT": "LT.NS",
    "BHARTIARTL": "BHARTIARTL.NS",
    "ITC": "ITC.NS",
    "HINDUNILVR": "HINDUNILVR.NS",
}


def get_market_movers():

    results = []

    for name, symbol in WATCHLIST.items():

        try:
            hist = yf.Ticker(symbol).history(period="2d")

            if len(hist) >= 2:

                current = hist["Close"].iloc[-1]
                previous = hist["Close"].iloc[-2]

                pct = ((current - previous) / previous) * 100

                results.append(
                    {
                        "Stock": name,
                        "Price": round(current, 2),
                        "% Change": round(pct, 2),
                    }
                )

        except Exception:
            pass

    gainers = sorted(results, key=lambda x: x["% Change"], reverse=True)[:5]
    losers = sorted(results, key=lambda x: x["% Change"])[:5]

    return gainers, losers
