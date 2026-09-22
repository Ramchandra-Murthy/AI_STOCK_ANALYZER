from __future__ import annotations

import io
import re
import time
from urllib.request import Request, urlopen

import pandas as pd

from scanner.universe import NSE_CANDIDATES

NSE_EQUITY_LIST_URL = "https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv"
CACHE_TTL_SECONDS = 15 * 60
MIN_PRICE = 20.0
MIN_AVG_DAILY_TURNOVER = 2.0e7
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9&.-]+$")

_cached_nse_symbols: tuple[float, list[str]] | None = None


def _download_nse_equity_list() -> list[str]:
    request = Request(
        NSE_EQUITY_LIST_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; AI_STOCK_ANALYZER/1.0)",
            "Accept": "text/csv,*/*",
        },
    )
    with urlopen(request, timeout=15) as response:
        payload = response.read()

    frame = pd.read_csv(io.BytesIO(payload))
    if "SYMBOL" not in frame.columns:
        raise ValueError("NSE equity list does not contain SYMBOL")

    symbols = frame["SYMBOL"].astype(str).str.strip().str.upper()
    if "SERIES" in frame.columns:
        symbols = symbols[frame["SERIES"].astype(str).str.strip().eq("EQ")]

    result = sorted(
        {
            symbol
            for symbol in symbols
            if symbol
            and symbol != "nan"
            and SYMBOL_PATTERN.fullmatch(symbol)
        }
    )
    return result


def dynamic_nse_symbols() -> list[str]:
    """Return the current NSE equity universe, falling back to the curated list."""
    global _cached_nse_symbols

    now = time.time()
    if _cached_nse_symbols and now - _cached_nse_symbols[0] < CACHE_TTL_SECONDS:
        return _cached_nse_symbols[1]

    try:
        symbols = _download_nse_equity_list()
        if symbols:
            _cached_nse_symbols = (now, symbols)
            return symbols
    except Exception:
        pass

    return list(NSE_CANDIDATES)


def merge_nse_universe(extra_symbols: list[str] | None = None) -> list[str]:
    """Merge the live NSE list with curated symbols so known names are never lost."""
    symbols = set(dynamic_nse_symbols())
    symbols.update(NSE_CANDIDATES)
    if extra_symbols:
        symbols.update(symbol.strip().upper() for symbol in extra_symbols if symbol.strip())
    return sorted(symbols)


def passes_liquidity_filter(
    latest_price: float,
    average_volume: float,
) -> bool:
    """Keep reasonably liquid stocks suitable for an intraday opportunity scan."""
    return (
        latest_price >= MIN_PRICE
        and latest_price * average_volume >= MIN_AVG_DAILY_TURNOVER
    )
