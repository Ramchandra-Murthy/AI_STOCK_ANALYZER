"""Top-10 market mover scanner with Chapter 4-10 workflow signals."""

from __future__ import annotations

import pandas as pd

from engine.live_integrated_scanner import scan_integrated_tickers
from scanner.dynamic_universe import merge_bse_universe, merge_nse_universe
from scanner.market_scanner import _batch_change_screen


def scan_top10_integrated(
    *,
    period: str = "6mo",
    interval: str = "1d",
) -> pd.DataFrame:
    """Return the ten largest liquid NSE/BSE daily movers with workflow signals."""
    candidates = {"NSE": merge_nse_universe(), "BSE": merge_bse_universe()}
    movers = _batch_change_screen(candidates)[:10]
    if not movers:
        return pd.DataFrame()

    tickers = [ticker for ticker, _exchange, _change in movers]
    changes = {ticker: change for ticker, _exchange, change in movers}
    result = scan_integrated_tickers(tickers, period=period, interval=interval)
    if result.empty:
        return result

    result["Change %"] = result["Ticker"].map(changes)
    result["Change %"] = result["Change %"].round(2)
    return result.sort_values(
        "Change %", key=lambda values: values.abs(), ascending=False
    ).reset_index(drop=True)
