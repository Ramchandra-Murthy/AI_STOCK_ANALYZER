from portfolio.portfolio import load_portfolio
from services.analyzer import analyze_stock


def get_live_price(symbol):
    """
    Returns latest market price using the analyzer.
    """

    try:
        result = analyze_stock(symbol)

        last = result["last"]

        return round(float(last["Close"]), 2)

    except Exception:
        return None


def get_portfolio():
    """
    Returns portfolio with live prices and calculations.
    """

    df = load_portfolio()

    if df.empty:
        return df

    cmp_list = []
    current_values = []
    profits = []
    returns = []

    for _, row in df.iterrows():

        cmp = get_live_price(row["symbol"])

        if cmp is None:
            cmp_list.append(None)
            current_values.append(None)
            profits.append(None)
            returns.append(None)
            continue

        investment = row["quantity"] * row["buy_price"]

        current_value = row["quantity"] * cmp

        profit = current_value - investment

        ret = (profit / investment) * 100 if investment else 0

        cmp_list.append(cmp)
        current_values.append(round(current_value, 2))
        profits.append(round(profit, 2))
        returns.append(round(ret, 2))

    df["CMP"] = cmp_list
    df["Current Value"] = current_values
    df["Profit"] = profits
    df["Return %"] = returns

    return df


def get_summary(df):

    if df.empty:
        return {
            "investment": 0,
            "current_value": 0,
            "profit": 0,
            "return": 0,
            "holdings": 0,
        }

    investment = (df["quantity"] * df["buy_price"]).sum()

    current_value = df["Current Value"].fillna(0).sum()

    profit = current_value - investment

    returns = (profit / investment) * 100 if investment else 0

    return {
        "investment": round(investment, 2),
        "current_value": round(current_value, 2),
        "profit": round(profit, 2),
        "return": round(returns, 2),
        "holdings": len(df),
    }
