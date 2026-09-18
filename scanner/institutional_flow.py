"""NSE FII/FPI and DII cash-market flow helpers."""

from __future__ import annotations

import pandas as pd
import requests

NSE_FII_DII_URL = "https://www.nseindia.com/api/fiidiiTradeReact"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/131.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Referer": "https://www.nseindia.com/reports/fii-dii",
}


def fetch_fii_dii_flow(timeout: int = 10) -> pd.DataFrame:
    """Fetch the latest NSE FII/FPI and DII cash-market activity."""
    session = requests.Session()
    session.headers.update(_HEADERS)
    session.get("https://www.nseindia.com", timeout=timeout)
    response = session.get(NSE_FII_DII_URL, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list):
        raise ValueError("NSE FII/DII response format was not a list.")
    frame = pd.DataFrame(payload)
    if frame.empty:
        return frame

    rename = {
        "category": "Category",
        "date": "Date",
        "buyValue": "Buy Value (₹ Cr)",
        "sellValue": "Sell Value (₹ Cr)",
        "netValue": "Net Value (₹ Cr)",
    }
    frame = frame.rename(columns=rename)
    required = list(rename.values())
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"NSE FII/DII response is missing: {', '.join(missing)}")
    for column in required[2:]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame[required]
