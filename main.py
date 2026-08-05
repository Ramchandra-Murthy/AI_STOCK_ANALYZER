from data.database import create_table
from data.downloader import download_stock
from data.loader import save_dataframe
from data.reader import load_stock
from engine.breakout_engine import detect_breakout
from engine.signal_engine import generate_signal
from indicators.atr import calculate_atr
from indicators.bollinger import calculate_bollinger
from indicators.macd import calculate_macd
from indicators.moving_average import calculate_ema, calculate_sma
from indicators.rsi import calculate_rsi
from indicators.support_resistance import calculate_support_resistance
from indicators.trend import detect_trend


def print_header(title):
    print("\n" + "=" * 70)
    print(title.center(70))
    print("=" * 70)


def main():

    symbol = "RELIANCE.NS"

    print_header("AI STOCK ANALYZER PRO V3.0")

    # --------------------------------------------------
    # DATABASE
    # --------------------------------------------------

    create_table()

    print("\nDownloading latest market data...")

    df = download_stock(symbol)

    save_dataframe(df, symbol)

    df = load_stock(symbol)

    # --------------------------------------------------
    # INDICATORS
    # --------------------------------------------------

    df = calculate_sma(df, 20)
    df = calculate_sma(df, 50)

    df = calculate_ema(df, 20)

    df = calculate_rsi(df, 14)

    df = calculate_macd(df)

    df = calculate_bollinger(df)

    df = calculate_atr(df)

    df = calculate_support_resistance(df)

    # --------------------------------------------------
    # TREND
    # --------------------------------------------------

    trend = detect_trend(df)

    # --------------------------------------------------
    # AI SIGNAL
    # --------------------------------------------------

    signal = generate_signal(df)

    # --------------------------------------------------
    # BREAKOUT
    # --------------------------------------------------

    breakout = detect_breakout(df)

    last = df.iloc[-1]

    # --------------------------------------------------
    # LAST RECORDS
    # --------------------------------------------------

    print_header("LAST FIVE RECORDS")

    print(df.tail())

    # --------------------------------------------------
    # TREND REPORT
    # --------------------------------------------------

    print_header("TREND REPORT")

    for key, value in trend.items():
        print(f"{key:20}: {value}")

    # --------------------------------------------------
    # INDICATOR SUMMARY
    # --------------------------------------------------

    print_header("INDICATOR SUMMARY")

    print(f"SMA 20        : {last['SMA_20']:.2f}")
    print(f"SMA 50        : {last['SMA_50']:.2f}")
    print(f"EMA 20        : {last['EMA_20']:.2f}")
    print(f"RSI           : {last['RSI_14']:.2f}")
    print(f"MACD          : {last['MACD']:.2f}")
    print(f"Signal Line   : {last['Signal']:.2f}")
    print(f"Histogram     : {last['Histogram']:.2f}")
    print(f"ATR           : {last['ATR']:.2f}")

    # --------------------------------------------------
    # BOLLINGER BANDS
    # --------------------------------------------------

    print_header("BOLLINGER BANDS")

    print(f"Upper Band    : {last['BB_Upper']:.2f}")
    print(f"Middle Band   : {last['BB_Middle']:.2f}")
    print(f"Lower Band    : {last['BB_Lower']:.2f}")
    print(f"Close Price   : {last['Close']:.2f}")

    # --------------------------------------------------
    # SUPPORT & RESISTANCE
    # --------------------------------------------------

    print_header("SUPPORT & RESISTANCE")

    print(f"Support       : {last['Support']:.2f}")
    print(f"Resistance    : {last['Resistance']:.2f}")
    print(f"Close Price   : {last['Close']:.2f}")

    distance_support = last["Close"] - last["Support"]
    distance_resistance = last["Resistance"] - last["Close"]

    print(f"Distance to Support    : {distance_support:.2f}")
    print(f"Distance to Resistance : {distance_resistance:.2f}")

    if distance_support < distance_resistance:
        print("Nearest Level : SUPPORT")
    else:
        print("Nearest Level : RESISTANCE")

    # --------------------------------------------------
    # BREAKOUT ENGINE
    # --------------------------------------------------

    print_header("BREAKOUT ENGINE")

    print(f"Signal        : {breakout['Signal']}")
    print(f"Reason        : {breakout['Reason']}")

    # --------------------------------------------------
    # AI SIGNAL ENGINE
    # --------------------------------------------------

    print_header("AI SIGNAL ENGINE")

    print(f"Final Score      : {signal['Score']}")
    print(f"Recommendation   : {signal['Recommendation']}")

    print("\nReasons:")

    for reason in signal["Reasons"]:
        print(f" • {reason}")

    # --------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------

    print_header("FINAL SUMMARY")

    print(f"Stock             : {symbol}")
    print(f"Current Price     : {last['Close']:.2f}")
    print(f"Trend             : {trend['Trend']}")
    print(f"Momentum          : {trend['Momentum']}")
    print(f"Support           : {last['Support']:.2f}")
    print(f"Resistance        : {last['Resistance']:.2f}")
    print(f"Breakout Signal   : {breakout['Signal']}")
    print(f"AI Recommendation : {signal['Recommendation']}")
    print(f"AI Score          : {signal['Score']}")

    print_header("ANALYSIS COMPLETE")


if __name__ == "__main__":
    main()
