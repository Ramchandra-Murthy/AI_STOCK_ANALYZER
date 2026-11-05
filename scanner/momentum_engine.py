"""Intraday momentum engine: a transparent 0-100 momentum-strength score per stock.

Pure computation on one-minute OHLCV bars. No network, no Streamlit, no globals, so it is
deterministic and unit-testable; fetching and ranking live in later layers.

What the score is
-----------------
``score`` measures how strong and how well confirmed the *recent* price move is. It is not
a probability, not a forecast and not a buy or sell signal. It is comparable between
symbols at one moment, and the same fixed scales apply to every symbol (nothing is fitted).

Components (maximum points sum to 100)::

    magnitude      60  per-window move size vs a fixed scale, dominant side only
                       (1m 10, 5m 20, 10m 15, 15m 15)
    confirmation   20  share of the available window weight that agrees with the direction
    volume         20  recent volume vs the session's earlier typical volume

If a component cannot be computed (for example volume for an index, or a window with no
bar), its points are removed and the score is rescaled over the points that remain.
``score_coverage`` reports that share, so a score built from less evidence is visible and a
scanner can filter on it. Nothing is ever filled in with an invented value.

Data rules
----------
* Only *completed* bars count: a bar stamped ``t`` is complete once ``t + 1 minute <= as_of``.
  The forming bar and any later bar are dropped, so a result never depends on information
  after ``as_of`` (no look-ahead).
* Only bars from the same IST calendar date as the latest bar are used, so an overnight
  gap is never read as intraday momentum.
* Window returns are time based (the bar ``w`` minutes before the latest bar), not
  position based, so missing minutes cannot silently stretch a window.
* Stale, insufficient and invalid data produce an explicit status and no score.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

IST = ZoneInfo("Asia/Kolkata")

SCORE_TYPE = "momentum_strength_0_100_not_a_probability"
WINDOWS: tuple[int, ...] = (1, 5, 10, 15)

# Status values. Only OK and PARTIAL carry a score.
STATUS_OK = "OK"
STATUS_PARTIAL = "PARTIAL"
STATUS_STALE = "STALE"
STATUS_INSUFFICIENT = "INSUFFICIENT"
STATUS_INVALID = "INVALID"
SCORED_STATUSES = frozenset({STATUS_OK, STATUS_PARTIAL})

DIRECTIONS = ("UP", "DOWN", "MIXED", "NEUTRAL")
VOLUME_STATES = ("CONFIRMED", "NORMAL", "WEAK", "UNAVAILABLE")
CONFIRMATION_LEVELS = ("FULL", "PARTIAL", "NONE")

# Fixed, a-priori parameters (not fitted to any data).
WINDOW_POINTS: dict[int, float] = {1: 10.0, 5: 20.0, 10: 15.0, 15: 15.0}
CONFIRMATION_POINTS = 20.0
VOLUME_POINTS = 20.0
MAX_SCORE = 100.0
FLOAT_EPSILON = 1e-12
BAR = pd.Timedelta(minutes=1)

# Move that earns full magnitude credit for a window (fraction, 0.005 = 0.5%).
WINDOW_FULL_SCALE: dict[int, float] = {1: 0.005, 5: 0.010, 10: 0.015, 15: 0.020}


@dataclass(frozen=True)
class MomentumConfig:
    """Tunable but fixed-in-advance parameters. Defaults are documented assumptions."""

    flat_band: float = 0.0002  # |window return| at or below this is "flat" (2 bps)
    direction_share: float = 0.75  # weight share one side needs to call UP or DOWN
    min_windows: int = 2  # windows required to score at all
    full_confirmation_min_windows: int = 3  # windows needed for FULL confirmation
    stale_after_seconds: float = 180.0  # latest completed bar older than this is STALE
    lookback_tolerance_minutes: int = 1  # accepted gap when locating a window's start bar
    max_abs_window_return: float = 0.20  # larger moves are treated as unverified bad data
    volume_recent_minutes: int = 5
    volume_baseline_minutes: int = 30
    volume_min_baseline_bars: int = 10
    volume_confirmed_ratio: float = 1.5
    volume_weak_ratio: float = 0.8
    volume_full_ratio: float = 2.0  # recent/baseline ratio worth full volume points

    def __post_init__(self) -> None:
        for name in (
            "flat_band",
            "stale_after_seconds",
            "max_abs_window_return",
            "volume_confirmed_ratio",
            "volume_weak_ratio",
            "volume_full_ratio",
        ):
            value = getattr(self, name)
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a positive finite number")
        if not 0.5 < self.direction_share <= 1.0:
            raise ValueError("direction_share must be in (0.5, 1]")
        if not 1 <= self.min_windows <= len(WINDOWS):
            raise ValueError(f"min_windows must be between 1 and {len(WINDOWS)}")
        if not 1 <= self.full_confirmation_min_windows <= len(WINDOWS):
            raise ValueError("full_confirmation_min_windows must be between 1 and 4")
        for name in (
            "lookback_tolerance_minutes",
            "volume_recent_minutes",
            "volume_baseline_minutes",
            "volume_min_baseline_bars",
        ):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be at least 1")
        if self.volume_weak_ratio >= self.volume_confirmed_ratio:
            raise ValueError("volume_weak_ratio must be below volume_confirmed_ratio")
        if self.volume_full_ratio <= 1.0:
            raise ValueError("volume_full_ratio must be above 1")


DEFAULT_CONFIG = MomentumConfig()


@dataclass(frozen=True)
class ScoreComponent:
    """One explainable piece of the score. ``points`` is None when it was not computable."""

    name: str
    points: float | None
    max_points: float
    detail: str


@dataclass(frozen=True)
class MomentumResult:
    """Engine output for one symbol. ``score`` is None unless the status is scored."""

    status: str
    score: float | None
    direction: str
    as_of: datetime
    last_bar_time: datetime | None
    data_age_seconds: float | None
    returns: Mapping[int, float | None]
    window_notes: Mapping[int, str]
    components: tuple[ScoreComponent, ...]
    score_coverage: float
    volume_ratio: float | None
    volume_state: str
    timeframe_confirmation: str
    agreeing_windows: int
    available_windows: int
    reasons: tuple[str, ...] = ()
    score_type: str = SCORE_TYPE
    symbol: str | None = None
    extras: Mapping[str, Any] = field(default_factory=dict)

    @property
    def is_scored(self) -> bool:
        return self.status in SCORED_STATUSES and self.score is not None

    def to_dict(self) -> dict[str, Any]:
        """Flat, display-friendly dictionary (percent returns, one column per window)."""
        row: dict[str, Any] = {
            "Symbol": self.symbol,
            "Status": self.status,
            "Momentum score": self.score,
            "Direction": self.direction,
            "Timeframe confirmation": self.timeframe_confirmation,
            "Agreeing windows": f"{self.agreeing_windows}/{self.available_windows}",
            "Volume state": self.volume_state,
            "Volume ratio": self.volume_ratio,
            "Score coverage": self.score_coverage,
            "Last bar": None if self.last_bar_time is None else self.last_bar_time.isoformat(),
            "Data age (s)": self.data_age_seconds,
            "Reasons": ", ".join(self.reasons),
        }
        for window in WINDOWS:
            value = self.returns.get(window)
            row[f"{window}m %"] = None if value is None else round(value * 100.0, 4)
        return row


# ---------------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------------


def _as_ist(moment: datetime | None) -> datetime:
    """Return ``moment`` as an IST-aware datetime (naive values are taken to be IST)."""
    if moment is None:
        return datetime.now(IST)
    return moment.replace(tzinfo=IST) if moment.tzinfo is None else moment.astimezone(IST)


def _ist_index(index: pd.Index) -> pd.DatetimeIndex:
    stamps = pd.DatetimeIndex(pd.to_datetime(index, errors="coerce"))
    if stamps.tz is None:
        return stamps.tz_localize(IST, ambiguous="NaT", nonexistent="NaT")
    return stamps.tz_convert(IST)


def _prepare_bars(
    frame: pd.DataFrame | None, as_of: datetime
) -> tuple[pd.DataFrame | None, list[str]]:
    """Return completed same-session bars with a clean ``Close`` (and ``Volume`` if usable).

    ``None`` plus the reasons when nothing usable remains. Never modifies ``frame``.
    """
    if frame is None or len(frame) == 0:
        return None, ["no_data"]
    if "Close" not in frame.columns:
        return None, ["missing_close_column"]

    stamps = _ist_index(frame.index)
    close = pd.to_numeric(frame["Close"], errors="coerce").to_numpy(dtype=float)
    if "Volume" in frame.columns:
        volume = pd.to_numeric(frame["Volume"], errors="coerce").to_numpy(dtype=float)
    else:
        volume = np.full(len(frame), np.nan)
    bars = pd.DataFrame({"Close": close, "Volume": volume}, index=stamps)
    bars = bars[~bars.index.isna()]
    bars = bars.sort_index()
    bars = bars[~bars.index.duplicated(keep="last")]

    reasons: list[str] = []
    # Completed bars only: the forming minute and anything later never enter a feature.
    completed = bars[bars.index + BAR <= pd.Timestamp(as_of)]
    if len(completed) < len(bars):
        reasons.append(f"dropped_incomplete_or_future_bars:{len(bars) - len(completed)}")
    bars = completed

    valid_price = np.isfinite(bars["Close"].to_numpy()) & (bars["Close"].to_numpy() > 0)
    if not valid_price.all():
        reasons.append(f"dropped_invalid_prices:{int((~valid_price).sum())}")
    bars = bars[valid_price]
    if bars.empty:
        return None, [*reasons, "no_valid_completed_bars"]

    bars = bars[bars.index.normalize() == bars.index[-1].normalize()]

    vol = bars["Volume"].to_numpy()
    bars = bars.assign(Volume=np.where(np.isfinite(vol) & (vol >= 0), vol, np.nan))
    return bars, reasons


def _window_return(
    bars: pd.DataFrame, minutes: int, tolerance: int, max_abs: float
) -> tuple[float | None, str]:
    """Close-to-close return over ``minutes`` ending at the latest bar, or (None, reason)."""
    index = bars.index
    last_stamp = index[-1]
    target = last_stamp - pd.Timedelta(minutes=minutes)
    position = int(index.searchsorted(target, side="right")) - 1  # latest bar at or before
    if position < 0:
        return None, "insufficient_history"
    if target - index[position] > pd.Timedelta(minutes=tolerance):
        return None, "missing_bar"
    if index[position] >= last_stamp:
        return None, "insufficient_history"
    start = float(bars["Close"].iloc[position])
    end = float(bars["Close"].iloc[-1])
    value = end / start - 1.0
    if not math.isfinite(value):
        return None, "invalid_prices"
    if abs(value) > max_abs:
        return None, "unverified_extreme_move"
    return value, "ok"


def _sign(value: float, band: float) -> int:
    if abs(value) <= band + FLOAT_EPSILON:
        return 0
    return 1 if value > 0 else -1


# ---------------------------------------------------------------------------
# Direction, volume and score
# ---------------------------------------------------------------------------


def classify_direction(
    returns: Mapping[int, float | None], config: MomentumConfig = DEFAULT_CONFIG
) -> tuple[str, int, int, float]:
    """Return ``(direction, agreeing_windows, available_windows, dominant_share)``.

    Each available window votes UP, DOWN or flat (within ``flat_band``) with its fixed
    weight. NEUTRAL: every available window is flat. UP or DOWN: one side holds at least
    ``direction_share`` of the non-flat weight. Otherwise MIXED. With no available window
    the direction is NEUTRAL (there is no evidence either way).
    """
    available = [w for w in WINDOWS if returns.get(w) is not None]
    signs = {w: _sign(float(returns[w]), config.flat_band) for w in available}  # type: ignore[arg-type]
    up = sum(WINDOW_POINTS[w] for w, s in signs.items() if s > 0)
    down = sum(WINDOW_POINTS[w] for w, s in signs.items() if s < 0)
    voting = up + down
    if voting == 0:
        return "NEUTRAL", 0, len(available), 0.0
    side = 1 if up >= down else -1
    dominant = max(up, down)
    share = dominant / voting
    agreeing = sum(1 for s in signs.values() if s == side)
    if share + FLOAT_EPSILON >= config.direction_share and up != down:
        return ("UP" if side > 0 else "DOWN"), agreeing, len(available), share
    return "MIXED", agreeing, len(available), share


def volume_confirmation(
    bars: pd.DataFrame, config: MomentumConfig = DEFAULT_CONFIG
) -> tuple[float | None, str]:
    """Recent mean volume over the session's earlier median volume, with a state label.

    Recent bars are the last ``volume_recent_minutes`` completed bars; the baseline is the
    median of the ``volume_baseline_minutes`` bars immediately before them (so the surge
    never contaminates its own baseline). Returns ``(None, "UNAVAILABLE")`` when volume is
    absent (indices), too sparse, or the baseline is zero.
    """
    volume = bars["Volume"]
    recent_n = config.volume_recent_minutes
    if len(volume) <= recent_n:
        return None, "UNAVAILABLE"
    recent = volume.iloc[-recent_n:]
    baseline = volume.iloc[-(recent_n + config.volume_baseline_minutes) : -recent_n].dropna()
    if recent.isna().any() or len(baseline) < config.volume_min_baseline_bars:
        return None, "UNAVAILABLE"
    typical = float(baseline.median())
    if not math.isfinite(typical) or typical <= 0:
        return None, "UNAVAILABLE"
    ratio = float(recent.mean()) / typical
    if ratio >= config.volume_confirmed_ratio:
        return ratio, "CONFIRMED"
    if ratio < config.volume_weak_ratio:
        return ratio, "WEAK"
    return ratio, "NORMAL"


def _clip01(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def _build_components(
    returns: Mapping[int, float | None],
    direction: str,
    share: float,
    volume_ratio: float | None,
    config: MomentumConfig,
) -> tuple[ScoreComponent, ...]:
    """Explainable components. ``points`` is None where the evidence does not exist."""
    components: list[ScoreComponent] = []
    side = {"UP": 1, "DOWN": -1}.get(direction, 0)
    directional = side != 0

    # Magnitude: only the dominant side earns credit; opposing/flat windows earn nothing.
    dominant_side = side
    if not directional:
        up = sum(WINDOW_POINTS[w] for w in WINDOWS if (returns.get(w) or 0.0) > config.flat_band)
        down = sum(WINDOW_POINTS[w] for w in WINDOWS if (returns.get(w) or 0.0) < -config.flat_band)
        dominant_side = 1 if up >= down else -1
    for window in WINDOWS:
        maximum = WINDOW_POINTS[window]
        value = returns.get(window)
        name = f"magnitude_{window}m"
        if value is None:
            components.append(ScoreComponent(name, None, maximum, "window unavailable"))
            continue
        aligned = _sign(value, config.flat_band) == dominant_side
        strength = _clip01(abs(value) / WINDOW_FULL_SCALE[window]) if aligned else 0.0
        detail = f"{value * 100:+.3f}% vs full scale {WINDOW_FULL_SCALE[window] * 100:.2f}%" + (
            "" if aligned else " (not with the dominant side: 0 points)"
        )
        components.append(ScoreComponent(name, round(maximum * strength, 4), maximum, detail))

    available = sum(1 for w in WINDOWS if returns.get(w) is not None)
    if available == 0:
        components.append(ScoreComponent("confirmation", None, CONFIRMATION_POINTS, "no windows"))
    elif directional:
        points = CONFIRMATION_POINTS * share
        detail = f"{share:.0%} of window weight agrees with {direction}"
        components.append(
            ScoreComponent("confirmation", round(points, 4), CONFIRMATION_POINTS, detail)
        )
    else:
        components.append(
            ScoreComponent(
                "confirmation", 0.0, CONFIRMATION_POINTS, f"direction is {direction}: no agreement"
            )
        )

    if volume_ratio is None:
        components.append(ScoreComponent("volume", None, VOLUME_POINTS, "volume unavailable"))
    elif directional:
        span = config.volume_full_ratio - 1.0
        points = VOLUME_POINTS * _clip01((volume_ratio - 1.0) / span)
        detail = f"recent volume {volume_ratio:.2f}x the session's typical volume"
        components.append(ScoreComponent("volume", round(points, 4), VOLUME_POINTS, detail))
    else:
        detail = (
            f"recent volume {volume_ratio:.2f}x, but direction is {direction}: not a confirmation"
        )
        components.append(ScoreComponent("volume", 0.0, VOLUME_POINTS, detail))
    return tuple(components)


def _total(components: tuple[ScoreComponent, ...]) -> tuple[float, float]:
    """Return ``(score_0_100, coverage)`` rescaled over the computable components."""
    possible = sum(c.max_points for c in components if c.points is not None)
    earned = sum(c.points for c in components if c.points is not None)  # type: ignore[misc]
    if possible <= 0:
        return 0.0, 0.0
    score = min(max(earned / possible * MAX_SCORE, 0.0), MAX_SCORE)
    return round(score, 2), round(possible / MAX_SCORE, 4)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _unscored(
    status: str,
    as_of: datetime,
    reasons: list[str],
    symbol: str | None,
    *,
    last_bar: datetime | None = None,
    age: float | None = None,
    returns: Mapping[int, float | None] | None = None,
    notes: Mapping[int, str] | None = None,
) -> MomentumResult:
    return MomentumResult(
        status=status,
        score=None,
        direction="NEUTRAL",
        as_of=as_of,
        last_bar_time=last_bar,
        data_age_seconds=age,
        returns=returns or {w: None for w in WINDOWS},
        window_notes=notes or {},
        components=(),
        score_coverage=0.0,
        volume_ratio=None,
        volume_state="UNAVAILABLE",
        timeframe_confirmation="NONE",
        agreeing_windows=0,
        available_windows=0,
        reasons=tuple(reasons),
        symbol=symbol,
    )


def compute_momentum(
    frame: pd.DataFrame | None,
    *,
    as_of: datetime | None = None,
    config: MomentumConfig | None = None,
    symbol: str | None = None,
) -> MomentumResult:
    """Score one symbol's recent momentum from one-minute bars known at ``as_of``.

    ``frame`` needs a datetime index (naive values are taken as IST) and a ``Close``
    column; ``Volume`` is optional. ``as_of`` defaults to now (IST); pass it explicitly to
    replay or test. Returns a result whose ``status`` says whether a score exists.
    """
    cfg = config or DEFAULT_CONFIG
    moment = _as_ist(as_of)
    bars, reasons = _prepare_bars(frame, moment)
    if bars is None:
        status = STATUS_INVALID if "missing_close_column" in reasons else STATUS_INSUFFICIENT
        return _unscored(status, moment, reasons, symbol)

    last_bar = bars.index[-1]
    age = (pd.Timestamp(moment) - (last_bar + BAR)).total_seconds()
    last_dt = last_bar.to_pydatetime()
    if age > cfg.stale_after_seconds:
        return _unscored(
            STATUS_STALE,
            moment,
            [*reasons, f"latest_completed_bar_is_{age:.0f}s_old"],
            symbol,
            last_bar=last_dt,
            age=age,
        )

    returns: dict[int, float | None] = {}
    notes: dict[int, str] = {}
    for window in WINDOWS:
        returns[window], notes[window] = _window_return(
            bars, window, cfg.lookback_tolerance_minutes, cfg.max_abs_window_return
        )
    available = [w for w in WINDOWS if returns[w] is not None]
    if len(available) < cfg.min_windows:
        missing = ", ".join(f"{w}m:{notes[w]}" for w in WINDOWS if returns[w] is None)
        return _unscored(
            STATUS_INSUFFICIENT,
            moment,
            [*reasons, f"only_{len(available)}_of_{len(WINDOWS)}_windows ({missing})"],
            symbol,
            last_bar=last_dt,
            age=age,
            returns=returns,
            notes=notes,
        )

    direction, agreeing, count, share = classify_direction(returns, cfg)
    ratio, volume_state = volume_confirmation(bars, cfg)
    components = _build_components(returns, direction, share, ratio, cfg)
    score, coverage = _total(components)

    if (
        direction in {"UP", "DOWN"}
        and agreeing == count
        and count >= cfg.full_confirmation_min_windows
    ):
        confirmation = "FULL"
    elif direction in {"UP", "DOWN"}:
        confirmation = "PARTIAL"
    else:
        confirmation = "NONE"

    # Routine preparation notes (such as the forming bar being dropped) are informational;
    # only missing evidence makes a result PARTIAL.
    missing_evidence: list[str] = []
    if len(available) < len(WINDOWS):
        missing_evidence.append(
            "windows_unavailable:" + ",".join(f"{w}m" for w in WINDOWS if returns[w] is None)
        )
    if volume_state == "UNAVAILABLE":
        missing_evidence.append("volume_unavailable")
    result_reasons = [*reasons, *missing_evidence]
    return MomentumResult(
        status=STATUS_PARTIAL if missing_evidence else STATUS_OK,
        score=score,
        direction=direction,
        as_of=moment,
        last_bar_time=last_dt,
        data_age_seconds=round(age, 3),
        returns=returns,
        window_notes=notes,
        components=components,
        score_coverage=coverage,
        volume_ratio=None if ratio is None else round(ratio, 4),
        volume_state=volume_state,
        timeframe_confirmation=confirmation,
        agreeing_windows=agreeing,
        available_windows=count,
        reasons=tuple(result_reasons),
        symbol=symbol,
    )


def compute_momentum_batch(
    frames: Mapping[str, pd.DataFrame | None],
    *,
    as_of: datetime | None = None,
    config: MomentumConfig | None = None,
) -> dict[str, MomentumResult]:
    """Score many symbols against one shared ``as_of`` (resolved once, so all agree).

    One symbol's bad data cannot affect another: each is scored independently and every
    input key appears in the output.
    """
    moment = _as_ist(as_of)
    return {
        symbol: compute_momentum(frame, as_of=moment, config=config, symbol=symbol)
        for symbol, frame in frames.items()
    }
