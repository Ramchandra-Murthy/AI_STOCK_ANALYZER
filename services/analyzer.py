from data.database import create_table
from data.downloader import download_stock
from data.loader import save_dataframe
from data.reader import load_stock

from indicators.moving_average import calculate_sma, calculate_ema
from indicators.rsi import calculate_rsi
from indicators.macd import calculate_macd
from indicators.macd_histogram import calculate_histogram
from indicators.bollinger import calculate_bollinger
from indicators.atr import calculate_atr
from indicators.trend import detect_trend
from indicators.support_resistance import calculate_support_resistance

from engine.signal_engine import generate_signal
from engine.breakout_engine import detect_breakout


def analyze_stock(symbol):

    create_table()

    df = download_stock(symbol)

    save_dataframe(df, symbol)

    df = load_stock(symbol)

    df = df.dropna(subset=["Open", "High", "Low", "Close"])

    df = df.reset_index(drop=True)

    df = calculate_sma(df, 20)
    df = calculate_sma(df, 50)

    df = calculate_ema(df, 20)

    df = calculate_rsi(df, 14)

    df = calculate_macd(df)
    df = calculate_histogram(df)

    df = calculate_bollinger(df)

    df = calculate_atr(df)

    df = calculate_support_resistance(df)

    trend = detect_trend(df)

    signal = generate_signal(df)

    breakout = detect_breakout(df)

    return {
        "df": df,
        "last": df.iloc[-1],
        "trend": trend,
        "signal": signal,
        "breakout": breakout,
    }