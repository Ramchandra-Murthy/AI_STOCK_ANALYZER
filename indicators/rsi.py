def calculate_rsi(df, period=14):
    delta = df["Close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss.where(avg_loss != 0, 1)
    df[f"RSI_{period}"] = 100 - (100 / (1 + rs))
    df[f"RSI_{period}"] = df[f"RSI_{period}"].clip(0, 100)
    return df
