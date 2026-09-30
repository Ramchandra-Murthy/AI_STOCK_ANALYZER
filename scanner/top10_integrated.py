"""Top-10 market mover scanner with Chapter 4-10 workflow signals."""

from __future__ import annotations

import pandas as pd

from engine.live_integrated_scanner import scan_integrated_tickers
from scanner.market_scanner import _batch_change_screen
from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES

TOP10_ANALYSIS_PERIOD = "3mo"


def scan_top10_integrated(
    *,
    period: str = "6mo",
    interval: str = "1d",
) -> pd.DataFrame:
    """Return the ten largest liquid daily movers with workflow signals."""
    del period, interval
    candidates = {
        "NSE": NSE_CANDIDATES,
        "BSE": BSE_CANDIDATES,
    }
    movers = _batch_change_screen(candidates)[:10]
    if not movers:
        return pd.DataFrame()

    tickers = [ticker for ticker, _exchange, _change in movers]
    changes = {ticker: change for ticker, _exchange, change in movers}
    result = scan_integrated_tickers(
        tickers,
        period=TOP10_ANALYSIS_PERIOD,
        interval="1d",
    )
    if result.empty:
        return result

    result["Change %"] = result["Ticker"].map(changes)
    result["Change %"] = result["Change %"].round(2)
    return result.sort_values(
        "Change %", key=lambda values: values.abs(), ascending=False
    ).reset_index(drop=True)
