from __future__ import annotations

from typing import Any

import pandas as pd
import yfinance as yf

from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES
from scanner.unusual_activity import CAP_UNIVERSES, _frame_for, _ticker


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
    current = clean.loc[[stamp.date() == session_date for stamp in clean.index]]
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
    """Return stocks meeting the selected intraday price-jump threshold."""
    rows: list[dict[str, Any]] = []
    exchanges = ("NSE", "BSE") if exchange_category == "Both" else (exchange_category,)
    if cap_category == "All caps":
        universe = [(symbol, "NSE") for symbol in NSE_CANDIDATES] + [
            (symbol, "BSE") for symbol in BSE_CANDIDATES
        ]
    else:
        selected = CAP_UNIVERSES.get(cap_category, set())
        universe = [(symbol, "NSE") for symbol in NSE_CANDIDATES if symbol in selected]

    selected_universe = [(symbol, venue) for symbol, venue in universe if venue in exchanges]
    stats = {
        "candidate_count": len(selected_universe),
        "attempted_count": 0,
        "usable_count": 0,
        "download_failed_chunks": 0,
        "empty_chunks": 0,
        "processing_errors": 0,
        "matches_before_limit": 0,
        "displayed_count": 0,
    }

    # Yahoo has no native 2- or 3-minute interval. Compare 1-minute candles
    # for those windows and 5-minute candles for longer windows.
    candle_minutes = 1 if lookback_minutes in (2, 3) else 5
    interval = f"{candle_minutes}m"
    bars = max(1, int(round(lookback_minutes / candle_minutes)))

    for exchange in exchanges:
        tickers = [
            _ticker(symbol, exchange) for symbol, venue in selected_universe if venue == exchange
        ]
        for start in range(0, len(tickers), 10):
            chunk = tickers[start : start + 10]
            stats["attempted_count"] += len(chunk)
            try:
                history = yf.download(
                    tickers=chunk,
                    period="5d",
                    interval=interval,
                    progress=False,
                    auto_adjust=False,
                    group_by="ticker",
                    threads=False,
                )
                daily_history = yf.download(
                    tickers=chunk,
                    period="5d",
                    interval="1d",
                    progress=False,
                    auto_adjust=False,
                    group_by="ticker",
                    threads=False,
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

                    session_date = frame.index[-1].date()
                    current = frame.loc[[stamp.date() == session_date for stamp in frame.index]]
                    if len(current) <= bars:
                        continue
                    price = float(current.iloc[-1]["Close"])
                    prior_intraday = float(current.iloc[-1 - bars]["Close"])
                    intraday_pct = (
                        (price / prior_intraday - 1) * 100 if prior_intraday > 0 else None
                    )

                    baseline = float(current["Volume"].iloc[-min(13, len(current) - 1) : -1].mean())
                    volume = float(current.iloc[-1]["Volume"])
                    relative_volume = volume / baseline if baseline > 0 else float("nan")
                    reasons = []
                    if qualifies_daily:
                        reasons.append("Daily gain")
                    if qualifies_intraday:
                        reasons.append(f"{lookback_minutes}-min jump")
                    rows.append(
                        {
                            "Symbol": ticker.rsplit(".", 1)[0],
                            "Exchange": exchange,
                            "Market-cap basket": cap_category,
                            "Last price": round(price, 2),
                            f"Change over {lookback_minutes} min %": round(intraday_pct, 2),
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
                ["Today change %", f"Change over {lookback_minutes} min %"],
                ascending=[False, False],
                na_position="last",
            )
            .head(max(1, min(int(limit), 100)))
            .reset_index(drop=True)
        )
    stats["displayed_count"] = len(result)
    result.attrs["scan_stats"] = stats
    return result
