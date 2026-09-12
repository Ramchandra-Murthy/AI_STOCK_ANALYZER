def calculate_histogram(df):
    if "MACD" not in df.columns or "Signal" not in df.columns:
        from indicators.macd import calculate_macd

        df = calculate_macd(df)
    df["Histogram"] = df["MACD"] - df["Signal"]
    return df
