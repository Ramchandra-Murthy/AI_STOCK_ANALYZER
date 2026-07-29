import pandas as pd

from services.analyzer import analyze_stock


WATCHLIST = [

    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "SBIN.NS",
    "LT.NS",
    "ITC.NS",
    "BHARTIARTL.NS",
    "HINDUNILVR.NS"

]


def market_scan():

    results = []

    for symbol in WATCHLIST:

        try:

            result = analyze_stock(symbol)

            last = result["last"]

            signal = result["signal"]

            trend = result["trend"]

            results.append({

                "Symbol": symbol,

                "Price": round(last["Close"], 2),

                "Trend": trend["Trend"],

                "RSI": round(last["RSI_14"], 2),

                "MACD": round(last["MACD"], 2),

                "ATR": round(last["ATR"], 2),

                "AI Score": signal["Score"],

                "Confidence": abs(signal["Score"]),

                "Risk": "Medium",

                "Recommendation": signal["Recommendation"]

            })

        except Exception as e:

            print(symbol, e)

    df = pd.DataFrame(results)

    if not df.empty:

        df = df.sort_values(
            by="AI Score",
            ascending=False
        )

    return df