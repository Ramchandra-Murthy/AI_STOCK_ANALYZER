from src.database import DatabaseManager
from src.risk_manager import RiskManager
from src.scanner import batch_scan_stocks


def main():
    watchlist = [
        "RELIANCE.NS",
        "TCS.NS",
        "INFY.NS",
        "HDFCBANK.NS",
        "ITC.NS",
        "TMPV.NS",
        "SBIN.NS",
        "BHARTIARTL.NS",
        "ICICIBANK.NS",
        "LT.NS",
        "AXISBANK.NS",
        "SUNPHARMA.NS",
        "KOTAKBANK.NS",
        "WIPRO.NS",
    ]

    print("Starting AI Stock Analyzer batch scan across extended watchlist...")
    signals_df = batch_scan_stocks(watchlist)

    if signals_df.empty:
        print("No setups matching criteria found today across this list.")
        return

    print("\n--- Detected Setups ---")
    print(signals_df.to_string(index=False))

    db = DatabaseManager()
    db.save_signals(signals_df)

    if not signals_df.empty:
        sample = signals_df.iloc[0]
        rm = RiskManager(capital=500000.0, max_risk_pct=1.0)
        sizing = rm.calculate_position_size(entry_price=sample["Close"], atr=sample["ATR"])

        print("\n--- Risk Management Plan for " + str(sample["Ticker"]) + " ---")
        for k, v in sizing.items():
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
