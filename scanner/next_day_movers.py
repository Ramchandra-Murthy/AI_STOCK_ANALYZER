"""Next-business-day upside candidate scanner for NSE/BSE equities (research only).

The scanner ranks liquid stocks by a transparent, fixed-weight *ranking score* built
from information available at the close of the last completed regular session (the
"prediction cutoff"). The score orders candidates against each other; it is **not** a
probability, is not calibrated, and is not a buy/sell recommendation. Nothing here
places orders.

Design notes
------------
* The trading calendar comes from ``services.market_calendar``. Unconfigured calendar
  years fail closed instead of guessing a target date.
* Market data comes from ``services.resilient_market_data`` (Yahoo Finance daily bars).
  That feed is delayed, can be revised and has gaps. Provider failures and stale or
  invalid symbols are reported and excluded; stale data is never substituted.
* Features are computed by :func:`compute_feature_frame`, which only uses rolling or
  exponentially weighted windows that look backwards. The walk-forward evaluation in
  ``scanner.next_day_movers_eval`` reuses the very same function so the live scanner
  and the backtest cannot drift apart.
* Delivery data, verified news and corporate-action feeds are not available in this
  repository, so they are not scored and are listed as unavailable on every result.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

import numpy as np
import pandas as pd

from indicators.atr import calculate_atr
from indicators.macd import calculate_macd
from indicators.moving_average import calculate_sma
from indicators.rsi import calculate_rsi
from scanner.dynamic_universe import (
    MIN_AVG_DAILY_TURNOVER,
    MIN_PRICE,
    SYMBOL_PATTERN,
    yahoo_symbol_for_bse_code,
)
from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES
from services.market_calendar import (
    IST,
    REGULAR_SESSION_CLOSE,
    CalendarUnavailableError,
    is_equity_trading_day,
    next_equity_trading_day,
    previous_equity_trading_day,
)
from services.sector_mapping import sector_for_symbol

logger = logging.getLogger(__name__)

SUPPORTED_EXCHANGES = ("NSE", "BSE")
REQUIRED_COLUMNS = ("Open", "High", "Low", "Close", "Volume")
SCORE_TYPE = "ranking_score_0_100_not_a_probability"
DATA_SOURCE = (
    "Yahoo Finance daily OHLCV via services.resilient_market_data "
    "(auto-adjusted, delayed, not an exchange feed)"
)
DISCLAIMER = (
    "Research and paper-trading use only. Scores rank candidates against each other and are "
    "NOT probabilities; next-session moves are highly uncertain and this is not investment "
    "advice or a buy/sell recommendation."
)
UNSUPPORTED_DATA = (
    "Delivery percentage: no verified source in this repository (not scored)",
    "News and corporate-action events: no verified source in this repository (not scored)",
    "Sector index series: unavailable; sector strength uses same-sector peers in the scanned "
    "universe only",
)
BENCHMARK_NAMES = {"NSE": "NIFTY 50", "BSE": "SENSEX"}
SUFFIX_EXCHANGE = {".NS": "NSE", ".BO": "BSE"}
# Tolerance for OHLC internal-consistency checks (relative).
OHLC_TOLERANCE = 1e-3
COVERAGE_EPSILON = 1e-9
INVALID_WINDOW_ROWS = 60
MIN_SECTOR_PEERS = 3

# Fixed a-priori weights (sum to 1.0). They are NOT fitted to data.
FACTOR_WEIGHTS: dict[str, float] = {
    "ret_1d": 0.05,
    "ret_5d": 0.10,
    "ret_20d": 0.15,
    "clv": 0.07,
    "breakout_proximity": 0.08,
    "up_volume_surge": 0.07,
    "up_turnover_surge": 0.08,
    "above_sma20": 0.05,
    "sma20_over_sma50": 0.05,
    "rsi_balance": 0.05,
    "macd_hist_norm": 0.05,
    "rs_market_5d": 0.06,
    "rs_market_20d": 0.06,
    "rs_sector_5d": 0.08,
}
VOLATILITY_PENALTY_MAX = 15.0
GAP_RISK_PENALTY_MAX = 10.0
OVEREXTENSION_PENALTY = 5.0

# factor -> (label, display column, display format)
FACTOR_DISPLAY: dict[str, tuple[str, str, str]] = {
    "ret_1d": ("1-day return", "ret_1d", "pct"),
    "ret_5d": ("5-day return", "ret_5d", "pct"),
    "ret_20d": ("20-day return", "ret_20d", "pct"),
    "clv": ("Close location in day range", "clv", "ratio"),
    "breakout_proximity": ("Close vs prior 20-day high", "breakout_proximity", "pct"),
    "up_volume_surge": ("Up-day volume surge", "vol_ratio", "mult"),
    "up_turnover_surge": ("Up-day turnover surge", "turnover_ratio", "mult"),
    "above_sma20": ("Close vs 20-day SMA", "above_sma20", "pct"),
    "sma20_over_sma50": ("20-day vs 50-day SMA", "sma20_over_sma50", "pct"),
    "rsi_balance": ("RSI(14) near 60", "rsi14", "ratio"),
    "macd_hist_norm": ("MACD histogram / close", "macd_hist_norm", "pct"),
    "rs_market_5d": ("5-day return vs index", "rs_market_5d", "pct"),
    "rs_market_20d": ("20-day return vs index", "rs_market_20d", "pct"),
    "rs_sector_5d": ("5-day return vs sector peers", "rs_sector_5d", "pct"),
}

FrameFetcher = Callable[[list[str]], tuple[dict[str, pd.DataFrame], Mapping[str, Any]]]
SafetyFetcher = Callable[[list[str], date | None], tuple[pd.DataFrame, str | None]]


@dataclass(frozen=True)
class ScannerConfig:
    """Tunable thresholds. Defaults reuse the repository's liquidity constants."""

    exchanges: tuple[str, ...] = SUPPORTED_EXCHANGES
    top_n: int = 20
    min_price: float = MIN_PRICE
    min_median_turnover: float = MIN_AVG_DAILY_TURNOVER
    min_history: int = 70
    min_cross_section: int = 10
    min_factor_coverage: float = 0.8
    min_universe_coverage: float = 0.7
    max_abs_daily_move: float = 0.35
    max_zero_volume_days_10: int = 2
    max_gap_days: int = 7
    overbought_rsi: float = 80.0
    extended_move: float = 0.08
    close_buffer_minutes: int = 15
    prefer_nse_for_cross_listed: bool = True
    check_surveillance: bool = True
    exclude_surveillance_flagged: bool = True
    history_period: str = "1y"

    def __post_init__(self) -> None:
        if not self.exchanges or any(e not in SUPPORTED_EXCHANGES for e in self.exchanges):
            raise ValueError("exchanges must be a non-empty subset of NSE and BSE")
        if self.top_n < 1:
            raise ValueError("top_n must be at least 1")
        if self.min_cross_section < 2:
            raise ValueError("min_cross_section must be at least 2")
        for name in ("min_price", "min_median_turnover", "max_abs_daily_move"):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a positive finite number")
        for name in ("min_factor_coverage", "min_universe_coverage"):
            if not 0.0 < getattr(self, name) <= 1.0:
                raise ValueError(f"{name} must be in (0, 1]")


@dataclass(frozen=True)
class Instrument:
    """A listed equity. BSE symbols are six-digit scrip codes (repository convention)."""

    symbol: str
    exchange: str


@dataclass(frozen=True)
class ExclusionRecord:
    """A symbol that was removed from the ranking, with every reason found."""

    symbol: str
    exchange: str
    ticker: str | None
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class Candidate:
    """One ranked shortlist row. ``score`` is an ordering score, not a probability."""

    rank: int
    symbol: str
    exchange: str
    ticker: str
    score: float
    positive_score: float
    penalty: float
    factor_coverage: float
    supporting_factors: tuple[str, ...]
    risk_flags: tuple[str, ...]
    last_close: float
    data_timestamp: date
    data_source: str
    prediction_cutoff: datetime
    target_business_date: date
    score_type: str = SCORE_TYPE


@dataclass(frozen=True)
class ScanResult:
    """Scanner output. ``status`` is OK, DEGRADED or UNAVAILABLE (no ranking produced)."""

    status: str
    candidates: tuple[Candidate, ...]
    excluded: tuple[ExclusionRecord, ...]
    prediction_cutoff: datetime | None
    target_business_date: date | None
    generated_at: datetime
    data_quality: dict[str, Any]
    unavailable_data: tuple[str, ...]
    warnings: tuple[str, ...]
    disclaimer: str = DISCLAIMER
    score_type: str = SCORE_TYPE
    errors: tuple[str, ...] = field(default_factory=tuple)

    def to_frame(self) -> pd.DataFrame:
        """Return the shortlist as a display-ready DataFrame (empty if unavailable)."""
        rows = [
            {
                "Rank": c.rank,
                "Symbol": c.symbol,
                "Exchange": c.exchange,
                "Ticker": c.ticker,
                "Score (0-100, not a probability)": c.score,
                "Positive score": c.positive_score,
                "Penalty": c.penalty,
                "Factor coverage": c.factor_coverage,
                "Supporting factors": " | ".join(c.supporting_factors),
                "Risk flags": ", ".join(c.risk_flags),
                "Last close": c.last_close,
                "Data timestamp": c.data_timestamp.isoformat(),
                "Data source": c.data_source,
                "Prediction cutoff": c.prediction_cutoff.isoformat(),
                "Target business date": c.target_business_date.isoformat(),
            }
            for c in self.candidates
        ]
        return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Calendar: prediction cutoff and target date
# ---------------------------------------------------------------------------


def resolve_prediction_cutoff(
    now: datetime, config: ScannerConfig | None = None
) -> tuple[date, date]:
    """Return ``(cutoff_session, target_session)`` for a run at ``now``.

    The cutoff session is the latest regular session whose close (plus a data-settling
    buffer) has passed; the target is the next regular trading day after it. A run on a
    weekend, holiday or before the buffered close therefore uses the previous session.
    Raises CalendarUnavailableError when the configured calendar cannot answer.
    """
    cfg = config or ScannerConfig()
    current = now.replace(tzinfo=IST) if now.tzinfo is None else now.astimezone(IST)
    ready_at = (
        datetime.combine(current.date(), REGULAR_SESSION_CLOSE)
        + timedelta(minutes=cfg.close_buffer_minutes)
    ).time()
    today = current.date()
    if is_equity_trading_day(today) and current.time() >= ready_at:
        cutoff = today
    else:
        cutoff = previous_equity_trading_day(today)
    return cutoff, next_equity_trading_day(cutoff)


def cutoff_timestamp(cutoff_session: date) -> datetime:
    """Information cutoff: the regular-session close on the cutoff session (IST)."""
    return datetime.combine(cutoff_session, REGULAR_SESSION_CLOSE, IST)


# ---------------------------------------------------------------------------
# Universe handling
# ---------------------------------------------------------------------------


def _bse_company_key(code: str) -> str | None:
    """Return the paired NSE symbol for a curated BSE code (used to spot cross-listings)."""
    return dict(zip(BSE_CANDIDATES, NSE_CANDIDATES, strict=True)).get(code)


def build_universe(
    entries: Iterable[Instrument | tuple[str, str]] | None = None,
    config: ScannerConfig | None = None,
) -> tuple[list[Instrument], list[ExclusionRecord]]:
    """Normalise, validate and de-duplicate a universe.

    Default is the repository's curated NSE/BSE lists. Rejected entries are returned
    with a reason rather than dropped silently.
    """
    cfg = config or ScannerConfig()
    if entries is None:
        entries = [Instrument(s, "NSE") for s in NSE_CANDIDATES] + [
            Instrument(c, "BSE") for c in BSE_CANDIDATES
        ]

    accepted: list[Instrument] = []
    excluded: list[ExclusionRecord] = []
    seen: set[tuple[str, str]] = set()

    for entry in entries:
        raw_symbol, raw_exchange = (
            (entry.symbol, entry.exchange) if isinstance(entry, Instrument) else entry
        )
        symbol = str(raw_symbol).strip().upper()
        exchange = str(raw_exchange).strip().upper()

        def reject(reason: str, _symbol: str = symbol, _exchange: str = exchange) -> None:
            excluded.append(ExclusionRecord(_symbol, _exchange, None, (reason,)))

        if exchange not in SUPPORTED_EXCHANGES:
            reject("unsupported_exchange")
            continue
        implied_exchange = SUFFIX_EXCHANGE.get(symbol[-3:])
        if implied_exchange is not None:
            if implied_exchange != exchange:
                reject("exchange_suffix_mismatch")
                continue
            symbol = symbol[:-3]
        if not SYMBOL_PATTERN.fullmatch(symbol):
            reject("invalid_symbol")
            continue
        if exchange == "BSE" and not (symbol.isdigit() and len(symbol) == 6):
            reject("invalid_bse_scrip_code")
            continue
        if exchange not in cfg.exchanges:
            continue
        if (exchange, symbol) in seen:
            excluded.append(ExclusionRecord(symbol, exchange, None, ("duplicate_symbol",)))
            continue
        seen.add((exchange, symbol))
        accepted.append(Instrument(symbol, exchange))

    if cfg.prefer_nse_for_cross_listed:
        nse_symbols = {i.symbol for i in accepted if i.exchange == "NSE"}
        kept: list[Instrument] = []
        for inst in accepted:
            key = _bse_company_key(inst.symbol) if inst.exchange == "BSE" else None
            if key is not None and key in nse_symbols:
                excluded.append(
                    ExclusionRecord(
                        inst.symbol, inst.exchange, None, ("cross_listed_duplicate_of_nse",)
                    )
                )
            else:
                kept.append(inst)
        accepted = kept
    return accepted, excluded


def ticker_for(instrument: Instrument) -> str | None:
    """Return the Yahoo Finance ticker using the repository's exchange conventions."""
    from services.market_service import normalize_market_symbol  # lazy: pulls in yfinance

    if instrument.exchange == "NSE":
        return normalize_market_symbol(instrument.symbol, "NSE")
    mapped = yahoo_symbol_for_bse_code(instrument.symbol)
    return normalize_market_symbol(mapped, "BSE") if mapped else None


def benchmark_tickers(exchanges: Iterable[str]) -> dict[str, str]:
    """Return ``{exchange: index ticker}`` using the repository's index definitions."""
    from services.market_service import MARKET_INDICES  # lazy: pulls in yfinance

    return {ex: MARKET_INDICES[BENCHMARK_NAMES[ex]] for ex in exchanges}


def sector_of(instrument: Instrument) -> str:
    """Broad sector label from the repository mapping; ``Unclassified`` when unknown."""
    symbol = instrument.symbol
    if instrument.exchange == "BSE":
        symbol = _bse_company_key(symbol) or symbol
    return sector_for_symbol(symbol)


# ---------------------------------------------------------------------------
# Data hygiene
# ---------------------------------------------------------------------------


def _normalise_index(index: pd.Index) -> pd.DatetimeIndex:
    stamps = pd.DatetimeIndex(pd.to_datetime(index, errors="coerce"))
    if stamps.tz is not None:
        stamps = stamps.tz_convert(IST).tz_localize(None)
    return stamps.normalize()


def clean_ohlcv(
    frame: pd.DataFrame | None, cutoff: date | None = None
) -> tuple[pd.DataFrame | None, list[str]]:
    """Return a validated daily OHLCV frame and any reasons it is unreliable.

    Bars dated after ``cutoff`` are dropped so a partially formed session can never
    leak into the features. Rows with non-positive or inconsistent prices, negative
    or missing volume and duplicate dates are removed; if too many recent rows were
    invalid the whole record is rejected.
    """
    if frame is None or frame.empty:
        return None, ["no_data"]
    missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    if missing:
        return None, [f"missing_columns:{','.join(missing)}"]

    data = frame.loc[:, list(REQUIRED_COLUMNS)].apply(pd.to_numeric, errors="coerce")
    data.index = _normalise_index(frame.index)
    data = data[~data.index.isna()]
    data = data.replace([np.inf, -np.inf], np.nan).sort_index()
    data = data[~data.index.duplicated(keep="last")]
    if cutoff is not None:
        data = data[data.index <= pd.Timestamp(cutoff)]
    if data.empty:
        return None, ["no_data_before_cutoff"]

    o, h, low, c, v = (data[col] for col in REQUIRED_COLUMNS)
    tol = OHLC_TOLERANCE
    valid = (
        data[["Open", "High", "Low", "Close"]].notna().all(axis=1)
        & (o > 0)
        & (h > 0)
        & (low > 0)
        & (c > 0)
        & (h >= low * (1 - tol))
        & (c <= h * (1 + tol))
        & (c >= low * (1 - tol))
        & (o <= h * (1 + tol))
        & (o >= low * (1 - tol))
        & v.notna()
        & (v >= 0)
    )
    reasons: list[str] = []
    recent_invalid = int((~valid).tail(INVALID_WINDOW_ROWS).sum())
    if recent_invalid > max(2, int(0.05 * min(len(data), INVALID_WINDOW_ROWS))):
        reasons.append(
            f"unreliable_records:{recent_invalid}_invalid_rows_in_last_{INVALID_WINDOW_ROWS}"
        )
        return None, reasons
    data = data[valid]
    if data.empty:
        return None, ["no_valid_rows"]
    return data, reasons


# ---------------------------------------------------------------------------
# Features (backward-looking only)
# ---------------------------------------------------------------------------


def compute_feature_frame(ohlcv: pd.DataFrame) -> pd.DataFrame:
    """Compute per-date features from a cleaned OHLCV frame.

    Every column on row ``t`` depends only on bars dated ``<= t`` (rolling and
    exponentially weighted windows look backwards; ``shift`` is always positive), so a
    row can be used as the information set at the close of day ``t``. The repository's
    indicator helpers mutate their input, hence the private working copy.
    """
    work = ohlcv.loc[:, list(REQUIRED_COLUMNS)].astype(float).copy()
    calculate_sma(work, 20)
    calculate_sma(work, 50)
    calculate_rsi(work, 14)
    calculate_macd(work)
    calculate_atr(work, 14)

    close, high, low, open_, volume = (
        work[col] for col in ("Close", "High", "Low", "Open", "Volume")
    )
    feats = pd.DataFrame(index=work.index)
    feats["close"] = close
    for days in (1, 5, 20):
        feats[f"ret_{days}d"] = close.pct_change(days)

    day_range = high - low
    feats["clv"] = ((close - low) / day_range).where(day_range > 0)
    prior_high_20 = high.rolling(20).max().shift(1)
    feats["breakout_20d"] = (close > prior_high_20).astype(float).where(prior_high_20.notna())
    feats["breakout_proximity"] = close / prior_high_20 - 1.0

    turnover = close * volume
    feats["vol_ratio"] = volume / volume.rolling(20).mean().shift(1)
    feats["turnover_ratio"] = turnover / turnover.rolling(20).mean().shift(1)
    rising = feats["ret_1d"] > 0
    known = feats["ret_1d"].notna()
    for name, ratio in (("up_volume_surge", "vol_ratio"), ("up_turnover_surge", "turnover_ratio")):
        surge = np.log1p((feats[ratio] - 1.0).clip(lower=0))
        feats[name] = surge.where(rising, 0.0).where(known & feats[ratio].notna())

    feats["above_sma20"] = close / work["SMA_20"] - 1.0
    feats["sma20_over_sma50"] = work["SMA_20"] / work["SMA_50"] - 1.0
    feats["rsi14"] = work["RSI_14"]
    feats["rsi_balance"] = -(work["RSI_14"] - 60.0).abs()
    feats["macd_hist_norm"] = work["Histogram"] / close
    feats["atr_pct"] = work["ATR"] / close

    overnight_gap = open_ / close.shift(1) - 1.0
    feats["gap_std_60"] = overnight_gap.rolling(60, min_periods=40).std()
    feats["gap_abs_max_60"] = overnight_gap.abs().rolling(60, min_periods=40).max()

    feats["median_turnover_20"] = turnover.rolling(20).median()
    feats["zero_volume_days_10"] = (volume == 0).astype(float).rolling(10).sum()
    feats["max_abs_move_25"] = close.pct_change().abs().rolling(25).max()
    day_gaps = pd.Series(work.index, index=work.index).diff().dt.days
    feats["max_gap_days_60"] = day_gaps.rolling(60, min_periods=1).max()
    feats["history_len"] = np.arange(1, len(work) + 1, dtype=float)
    return feats.replace([np.inf, -np.inf], np.nan)


def benchmark_feature_frame(index_ohlcv: pd.DataFrame) -> pd.DataFrame:
    """Backward-looking index returns used for market-relative strength."""
    close = index_ohlcv["Close"].astype(float)
    return pd.DataFrame(
        {"bm_ret_5d": close.pct_change(5), "bm_ret_20d": close.pct_change(20)},
        index=index_ohlcv.index,
    )


def ineligibility_flags(feats: pd.DataFrame, config: ScannerConfig) -> pd.DataFrame:
    """Boolean reason columns (True = excluded) shared by the scanner and the backtest."""
    flags = pd.DataFrame(index=feats.index)
    flags["insufficient_history"] = (feats["history_len"] < config.min_history) | feats[
        ["ret_20d", "above_sma20", "sma20_over_sma50", "rsi14", "atr_pct", "gap_std_60"]
    ].isna().any(axis=1)
    flags["price_below_minimum"] = feats["close"] < config.min_price
    flags["low_liquidity"] = ~(feats["median_turnover_20"] >= config.min_median_turnover)
    flags["no_trading_on_cutoff_session"] = feats["vol_ratio"].isna() | (
        feats["turnover_ratio"].fillna(0.0) <= 0.0
    )
    flags["frequent_zero_volume"] = feats["zero_volume_days_10"] > config.max_zero_volume_days_10
    flags["data_gap"] = feats["max_gap_days_60"] > config.max_gap_days
    flags["extreme_move_unverified"] = feats["max_abs_move_25"] > config.max_abs_daily_move
    return flags


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------


def add_relative_strength(panel: pd.DataFrame) -> pd.DataFrame:
    """Add market- and sector-relative strength columns to a one-date cross-section.

    Market strength needs the ``bm_ret_*`` columns; sector strength compares each stock
    with the median 5-day return of the other same-sector stocks in the panel and is only
    defined with at least ``MIN_SECTOR_PEERS`` peers and a classified sector.
    """
    result = panel.copy()
    for window in ("5d", "20d"):
        bm = result.get(f"bm_ret_{window}", pd.Series(np.nan, index=result.index))
        result[f"rs_market_{window}"] = result[f"ret_{window}"] - bm
    sector_rs = np.full(len(result), np.nan)
    if "sector" in result.columns:
        returns = result["ret_5d"].to_numpy(dtype=float)
        sectors = result["sector"].to_numpy()
        for sector in pd.unique(sectors):
            members = np.flatnonzero(sectors == sector)
            if sector == "Unclassified" or len(members) <= MIN_SECTOR_PEERS:
                continue
            for position in members:
                if np.isnan(returns[position]):
                    continue
                peers = returns[members[members != position]]
                peers = peers[~np.isnan(peers)]
                if len(peers) >= MIN_SECTOR_PEERS:
                    sector_rs[position] = returns[position] - np.median(peers)
    result["rs_sector_5d"] = sector_rs
    return result


def score_panel(panel: pd.DataFrame, config: ScannerConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Score a one-date cross-section; returns ``(scores, factor_percentile_ranks)``.

    Each factor becomes a cross-sectional percentile rank in [0, 1]; the positive score is
    the weight-averaged rank scaled to 0-100 over the factors that are available for that
    stock (weights renormalised). Volatility, overnight-gap and over-extension penalties are
    subtracted. The result orders stocks within one date only.
    """
    ranks = pd.DataFrame(index=panel.index)
    for name in FACTOR_WEIGHTS:
        column = panel[name] if name in panel.columns else pd.Series(np.nan, index=panel.index)
        if column.notna().sum() < config.min_cross_section:
            ranks[name] = np.nan
        else:
            ranks[name] = column.rank(pct=True, method="average")

    weights = pd.Series(FACTOR_WEIGHTS)
    available = ranks.notna().mul(weights, axis=1)
    available_weight = available.sum(axis=1)
    coverage = available_weight / weights.sum()
    weighted = ranks.mul(weights, axis=1).sum(axis=1, skipna=True)
    positive = (weighted / available_weight.where(available_weight > 0)) * 100.0

    volatility = VOLATILITY_PENALTY_MAX * panel["atr_pct"].rank(pct=True)
    gap_risk = GAP_RISK_PENALTY_MAX * panel["gap_std_60"].rank(pct=True)
    extension = OVEREXTENSION_PENALTY * (
        (panel["rsi14"] > config.overbought_rsi).astype(float)
        + (panel["ret_1d"] > config.extended_move).astype(float)
    )
    penalty = volatility.fillna(0.0) + gap_risk.fillna(0.0) + extension

    scores = pd.DataFrame(
        {
            "score": (positive - penalty).clip(lower=0.0, upper=100.0),
            "positive_score": positive,
            "penalty": penalty,
            "factor_coverage": coverage,
        },
        index=panel.index,
    )
    return scores, ranks


def rankable(scores: pd.DataFrame, config: ScannerConfig) -> pd.DataFrame:
    """Rows whose available factor weight meets the minimum coverage.

    A small epsilon absorbs floating-point error in the weight sums, so a stock at exactly
    the threshold (for example 0.80) is not dropped by rounding. Shared by the live scan
    and the walk-forward evaluation so the two cannot disagree.
    """
    return scores[scores["factor_coverage"] >= config.min_factor_coverage - COVERAGE_EPSILON]


def _format_value(value: float, kind: str) -> str:
    if kind == "pct":
        return f"{value * 100:+.1f}%"
    if kind == "mult":
        return f"{value:.1f}x avg"
    return f"{value:.2f}"


def supporting_factors(
    feature_row: pd.Series, rank_row: pd.Series, limit: int = 4
) -> tuple[str, ...]:
    """Describe the factors that lift a stock furthest above the neutral (median) rank."""
    edges = {
        name: (rank_row[name] - 0.5) * weight
        for name, weight in FACTOR_WEIGHTS.items()
        if pd.notna(rank_row.get(name))
    }
    notes: list[str] = []
    for name, edge in sorted(edges.items(), key=lambda item: item[1], reverse=True):
        if edge <= 0 or len(notes) >= limit:
            break
        label, column, kind = FACTOR_DISPLAY[name]
        value = feature_row.get(column)
        if pd.isna(value):
            continue
        notes.append(
            f"{label}: {_format_value(float(value), kind)} (percentile {rank_row[name] * 100:.0f})"
        )
    if feature_row.get("breakout_20d") == 1.0:
        notes.append("Closed above prior 20-day high")
    return tuple(notes)


def risk_flags(
    feature_row: pd.Series, rank_row: pd.Series, config: ScannerConfig, sector: str
) -> tuple[str, ...]:
    """Plain-language risk flags derived from observable data only."""
    flags: list[str] = []
    atr_rank = rank_row.get("atr_pct_rank")
    if feature_row["atr_pct"] > 0.04 or (pd.notna(atr_rank) and atr_rank >= 0.9):
        flags.append("high_volatility")
    gap_rank = rank_row.get("gap_std_rank")
    if feature_row["gap_abs_max_60"] > 0.05 or (pd.notna(gap_rank) and gap_rank >= 0.9):
        flags.append("high_overnight_gap_risk")
    if feature_row["rsi14"] > config.overbought_rsi:
        flags.append("overbought_rsi")
    if feature_row["ret_1d"] > config.extended_move:
        flags.append("extended_1d_move")
    if feature_row["vol_ratio"] > 5.0:
        flags.append("extreme_volume_spike_cause_unverified")
    if feature_row["median_turnover_20"] < 2.0 * config.min_median_turnover:
        flags.append("near_liquidity_floor")
    if sector == "Unclassified":
        flags.append("sector_unclassified")
    return tuple(flags)


# ---------------------------------------------------------------------------
# Provider boundary
# ---------------------------------------------------------------------------


def default_frame_fetcher(period: str = "1y") -> FrameFetcher:
    """Build the default fetcher on top of ``download_market_frames`` (lazy import)."""

    def fetch(tickers: list[str]) -> tuple[dict[str, pd.DataFrame], Mapping[str, Any]]:
        from services.resilient_market_data import download_market_frames

        return download_market_frames(tickers, period=period, interval="1d", auto_adjust=True)

    return fetch


def default_safety_fetcher(
    symbols: list[str], as_of: date | None
) -> tuple[pd.DataFrame, str | None]:
    """NSE surveillance flags via the existing ``scanner.surveillance`` module."""
    from scanner.surveillance import fetch_nse_safety_snapshot

    return fetch_nse_safety_snapshot(symbols, as_of)


def _unavailable(
    reason: str,
    now: datetime,
    cutoff: date | None = None,
    target: date | None = None,
    excluded: Sequence[ExclusionRecord] = (),
    data_quality: dict[str, Any] | None = None,
    errors: Sequence[str] = (),
) -> ScanResult:
    return ScanResult(
        status="UNAVAILABLE",
        candidates=(),
        excluded=tuple(excluded),
        prediction_cutoff=cutoff_timestamp(cutoff) if cutoff else None,
        target_business_date=target,
        generated_at=now,
        data_quality=data_quality or {},
        unavailable_data=UNSUPPORTED_DATA,
        warnings=(reason,),
        errors=tuple(errors),
    )


def scan_next_day_movers(
    config: ScannerConfig | None = None,
    *,
    now: datetime | None = None,
    universe: Iterable[Instrument | tuple[str, str]] | None = None,
    fetcher: FrameFetcher | None = None,
    safety_fetcher: SafetyFetcher | None = None,
) -> ScanResult:
    """Rank next-business-day upside candidates using only data up to the cutoff session.

    Provider failures, stale data and invalid records are reported in the result and
    never papered over. When no trustworthy cross-section exists the status is
    ``UNAVAILABLE`` and the shortlist is empty.
    """
    cfg = config or ScannerConfig()
    now = now or datetime.now(IST)
    now = now.replace(tzinfo=IST) if now.tzinfo is None else now.astimezone(IST)

    try:
        cutoff, target = resolve_prediction_cutoff(now, cfg)
    except CalendarUnavailableError as exc:
        return _unavailable(f"Trading calendar unavailable: {exc}", now, errors=(str(exc),))

    instruments, excluded = build_universe(universe, cfg)
    excluded = list(excluded)
    tickers: dict[Instrument, str] = {}
    for inst in instruments:
        ticker = ticker_for(inst)
        if ticker is None:
            excluded.append(
                ExclusionRecord(inst.symbol, inst.exchange, None, ("no_ticker_mapping",))
            )
        elif ticker in tickers.values():
            excluded.append(
                ExclusionRecord(inst.symbol, inst.exchange, ticker, ("duplicate_ticker",))
            )
        else:
            tickers[inst] = ticker
    if not tickers:
        return _unavailable("Universe is empty after validation.", now, cutoff, target, excluded)

    bench = benchmark_tickers(sorted({i.exchange for i in tickers}))
    request = list(dict.fromkeys([*tickers.values(), *bench.values()]))
    fetch = fetcher or default_frame_fetcher(cfg.history_period)
    try:
        frames, diagnostics = fetch(request)
    except Exception as exc:  # provider boundary: any failure is reported, never hidden
        logger.exception("Market-data provider failed")
        return _unavailable(
            f"Market-data provider failed: {type(exc).__name__}: {exc}",
            now,
            cutoff,
            target,
            excluded,
            errors=(f"{type(exc).__name__}: {exc}",),
        )

    benchmarks: dict[str, pd.DataFrame] = {}
    unavailable = list(UNSUPPORTED_DATA)
    warnings: list[str] = []
    for exchange, ticker in bench.items():
        clean, reasons = clean_ohlcv(frames.get(ticker), cutoff)
        if clean is None or clean.index[-1].date() != cutoff:
            detail = reasons or [f"last bar {None if clean is None else clean.index[-1].date()}"]
            unavailable.append(
                f"Market-relative strength unavailable for {exchange} ({ticker}): {', '.join(detail)}"
            )
            continue
        benchmarks[exchange] = benchmark_feature_frame(clean)

    rows: dict[str, pd.Series] = {}
    last_dates: dict[str, date] = {}
    meta: dict[str, Instrument] = {}
    for inst, ticker in tickers.items():
        clean, reasons = clean_ohlcv(frames.get(ticker), cutoff)
        if clean is None:
            excluded.append(ExclusionRecord(inst.symbol, inst.exchange, ticker, tuple(reasons)))
            continue
        last_date = clean.index[-1].date()
        if last_date != cutoff:
            excluded.append(
                ExclusionRecord(
                    inst.symbol, inst.exchange, ticker, (f"stale_data:last_bar={last_date}",)
                )
            )
            continue
        feats = compute_feature_frame(clean)
        flags = ineligibility_flags(feats, cfg).iloc[-1]
        problems = [name for name, hit in flags.items() if bool(hit)]
        if problems:
            excluded.append(ExclusionRecord(inst.symbol, inst.exchange, ticker, tuple(problems)))
            continue
        row = feats.iloc[-1].copy()
        if inst.exchange in benchmarks:
            row = pd.concat([row, benchmarks[inst.exchange].loc[pd.Timestamp(cutoff)]])
        rows[ticker] = row
        last_dates[ticker] = last_date
        meta[ticker] = inst

    requested = len(tickers)
    usable = len(rows)
    coverage = usable / requested if requested else 0.0
    quality: dict[str, Any] = {
        "universe_requested": requested,
        "eligible": usable,
        "coverage_pct": round(coverage * 100, 1),
        "provider_diagnostics": dict(diagnostics) if diagnostics else {},
        "excluded_count": len(excluded),
        "stale_symbols": sum(
            1 for rec in excluded if any(r.startswith("stale_data") for r in rec.reasons)
        ),
    }

    surveillance_note: str | None = None
    flagged: dict[str, str] = {}
    nse_symbols = [meta[t].symbol for t in rows if meta[t].exchange == "NSE"]
    if cfg.check_surveillance and nse_symbols:
        checker = safety_fetcher or default_safety_fetcher
        try:
            snapshot, error = checker(nse_symbols, cutoff)
        except Exception as exc:  # provider boundary
            logger.exception("Surveillance provider failed")
            snapshot, error = pd.DataFrame(), f"{type(exc).__name__}: {exc}"
        if error or snapshot is None or snapshot.empty:
            surveillance_note = error or "empty response"
            unavailable.append(f"NSE surveillance flags unavailable: {surveillance_note}")
        else:
            flagged = {
                str(r["Symbol"]): str(r["Safety flags"])
                for _, r in snapshot.iterrows()
                if str(r.get("Safety flags", "")).strip()
            }
        if flagged and cfg.exclude_surveillance_flagged:
            for ticker in [
                t for t in rows if meta[t].exchange == "NSE" and meta[t].symbol in flagged
            ]:
                inst = meta.pop(ticker)
                rows.pop(ticker)
                excluded.append(
                    ExclusionRecord(
                        inst.symbol,
                        inst.exchange,
                        ticker,
                        (f"nse_surveillance:{flagged[inst.symbol]}",),
                    )
                )

    if len(rows) < cfg.min_cross_section:
        return _unavailable(
            f"Only {len(rows)} eligible symbols (need {cfg.min_cross_section}) - no ranking produced.",
            now,
            cutoff,
            target,
            excluded,
            quality,
        )

    panel = pd.DataFrame(rows).T.astype(float)
    panel["sector"] = [sector_of(meta[t]) for t in panel.index]
    panel = add_relative_strength(panel)
    scores, ranks = score_panel(panel, cfg)
    ranks["atr_pct_rank"] = panel["atr_pct"].rank(pct=True)
    ranks["gap_std_rank"] = panel["gap_std_60"].rank(pct=True)

    eligible = rankable(scores, cfg)
    for ticker in scores.index.difference(eligible.index):
        inst = meta[ticker]
        excluded.append(
            ExclusionRecord(inst.symbol, inst.exchange, ticker, ("insufficient_factor_coverage",))
        )
    ordered = eligible.assign(_ticker=eligible.index).sort_values(
        ["score", "positive_score", "_ticker"], ascending=[False, False, True]
    )

    for exchange in sorted({i.exchange for i in meta.values()}):
        if exchange not in benchmarks:
            warnings.append(
                f"Market-relative strength missing for {exchange}; factor weights renormalised."
            )
    if coverage < cfg.min_universe_coverage:
        warnings.append(
            f"Only {coverage * 100:.0f}% of the universe produced usable data; ranking may be unrepresentative."
        )
    if surveillance_note:
        warnings.append("NSE surveillance check unavailable; review flags manually before any use.")
    status = "DEGRADED" if warnings else "OK"

    candidates: list[Candidate] = []
    cutoff_ts = cutoff_timestamp(cutoff)
    for position, (ticker, score_row) in enumerate(ordered.head(cfg.top_n).iterrows(), start=1):
        inst = meta[ticker]
        flags_out = list(
            risk_flags(panel.loc[ticker], ranks.loc[ticker], cfg, panel.at[ticker, "sector"])
        )
        if inst.exchange == "BSE":
            flags_out.append("bse_surveillance_not_checked")
        elif surveillance_note:
            flags_out.append("nse_surveillance_check_unavailable")
        candidates.append(
            Candidate(
                rank=position,
                symbol=inst.symbol,
                exchange=inst.exchange,
                ticker=str(ticker),
                score=round(float(score_row["score"]), 2),
                positive_score=round(float(score_row["positive_score"]), 2),
                penalty=round(float(score_row["penalty"]), 2),
                factor_coverage=round(float(score_row["factor_coverage"]), 3),
                supporting_factors=supporting_factors(panel.loc[ticker], ranks.loc[ticker]),
                risk_flags=tuple(flags_out),
                last_close=round(float(panel.at[ticker, "close"]), 2),
                data_timestamp=last_dates[ticker],
                data_source=DATA_SOURCE,
                prediction_cutoff=cutoff_ts,
                target_business_date=target,
            )
        )

    quality["ranked"] = len(ordered)
    return ScanResult(
        status=status,
        candidates=tuple(candidates),
        excluded=tuple(excluded),
        prediction_cutoff=cutoff_ts,
        target_business_date=target,
        generated_at=now,
        data_quality=quality,
        unavailable_data=tuple(unavailable),
        warnings=tuple(warnings),
    )
