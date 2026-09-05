def calculate_support_resistance(df, window=10):
    df["Resistance"] = df["High"].rolling(window=window, center=True).max()
    df["Support"] = df["Low"].rolling(window=window, center=True).min()
    df["Resistance"] = df["Resistance"].fillna(method="ffill")
    df["Support"] = df["Support"].fillna(method="ffill")
    return df
