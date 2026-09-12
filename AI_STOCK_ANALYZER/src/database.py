import sqlite3

import pandas as pd


class DatabaseManager:
    def __init__(self, db_name: str = "stock_analyzer.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_table()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS scan_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            ticker TEXT,
            close_price REAL,
            volume_ratio REAL,
            signal_type TEXT
        );
        """
        self.conn.execute(query)
        self.conn.commit()

    def save_signals(self, df_signals: pd.DataFrame):
        if df_signals.empty:
            return
        for _, row in df_signals.iterrows():
            self.conn.execute(
                "INSERT INTO scan_results (ticker, close_price, volume_ratio, signal_type) VALUES (?, ?, ?, ?)",
                (row["Ticker"], row["Close"], row["Volume_Ratio"], row["Signal_Type"]),
            )
        self.conn.commit()
        print(f"Successfully saved {len(df_signals)} signals to database.")
