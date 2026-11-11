"""Intraday opportunity screening for momentum and low-priced stocks.

The scanner ranks observable intraday conditions; it does not predict profits or
provide guaranteed trade signals. The All caps universe is built from the current dynamic NSE and BSE equity
lists. Provider coverage is reported separately; a listed symbol is not assumed
to have a usable intraday quote.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

import pandas as pd

from scanner.day_trading_strategy import (
    analyze_day_trade_setup,
    calculate_day_trade_plan,
    classify_day_trade_plan_state,
)
from scanner.dynamic_universe import (
    merge_bse_universe,
    merge_nse_universe,
    yahoo_symbol_for_bse_code,
)
from scanner.surveillance import (
    apply_safety_filter,
    fetch_nse_safety_snapshot,
    liquidity_warning,
)
from scanner.universe import bse_candidates_for_nse_symbols
from scanner.unusual_activity import CAP_UNIVERSES
from services.intraday_vwap_orb import vwap_orb_metrics
from services.resilient_market_data import download_symbol_frames

CHUNK_SIZE = 100
CHUNK_DOWNLOAD_ATTEMPTS = 3
CHUNK_RETRY_BACKOFF_SECONDS = (0.5, 1.0)


def _download_chunk_with_retry(
    tickers: list[str],
    interval: str,
) -> tuple[pd.DataFrame, int]:
    """Download one chunk through the shared cache and bounded provider controls.

    The shared service owns retries, concurrency limits, request timeouts and
    cache reuse. Reassemble its per-symbol frames into yfinance's familiar
    ticker-first MultiIndex shape for the existing analysis pipeline.
    """
    frames, _missing = download_symbol_frames(
        tickers,
        period="1d",
        interval=interval,
        auto_adjust=False,
        batch_size=max(1, len(tickers)),
        timeout=15,
        retries=CHUNK_DOWNLOAD_ATTEMPTS - 1,
        recover_missing=False,
    )
    if not frames:
        return pd.DataFrame(), CHUNK_DOWNLOAD_ATTEMPTS
    history = pd.concat(frames, axis=1).sort_index()
    return history, 1


def summarize_day_trading_setup(strategy: dict[str, Any]) -> dict[str, Any]:
    """Convert setup-engine conditions into concise scanner evidence."""
    long_score = strategy["Long setup score"]
    short_score = strategy["Short setup score"]
    direction = (
        "LONG" if long_score > short_score else "SHORT" if short_score > long_score else "NEUTRAL"
    )
    trend = strategy["Trend"]
    vwap_relation = strategy["VWAP relation"]
    ema_alignment = strategy["EMA 9/20"]
    rvol = strategy["RVOL"]
    breakout = strategy["Breakout"]
    breakdown = strategy["Breakdown"]

    evidence = []
    if trend != "MIXED":
        evidence.append(trend)
    if vwap_relation in {"ABOVE", "BELOW"}:
        evidence.append(f"VWAP {vwap_relation}")
    if ema_alignment in {"BULLISH", "BEARISH"}:
        evidence.append(f"EMA {ema_alignment}")
    if rvol >= 1.5:
        evidence.append("RVOL CONFIRMED")
    if breakout == "YES":
        evidence.append("BREAKOUT")
    if breakdown == "YES":
        evidence.append("BREAKDOWN")

    if direction == "LONG" and long_score >= 70:
        setup_state = "LONG SETUP WATCH"
    elif direction == "SHORT" and short_score >= 70:
        setup_state = "SHORT SETUP WATCH"
    else:
        setup_state = "CONTEXT ONLY"

    return {
        "Direction": direction,
        "Setup state": setup_state,
        "Evidence": " • ".join(evidence) if evidence else "No strong confirmation",
    }


def select_day_trader_universe(
    cap_category: str = "All caps",
    exchange_category: str = "Both",
) -> list[tuple[str, str]]:
    """Return the selected candidate universe, using live NSE/BSE lists for All caps."""
    if cap_category not in {"All caps", *CAP_UNIVERSES}:
        return []
    exchanges = ("NSE", "BSE") if exchange_category == "Both" else (exchange_category,)
    if cap_category == "All caps":
        # All caps means the complete current exchange equity lists, not a
        # curated large-cap shortlist. Keep exchange membership separate so
        # duplicate company listings on NSE and BSE remain independently scannable.
        universe = [(symbol, "NSE") for symbol in merge_nse_universe()]
        universe.extend((symbol, "BSE") for symbol in merge_bse_universe())
    else:
        # Named cap baskets are maintained research subsets. Users selecting
        # All caps receive the full dynamic exchange universe above.
        selected = CAP_UNIVERSES[cap_category]
        universe = [(symbol, "NSE") for symbol in merge_nse_universe() if symbol in selected]
        universe.extend((symbol, "BSE") for symbol in bse_candidates_for_nse_symbols(selected))
    filtered = [(symbol, venue) for symbol, venue in universe if venue in exchanges]
    return sorted(set(filtered), key=lambda item: (item[1], item[0]))


def _add_coverage_diagnostics(stats: dict[str, Any]) -> dict[str, Any]:
    """Add explicit universe-resolution and usable-data coverage metrics."""
    candidates = int(stats.get("candidate_count", 0) or 0)
    mapped = int(stats.get("mapped_symbol_count", 0) or 0)
    usable = int(stats.get("usable_data_count", 0) or 0)
    stats["no_usable_data_count"] = max(0, mapped - usable)
    stats["data_coverage_pct"] = round(100.0 * usable / candidates, 1) if candidates else 0.0
    stats["universe_resolution_pct"] = round(100.0 * mapped / candidates, 1) if candidates else 0.0
    stats["scan_completed"] = True
    return stats


def _finalize_exchange_diagnostics(
    exchange_diagnostics: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Return exchange diagnostics with stable rounded timing values."""
    return {
        exchange: {
            **metrics,
            "download_seconds": round(max(0.0, float(metrics.get("download_seconds", 0))), 3),
        }
        for exchange, metrics in exchange_diagnostics.items()
    }


def _set_scan_timing_diagnostics(
    scan_stats: dict[str, Any],
    *,
    total_seconds: float,
    download_seconds: float,
    analysis_seconds: float,
    safety_filter_seconds: float = 0.0,
) -> None:
    """Store rounded phase timings consistently in scanner diagnostics."""
    scan_stats["download_seconds"] = round(max(0.0, download_seconds), 3)
    scan_stats["analysis_seconds"] = round(max(0.0, analysis_seconds), 3)
    scan_stats["safety_filter_seconds"] = round(max(0.0, safety_filter_seconds), 3)
    scan_stats["scan_duration_seconds"] = round(max(0.0, total_seconds), 3)


def scan_has_provider_data(scan_stats: dict[str, Any]) -> bool:
    """Return whether at least one mapped-symbol download chunk returned data."""
    mapped = int(scan_stats.get("mapped_symbol_count", 0) or 0)
    nonempty = int(scan_stats.get("nonempty_chunks", 0) or 0)
    failed = int(scan_stats.get("download_failed_chunks", 0) or 0)
    return mapped == 0 or nonempty > 0 or failed == 0


def max_candle_age_minutes(exchange: str, interval: str) -> float:
    """Return a conservative source-specific freshness limit for intraday candles.

    Yahoo's BSE intraday coverage can be delayed relative to NSE. The larger
    BSE allowance avoids misclassifying that known provider delay as bad data.
    """
    if exchange == "BSE":
        return 25.0 if interval == "1m" else 30.0
    return 10.0 if interval == "1m" else 15.0


def candle_age_minutes(timestamp: object, now: object | None = None) -> float | None:
    """Calculate candle age in minutes, interpreting naive timestamps as IST."""
    try:
        candle_at = pd.Timestamp(timestamp)
        current_at = pd.Timestamp.now(tz="Asia/Kolkata") if now is None else pd.Timestamp(now)
        if candle_at.tzinfo is None:
            candle_at = candle_at.tz_localize("Asia/Kolkata")
        else:
            candle_at = candle_at.tz_convert("Asia/Kolkata")
        if current_at.tzinfo is None:
            current_at = current_at.tz_localize("Asia/Kolkata")
        else:
            current_at = current_at.tz_convert("Asia/Kolkata")
        return max(0.0, (current_at - candle_at).total_seconds() / 60.0)
    except (TypeError, ValueError, OverflowError):
        return None


def _completed_volume_bars(
    volume: pd.Series,
    interval: str,
    now: object | None = None,
) -> pd.Series:
    """Return only volume bars whose full interval has elapsed.

    Yahoo intraday indexes identify bar start times. The newest bar can still
    be accumulating volume, so it must not be compared with completed bars.
    """
    interval_minutes = {"1m": 1, "5m": 5}.get(interval)
    if interval_minutes is None or volume.empty:
        return volume.iloc[0:0]
    current_at = pd.Timestamp.now(tz="Asia/Kolkata") if now is None else pd.Timestamp(now)
    if current_at.tzinfo is None:
        current_at = current_at.tz_localize("Asia/Kolkata")
    else:
        current_at = current_at.tz_convert("Asia/Kolkata")
    bar_starts = pd.DatetimeIndex(pd.to_datetime(volume.index))
    if bar_starts.tz is None:
        bar_starts = bar_starts.tz_localize("Asia/Kolkata")
    else:
        bar_starts = bar_starts.tz_convert("Asia/Kolkata")
    completed = bar_starts + pd.Timedelta(minutes=interval_minutes) <= current_at
    return volume.loc[completed].dropna()


def _candle_settings(lookback_minutes: int) -> tuple[str, int]:
    """Use the smallest candle interval that supports the requested lookback."""
    if lookback_minutes in (2, 3):
        candle_minutes = 1
    else:
        candle_minutes = 5
    interval = f"{candle_minutes}m"
    bars = max(1, int(round(lookback_minutes / candle_minutes)))
    return interval, bars


def _ticker(symbol: str, exchange: str) -> str | None:
    """Resolve an exchange symbol to a Yahoo Finance ticker.

    BSE scrip codes must be mapped through the official BSE scrip_id field;
    appending .BO to a numeric code produces unreliable/unusable coverage.
    """
    cleaned = str(symbol).strip().upper()
    if exchange == "NSE":
        return cleaned if cleaned.endswith((".NS", ".BO")) else f"{cleaned}.NS"
    if exchange == "BSE":
        if cleaned.endswith((".NS", ".BO")):
            return cleaned
        mapped = yahoo_symbol_for_bse_code(cleaned)
        return f"{mapped}.BO" if mapped else None
    return None


def _frame(history: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Extract and validate one ticker's OHLCV frame from Yahoo batch data.

    yfinance can return MultiIndex columns with either ticker-first or
    price-field-first ordering. Resolve the ticker by inspecting every level
    rather than assuming a fixed column layout.
    """
    if history is None or history.empty:
        return pd.DataFrame()

    if isinstance(history.columns, pd.MultiIndex):
        data = pd.DataFrame()
        for level in range(history.columns.nlevels):
            if ticker not in history.columns.get_level_values(level):
                continue
            candidate = history.xs(ticker, axis=1, level=level).copy()
            if {"Open", "High", "Low", "Close", "Volume"}.issubset(candidate.columns):
                data = candidate
                break
        if data.empty:
            return pd.DataFrame()
    else:
        data = history.copy()

    required = ["Open", "High", "Low", "Close", "Volume"]
    if not set(required).issubset(data.columns):
        return pd.DataFrame()

    data = data.loc[:, required].apply(pd.to_numeric, errors="coerce")
    data = data.replace([float("inf"), float("-inf")], float("nan"))
    data = data.dropna(subset=required).sort_index()
    if data.empty:
        return data

    valid_prices = (data[["Open", "High", "Low", "Close"]] > 0).all(axis=1)
    valid_volume = data["Volume"] >= 0
    valid_ohlc = (data["High"] >= data[["Open", "Close", "Low"]].max(axis=1)) & (
        data["Low"] <= data[["Open", "Close", "High"]].min(axis=1)
    )
    data = data.loc[valid_prices & valid_volume & valid_ohlc]
    return data[~data.index.duplicated(keep="last")]


def score_opportunity_rows(rows: pd.DataFrame) -> pd.DataFrame:
    """Score observable momentum, volume, range, and breakout conditions."""
    if rows is None or rows.empty:
        return pd.DataFrame()

    result = rows.copy()
    change = result["5-min change %"]
    long_momentum = (change.clip(lower=0) / 2.0 * 35).clip(upper=35)
    short_momentum = ((-change).clip(lower=0) / 2.0 * 35).clip(upper=35)
    volume = ((result["Volume surge x"] - 1.0).clip(lower=0) / 2.0 * 30).clip(upper=30)
    volatility = (result["Session range %"].clip(lower=0) / 4.0 * 20).clip(upper=20)
    breakout = result["Breakout"].eq("YES").astype(float) * 15
    breakdown_column = "Strategy breakdown" if "Strategy breakdown" in result else "Breakdown"
    breakdown = (
        result.get(breakdown_column, pd.Series("NO", index=result.index)).eq("YES").astype(float)
        * 15
    )
    long_score = long_momentum + volume + volatility + breakout
    short_score = short_momentum + volume + volatility + breakdown
    result["Opportunity score"] = pd.concat([long_score, short_score], axis=1).max(axis=1).round(1)

    setup_score = result.get("Setup score", result["Opportunity score"])
    result["Composite score"] = (result["Opportunity score"] * 0.6 + setup_score * 0.4).round(1)
    inferred_direction = pd.Series("NEUTRAL", index=result.index)
    inferred_direction = inferred_direction.mask(change > 0, "LONG").mask(change < 0, "SHORT")
    direction = result.get("Direction", inferred_direction).fillna(inferred_direction)
    result["Setup"] = "Momentum watch"
    long_momentum = (direction.eq("LONG")) & (result["5-min change %"] >= 0.75)
    short_momentum = (direction.eq("SHORT")) & (result["5-min change %"] <= -0.75)
    volume_confirmed = result["Volume surge x"] >= 1.5
    result.loc[long_momentum & volume_confirmed, "Setup"] = "Bullish volume + momentum"
    result.loc[short_momentum & volume_confirmed, "Setup"] = "Bearish volume + momentum"
    result.loc[direction.eq("LONG") & result["Breakout"].eq("YES"), "Setup"] = "Breakout watch"
    breakdown_signal = result.get(
        "Strategy breakdown",
        result.get("Breakdown", pd.Series("NO", index=result.index)),
    )
    result.loc[
        direction.eq("SHORT") & breakdown_signal.eq("YES"),
        "Setup",
    ] = "Breakdown watch"
    result.loc[
        direction.eq("LONG") & result["Low-price flag"].eq("YES") & volume_confirmed,
        "Setup",
    ] = "Low-price bullish volume watch"
    result.loc[
        direction.eq("SHORT") & result["Low-price flag"].eq("YES") & volume_confirmed,
        "Setup",
    ] = "Low-price bearish volume watch"

    return result.sort_values(
        [
            "Composite score",
            "Opportunity score",
            "Volume surge x",
            "Symbol",
        ],
        ascending=[False, False, False, True],
        na_position="last",
    ).reset_index(drop=True)


def scan_day_trader_opportunities(
    limit: int = 20,
    exchange_category: str = "Both",
    cap_category: str = "All caps",
    max_price: float = 50.0,
    lookback_minutes: int = 5,
    min_change_percent: float = 0.5,
    min_volume_surge: float = 1.2,
    low_price_only: bool = False,
    exclude_flagged: bool = True,
) -> pd.DataFrame:
    """Find intraday momentum candidates, including configurable low-price mode.

    max_price is a configurable low-price threshold, not a formal definition
    of a penny stock. Prices and eligibility use the latest Yahoo Finance
    candle returned by the provider.
    """
    if (
        limit < 1
        or max_price <= 0
        or lookback_minutes not in (2, 3, 5)
        or min_change_percent < 0
        or min_volume_surge < 0
        or cap_category not in {"All caps", *CAP_UNIVERSES}
    ):
        return pd.DataFrame()

    scan_started = perf_counter()
    download_seconds = 0.0
    analysis_seconds = 0.0
    universe = select_day_trader_universe(cap_category, exchange_category)
    exchanges = ("NSE", "BSE") if exchange_category == "Both" else (exchange_category,)

    # Use 5-minute candles for the default 5-minute scan. This cuts the Yahoo
    # payload substantially while preserving the requested 5-minute signal.
    # The 2- and 3-minute modes retain 1-minute candles for finer timing.
    interval, bars = _candle_settings(lookback_minutes)
    candle_minutes = 1 if interval == "1m" else 5
    rows: list[dict[str, Any]] = []
    scan_stats: dict[str, Any] = {
        "candidate_count": len(universe),
        "attempted_count": len(universe),
        "mapped_symbol_count": 0,
        "usable_data_count": 0,
        "stale_candle_count": 0,
        "max_candle_age_minutes": 0.0,
        "strategy_count": 0,
        "download_failed_chunks": 0,
        "empty_chunks": 0,
        "nonempty_chunks": 0,
        "filtered_count": 0,
        "price_change_pass_count": 0,
        "volume_surge_pass_count": 0,
        "both_filters_pass_count": 0,
        "low_price_pass_count": 0,
        "matches_before_safety": 0,
        "matches_after_safety": 0,
        "interval": interval,
        "lookback_minutes": lookback_minutes,
        "exchange": exchange_category,
        "cap_category": cap_category,
        "exchange_diagnostics": {},
    }

    for exchange in exchanges:
        exchange_symbols = [symbol for symbol, venue in universe if venue == exchange]
        exchange_stats = {
            "candidate_count": len(exchange_symbols),
            "mapped_symbol_count": 0,
            "chunks_attempted": 0,
            "chunks_succeeded": 0,
            "chunks_failed": 0,
            "usable_data_count": 0,
            "stale_candle_count": 0,
            "download_seconds": 0.0,
        }
        scan_stats["exchange_diagnostics"][exchange] = exchange_stats
        resolved_tickers = [_ticker(symbol, exchange) for symbol in exchange_symbols]
        scan_stats["unmapped_symbol_count"] = scan_stats.get("unmapped_symbol_count", 0) + sum(
            ticker is None for ticker in resolved_tickers
        )
        tickers = [ticker for ticker in resolved_tickers if ticker is not None]
        exchange_stats["mapped_symbol_count"] = len(tickers)
        scan_stats["mapped_symbol_count"] += len(tickers)
        for start in range(0, len(tickers), CHUNK_SIZE):
            chunk = tickers[start : start + CHUNK_SIZE]
            scan_stats["downloaded_chunk_symbol_count"] = scan_stats.get(
                "downloaded_chunk_symbol_count", 0
            ) + len(chunk)
            download_started = perf_counter()
            history, download_attempts = _download_chunk_with_retry(chunk, interval)
            chunk_download_seconds = perf_counter() - download_started
            download_seconds += chunk_download_seconds
            exchange_stats["chunks_attempted"] += 1
            exchange_stats["download_seconds"] += chunk_download_seconds
            scan_stats["download_attempts"] = (
                scan_stats.get("download_attempts", 0) + download_attempts
            )
            if history.empty:
                exchange_stats["chunks_failed"] += 1
                scan_stats["download_failed_chunks"] += 1
                scan_stats["empty_chunks"] += 1
                continue

            exchange_stats["chunks_succeeded"] += 1
            scan_stats["nonempty_chunks"] += 1
            analysis_started = perf_counter()
            for ticker in chunk:
                try:
                    data = _frame(history, ticker)
                    if len(data) <= bars:
                        continue

                    latest_candle_at = data.index[-1]
                    candle_age = candle_age_minutes(latest_candle_at)
                    freshness_limit = max_candle_age_minutes(exchange, interval)
                    if candle_age is None or candle_age > freshness_limit:
                        scan_stats["stale_candle_count"] += 1
                        exchange_stats["stale_candle_count"] += 1
                        continue
                    scan_stats["max_candle_age_minutes"] = round(
                        max(scan_stats["max_candle_age_minutes"], candle_age), 2
                    )

                    session_date = latest_candle_at.date()
                    session = data.loc[[stamp.date() == session_date for stamp in data.index]]
                    close = pd.to_numeric(session["Close"], errors="coerce").dropna()
                    high = pd.to_numeric(session["High"], errors="coerce").dropna()
                    volume = pd.to_numeric(session["Volume"], errors="coerce").dropna()
                    if len(close) <= bars or len(volume) < 6:
                        continue

                    scan_stats["usable_data_count"] += 1
                    exchange_stats["usable_data_count"] += 1
                    price = float(close.iloc[-1])
                    prior = float(close.iloc[-1 - bars])
                    if price <= 0 or prior <= 0:
                        continue

                    change = (price / prior - 1.0) * 100.0
                    completed_volume = _completed_volume_bars(session["Volume"], interval)
                    if len(completed_volume) < 6:
                        continue
                    baseline = float(
                        completed_volume.iloc[-min(21, len(completed_volume) - 1) : -1].median()
                    )
                    latest_volume = float(completed_volume.iloc[-1])
                    volume_surge = latest_volume / baseline if baseline > 0 else 0.0

                    session_high = float(pd.to_numeric(session["High"], errors="coerce").max())
                    session_low = float(pd.to_numeric(session["Low"], errors="coerce").min())
                    session_range = (
                        (session_high - session_low) / price * 100.0 if price > 0 else 0.0
                    )

                    prior_highs = high.iloc[-21:-1] if len(high) >= 21 else high.iloc[:-1]
                    breakout = len(prior_highs) > 0 and price > float(prior_highs.max())
                    prior_lows = (
                        pd.to_numeric(session["Low"], errors="coerce").iloc[-21:-1]
                        if len(session) >= 21
                        else pd.to_numeric(session["Low"], errors="coerce").iloc[:-1]
                    )
                    breakdown = len(prior_lows) > 0 and price < float(prior_lows.min())

                    # Include meaningful downside moves as short candidates too.
                    price_pass = abs(change) >= min_change_percent
                    volume_pass = volume_surge >= min_volume_surge
                    if price_pass:
                        scan_stats["price_change_pass_count"] += 1
                    if change < 0 and price_pass:
                        scan_stats["downside_move_pass_count"] = (
                            scan_stats.get("downside_move_pass_count", 0) + 1
                        )
                    elif change > 0 and price_pass:
                        scan_stats["upside_move_pass_count"] = (
                            scan_stats.get("upside_move_pass_count", 0) + 1
                        )
                    if volume_pass:
                        scan_stats["volume_surge_pass_count"] += 1
                    if price_pass and volume_pass:
                        scan_stats["both_filters_pass_count"] += 1

                    low_price = price <= max_price
                    if low_price:
                        scan_stats["low_price_pass_count"] += 1

                    # Cheap first-stage filters: avoid expensive strategy/VWAP
                    # calculations for symbols that cannot enter the result set.
                    if not price_pass or not volume_pass:
                        continue
                    if low_price_only and not low_price:
                        continue

                    strategy = analyze_day_trade_setup(
                        session,
                        opening_range_bars=5 if candle_minutes == 1 else 1,
                        level_lookback=min(20, max(5, len(session) - 1)),
                    )
                    if not strategy:
                        continue

                    scan_stats["strategy_count"] += 1
                    vwap_orb = vwap_orb_metrics(session, orb_minutes=(5, 15))
                    strategy.update(vwap_orb)

                    setup_score = max(
                        strategy["Long setup score"],
                        strategy["Short setup score"],
                    )
                    strategy_name = strategy["Setup"]
                    trend = strategy["Trend"]
                    vwap_relation = strategy["VWAP relation"]
                    ema_alignment = strategy["EMA 9/20"]
                    strategy_rvol = strategy["RVOL"]
                    strategy_breakout = strategy["Breakout"]
                    strategy_breakdown = strategy["Breakdown"]
                    orb_high = strategy["ORB high"]
                    orb_low = strategy["ORB low"]
                    strategy_summary = summarize_day_trading_setup(strategy)
                    trade_plan = calculate_day_trade_plan(strategy)
                    plan_state = classify_day_trade_plan_state(strategy, trade_plan)
                    direction = strategy_summary["Direction"]
                    setup_state = strategy_summary["Setup state"]
                    evidence_text = strategy_summary["Evidence"]

                    low_price = price <= max_price
                    if low_price:
                        scan_stats["low_price_pass_count"] += 1

                    if not price_pass or not volume_pass:
                        continue
                    if low_price_only and not low_price:
                        continue

                    rows.append(
                        {
                            "Symbol": ticker.rsplit(".", 1)[0],
                            "Exchange": exchange,
                            "Market-cap basket": cap_category,
                            "Price": round(price, 2),
                            "5-min change %": round(change, 2),
                            "Volume surge x": round(volume_surge, 2),
                            "Session range %": round(session_range, 2),
                            "Breakout": "YES" if breakout else "—",
                            "Breakdown": "YES" if breakdown else "—",
                            "Day-trading setup": strategy_name,
                            "Direction": direction,
                            "Setup state": setup_state,
                            "Evidence": evidence_text,
                            "Plan": trade_plan["Plan"],
                            "Plan state": plan_state,
                            "Entry reference": trade_plan["Entry reference"],
                            "Stop reference": trade_plan["Stop reference"],
                            "Target 1": trade_plan["Target 1"],
                            "Target 2": trade_plan["Target 2"],
                            "Target 3": trade_plan["Target 3"],
                            "Risk per share": trade_plan["Risk per share"],
                            "R:R T1": trade_plan["R:R T1"],
                            "R:R T2": trade_plan["R:R T2"],
                            "R:R T3": trade_plan["R:R T3"],
                            "Setup score": setup_score,
                            "Trend": trend,
                            "VWAP": vwap_relation,
                            "VWAP price": vwap_orb.get("VWAP"),
                            "VWAP distance %": vwap_orb.get("VWAP distance %"),
                            "VWAP bias": vwap_orb.get("VWAP bias"),
                            "ORB 5m high": vwap_orb.get("ORB 5m high"),
                            "ORB 5m low": vwap_orb.get("ORB 5m low"),
                            "ORB 5m state": vwap_orb.get("ORB 5m state"),
                            "ORB 15m high": vwap_orb.get("ORB 15m high"),
                            "ORB 15m low": vwap_orb.get("ORB 15m low"),
                            "ORB 15m state": vwap_orb.get("ORB 15m state"),
                            "EMA 9/20": ema_alignment,
                            "RVOL": strategy_rvol,
                            "ORB high": orb_high,
                            "ORB low": orb_low,
                            "Strategy breakout": strategy_breakout,
                            "Strategy breakdown": strategy_breakdown,
                            "Low-price flag": "YES" if low_price else "—",
                            "Latest candle": str(latest_candle_at),
                            "Candle age (min)": round(candle_age, 2),
                            "Freshness limit (min)": freshness_limit,
                            "Data delay": (
                                "Up to 15 min provider delay"
                                if exchange == "BSE"
                                else "Provider timestamp"
                            ),
                            "Liquidity": liquidity_warning(price, latest_volume),
                        }
                    )
                except (KeyError, TypeError, ValueError, IndexError):
                    continue
            analysis_seconds += perf_counter() - analysis_started

    scan_stats["exchange_diagnostics"] = _finalize_exchange_diagnostics(
        scan_stats["exchange_diagnostics"]
    )

    _set_scan_timing_diagnostics(
        scan_stats,
        total_seconds=perf_counter() - scan_started,
        download_seconds=download_seconds,
        analysis_seconds=analysis_seconds,
    )
    scan_stats["unmapped_symbol_count"] = scan_stats.get("unmapped_symbol_count", 0)
    _add_coverage_diagnostics(scan_stats)

    if not rows:
        empty = pd.DataFrame()
        empty.attrs["scan_stats"] = scan_stats
        return empty

    result = pd.DataFrame(rows)
    scan_stats["matches_before_safety"] = len(result)
    result = score_opportunity_rows(result)
    result["Screen"] = result["Low-price flag"].map(
        {"YES": f"Low-price <= ₹{max_price:g}", "—": "Momentum"}
    )

    nse_symbols = result.loc[result["Exchange"].eq("NSE"), "Symbol"].tolist()
    safety_started = perf_counter()
    safety, _ = fetch_nse_safety_snapshot(nse_symbols)
    result = apply_safety_filter(result, safety, exclude_flagged=exclude_flagged)
    _set_scan_timing_diagnostics(
        scan_stats,
        total_seconds=perf_counter() - scan_started,
        download_seconds=download_seconds,
        analysis_seconds=analysis_seconds,
        safety_filter_seconds=perf_counter() - safety_started,
    )
    scan_stats["matches_after_safety"] = len(result)
    scan_stats["filtered_count"] = max(
        0,
        scan_stats["usable_data_count"] - scan_stats["matches_before_safety"],
    )
    result = result.head(max(1, min(int(limit), 100))).reset_index(drop=True)
    scan_stats["displayed_count"] = len(result)
    result.attrs["scan_stats"] = scan_stats
    return result
