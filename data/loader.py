from data.database import connect


def save_dataframe(df, symbol):
    conn = connect()
    cur = conn.cursor()
    df_reset = df.reset_index()
    df_reset = df_reset.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
    for _, row in df_reset.iterrows():
        cur.execute(
            """INSERT OR REPLACE INTO stock_prices VALUES(?,?,?,?,?,?,?)""",
            (
                str(row["Date"].date()),
                symbol,
                float(row["Open"]),
                float(row["High"]),
                float(row["Low"]),
                float(row["Close"]),
                int(row["Volume"]),
            ),
        )
    conn.commit()
    conn.close()
