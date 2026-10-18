"""Portfolio valuation service.

Portfolio valuation uses the canonical market-data service directly. It does
not run the full technical analyzer for every holding, avoiding database
writes and avoiding a misleading "live" label for daily market data.
"""

from portfolio.portfolio import load_portfolio
from services.market_service import get_latest_available_price


def get_live_price(symbol):
    """Backward-compatible price helper returning the latest available price."""
    data = get_latest_available_price(symbol)
    return data["price"]


def get_portfolio():
    """Return portfolio with latest available prices and valuation metadata."""
    df = load_portfolio()

    if df.empty:
        return df

    prices = []
    observed_at = []
    sources = []
    frequencies = []
    current_values = []
    profits = []
    returns = []

    for _, row in df.iterrows():
        quote = get_latest_available_price(row["symbol"])
        cmp = quote["price"]

        prices.append(cmp)
        observed_at.append(quote["observed_at"])
        sources.append(quote["source"])
        frequencies.append(quote["frequency"])

        if cmp is None:
            current_values.append(None)
            profits.append(None)
            returns.append(None)
            continue

        investment = row["quantity"] * row["buy_price"]
        current_value = row["quantity"] * cmp
        profit = current_value - investment
        ret = (profit / investment) * 100 if investment else 0

        current_values.append(round(current_value, 2))
        profits.append(round(profit, 2))
        returns.append(round(ret, 2))

    df["CMP"] = prices
    df["Price Observed"] = observed_at
    df["Price Source"] = sources
    df["Price Frequency"] = frequencies
    df["Current Value"] = current_values
    df["Profit"] = profits
    df["Return %"] = returns

    return df


def get_summary(df):
    """Summarize only holdings with available prices and report unvalued holdings."""
    if df.empty:
        return {
            "investment": 0,
            "current_value": 0,
            "profit": 0,
            "return": 0,
            "holdings": 0,
            "valued_holdings": 0,
            "unpriced_holdings": 0,
        }

    if "Current Value" in df.columns:
        valued = df.loc[df["Current Value"].notna()]
        current_value = valued["Current Value"].sum()
    else:
        valued = df.iloc[0:0]
        current_value = 0.0

    investment = (valued["quantity"] * valued["buy_price"]).sum()
    profit = current_value - investment
    returns = (profit / investment) * 100 if investment else 0

    return {
        "investment": round(float(investment), 2),
        "current_value": round(float(current_value), 2),
        "profit": round(float(profit), 2),
        "return": round(float(returns), 2),
        "holdings": len(df),
        "valued_holdings": len(valued),
        "unpriced_holdings": len(df) - len(valued),
    }
