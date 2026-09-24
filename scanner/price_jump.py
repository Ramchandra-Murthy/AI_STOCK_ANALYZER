from __future__ import annotations

from typing import Any

import pandas as pd
import yfinance as yf

from scanner.dynamic_universe import merge_bse_universe, merge_nse_universe
from scanner.universe import NSE_CANDIDATES
from scanner.unusual_activity import CAP_UNIVERSES, _frame_for, _ticker

CHUNK_SIZE = 25
INTRADAY_PERIOD = "1d"


def calculate_price_jump(
    frame: pd.DataFrame,
    lookback_bars: int = 1,
    jump_percent: float = 1.0,
) -> dict[str, float | None] | None:
    """Calculate the latest same-session price jump and relative volume."""
    if frame is None or frame.empty or lookback_bars < 1:
        return None
    required = {"Close", "Volume"}
    if not required.issubset(frame.columns):
        return None

    clean = frame.dropna(subset=list(required)).sort_index()
    clean = clean[~clean.index.duplicated(keep="last")]
    if clean.empty:
        return None

    session_date = clean.index[-1].date()
    session_mask = clean.index.date == session_date
    current = clean.loc[session_mask]
    if len(current) <= lookback_bars:
        return None

    price = float(current.iloc[-1]["Close"])
    prior_price = float(current.iloc[-1 - lookback_bars]["Close"])
    if price <= 0 or prior_price <= 0:
        return None

    intraday_pct = (price / prior_price - 1.0) * 100.0
    baseline = float(current["Volume"].iloc[-min(13, len(current) - 1) : -1].mean())
    volume = float(current.iloc[-1]["Volume"])
    relative_volume = volume / baseline if baseline > 0 else float("nan")
    return {
        "price": price,
        "intraday_pct": intraday_pct,
        "volume": volume,
        "relative_volume": relative_volume,
        "qualifies": float(intraday_pct >= jump_percent),
    }


def scan_price_jumps(
    limit: int = 20,
    cap_category: str = "All caps",
    exchange_category: str = "Both",
    lookback_minutes: int = 5,
    jump_percent: float = 1.0,
) -> pd.DataFrame:
    """Return stocks meeting the selected intraday price-jump threshold.

    The broad candidate universe is rescanned on every run, so the returned
    symbols can change as current market conditions change. Yahoo Finance
    uses 1-minute candles for 2- and 3-minute lookbacks and 5-minute candles
    for 5-minute and longer lookbacks.
    """
    if lookback_minutes < 1 or jump_percent < 0:
        return pd.DataFrame()

    rows: list[dict[str, Any]] = []
    exchanges = ("NSE", "BSE") if exchange_category == "Both" else (exchange_category,)

    if cap_category == "All caps":
        universe = [(symbol, "NSE") for symbol in merge_nse_universe()] + [
            (symbol, "BSE") for symbol in merge_bse_universe()
        ]
    else:
        selected = CAP_UNIVERSES.get(cap_category, set())
        universe = [(symbol, "NSE") for symbol in NSE_CANDIDATES if symbol in selected]

    selected_universe = [(symbol, venue) for symbol, venue in universe if venue in exchanges]
    unique_universe = list(dict.fromkeys(selected_universe))
    duplicate_count = len(selected_universe) - len(unique_universe)
    selected_universe = unique_universe
    stats = {
        "candidate_count": len(selected_universe),
        "duplicate_candidates_removed": duplicate_count,
        "attempted_count": 0,
        "usable_count": 0,
        "download_failed_chunks": 0,
        "empty_chunks": 0,
        "processing_errors": 0,
        "matches_before_limit": 0,
        "displayed_count": 0,
        "interval": "1m" if lookback_minutes in (2, 3) else "5m",
    }

    candle_minutes = 1 if lookback_minutes in (2, 3) else 5
    interval = f"{candle_minutes}m"
    bars = max(1, int(round(lookback_minutes / candle_minutes)))

    for exchange in exchanges:
        tickers = [
            _ticker(symbol, exchange) for symbol, venue in selected_universe if venue == exchange
        ]
        for start in range(0, len(tickers), CHUNK_SIZE):
            chunk = tickers[start : start + CHUNK_SIZE]
            stats["attempted_count"] += len(chunk)
            try:
                history = yf.download(
                    tickers=chunk,
                    period=INTRADAY_PERIOD,
                    interval=interval,
                    progress=False,
                    auto_adjust=False,
                    group_by="ticker",
                    threads=False,
                    timeout=15,
                )
            except Exception:
                stats["download_failed_chunks"] += 1
                continue

            if history is None or history.empty:
                stats["empty_chunks"] += 1
                continue

            for ticker in chunk:
                try:
                    frame = _frame_for(history, ticker)
                    metrics = calculate_price_jump(frame, bars, jump_percent)
                    if metrics is None:
                        continue
                    stats["usable_count"] += 1
                    if not bool(metrics["qualifies"]):
                        continue

                    rows.append(
                        {
                            "Symbol": ticker.rsplit(".", 1)[0],
                            "Exchange": exchange,
                            "Market-cap basket": cap_category,
                            "Last price": round(float(metrics["price"]), 2),
                            f"Change over {lookback_minutes} min %": round(
                                float(metrics["intraday_pct"]), 2
                            ),
                            "Latest bar volume": int(metrics["volume"]),
                            "Volume vs recent bars": (
                                round(float(metrics["relative_volume"]), 2)
                                if pd.notna(metrics["relative_volume"])
                                else None
                            ),
                            "Latest candle (provider time)": str(frame.index[-1]),
                        }
                    )
                except (KeyError, TypeError, ValueError, IndexError):
                    stats["processing_errors"] += 1
                    continue

    stats["matches_before_limit"] = len(rows)
    if not rows:
        result = pd.DataFrame()
    else:
        result = (
            pd.DataFrame(rows)
            .sort_values(
                [
                    f"Change over {lookback_minutes} min %",
                    "Volume vs recent bars",
                ],
                ascending=[False, False],
                na_position="last",
            )
            .head(max(1, min(int(limit), 100)))
            .reset_index(drop=True)
        )

    stats["displayed_count"] = len(result)
    result.attrs["scan_stats"] = stats
    return result
