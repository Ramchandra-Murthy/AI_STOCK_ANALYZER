import yfinance as yf
import pandas as pd


def get_price_history(symbol, period="1y"):
    """
    Download historical price data and calculate
    commonly used technical indicators.
    """

    symbol = symbol.strip().upper()

    if "." not in symbol:
        symbol += ".NS"

    df = yf.download(
        symbol,
        period=period,
        auto_adjust=False,
        progress=False
    )

    if df.empty:
        return None

    # --------------------------------------------------------
    # Flatten MultiIndex columns (if returned by yfinance)
    # --------------------------------------------------------

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()

    # ========================================================
    # Exponential Moving Averages (EMA)
    # ========================================================

    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
    df["EMA200"] = df["Close"].ewm(span=200, adjust=False).mean()

    # ========================================================
    # RSI (14)
    # ========================================================

    delta = df["Close"].diff()

    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()

    rs = avg_gain / avg_loss

    df["RSI"] = 100 - (100 / (1 + rs))

    # ========================================================
    # Bollinger Bands (20,2)
    # ========================================================

    df["BB_Middle"] = df["Close"].rolling(window=20).mean()

    rolling_std = df["Close"].rolling(window=20).std()

    df["BB_Upper"] = df["BB_Middle"] + (2 * rolling_std)
    df["BB_Lower"] = df["BB_Middle"] - (2 * rolling_std)

    # ========================================================
    # MACD
    # ========================================================

    ema12 = df["Close"].ewm(span=12, adjust=False).mean()
    ema26 = df["Close"].ewm(span=26, adjust=False).mean()

    df["MACD"] = ema12 - ema26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Histogram"] = df["MACD"] - df["MACD_Signal"]

    # ========================================================
    # ATR (14)
    # ========================================================

    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()

    tr = pd.concat(
        [high_low, high_close, low_close],
        axis=1
    ).max(axis=1)

    df["ATR"] = tr.rolling(window=14).mean()

    # ========================================================
    # Volume Analysis
    # ========================================================

    df["Volume_MA20"] = df["Volume"].rolling(window=20).mean()

    # ========================================================
    # Support & Resistance (20-Day)
    # ========================================================

    df["Support"] = df["Low"].rolling(window=20).min()
    df["Resistance"] = df["High"].rolling(window=20).max()

    return df