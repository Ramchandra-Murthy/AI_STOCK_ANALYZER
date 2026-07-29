import yfinance as yf


def get_market_overview():

    symbols = {
        "NIFTY 50": "^NSEI",
        "BANKNIFTY": "^NSEBANK",
        "SENSEX": "^BSESN",
        "INDIA VIX": "^INDIAVIX"
    }

    market = {}

    for name, ticker in symbols.items():

        try:
            data = yf.download(
                ticker,
                period="2d",
                interval="1d",
                progress=False,
                auto_adjust=True
            )

            if len(data) >= 2:

                last = float(data["Close"].iloc[-1])
                prev = float(data["Close"].iloc[-2])

                change = last - prev
                pct = (change / prev) * 100

                market[name] = {
                    "value": round(last, 2),
                    "change": round(change, 2),
                    "percent": round(pct, 2)
                }

        except Exception:

            market[name] = {
                "value": "--",
                "change": "--",
                "percent": "--"
            }

    return market