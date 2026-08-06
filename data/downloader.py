import pandas as pd
import yfinance as yf


def download_stock(symbol, period="1y", interval="1d"):

    df = yf.download(
        tickers=symbol,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
        multi_level_index=False,
    )

    # Handle MultiIndex columns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Remove rows with missing OHLCV values
    df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"])

    return df
