"""Deterministic unit tests for the intraday momentum engine (synthetic bars only)."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from scanner.momentum_engine import (
    SCORE_TYPE,
    WINDOW_FULL_SCALE,
    WINDOW_POINTS,
    WINDOWS,
    MomentumConfig,
    classify_direction,
    compute_momentum,
    compute_momentum_batch,
    volume_confirmation,
)

IST = ZoneInfo("Asia/Kolkata")
DAY = datetime(2026, 11, 4, tzinfo=IST)
# Latest completed bar is 11:29 (ends 11:30); we score at 11:30:20.
AS_OF = DAY.replace(hour=11, minute=30, second=20)
LAST = DAY.replace(hour=11, minute=29)
N_BARS = 120


def bars(
    closes: list[float] | np.ndarray,
    volume: float | list[float] | np.ndarray | None = 100_000.0,
    last: datetime = LAST,
) -> pd.DataFrame:
    """One-minute bars whose final bar starts at ``last``."""
    n = len(closes)
    index = pd.date_range(end=last, periods=n, freq="1min", tz=IST)
    data: dict[str, object] = {"Close": np.asarray(closes, dtype=float)}
    if volume is not None:
        data["Volume"] = np.broadcast_to(np.asarray(volume, dtype=float), (n,)).copy()
    return pd.DataFrame(data, index=index)


def flat(price: float = 100.0, n: int = N_BARS) -> np.ndarray:
    return np.full(n, price)


def with_tail(tail: dict[int, float], base: float = 100.0, n: int = N_BARS) -> np.ndarray:
    """Closes where the price ``w`` bars before the end is ``base`` * (1 - ret) so the
    w-minute return is exactly ``tail[w]`` for each given window (windows must be ordered
    so that later (shorter) windows overwrite earlier ones consistently)."""
    end = base
    closes = np.full(n, base, dtype=float)
    for window, ret in sorted(tail.items(), reverse=True):
        closes[n - 1 - window] = end / (1.0 + ret)
    return closes


def score(closes, volume=100_000.0, **kwargs):
    return compute_momentum(bars(closes, volume), as_of=AS_OF, **kwargs)


# ---------------------------------------------------------------------------
# Formulas
# ---------------------------------------------------------------------------


def test_window_returns_are_exact_close_to_close_returns() -> None:
    closes = np.linspace(100.0, 101.19, N_BARS)
    result = score(closes)
    for window in WINDOWS:
        expected = closes[-1] / closes[-1 - window] - 1.0
        assert result.returns[window] == pytest.approx(expected, rel=1e-12)
    assert result.to_dict()["5m %"] == pytest.approx((closes[-1] / closes[-6] - 1) * 100, abs=1e-4)


def test_all_four_windows_are_reported_when_data_allows() -> None:
    result = score(np.linspace(100, 101, N_BARS))
    assert set(result.returns) == set(WINDOWS)
    assert all(value is not None for value in result.returns.values())
    assert result.available_windows == 4


def test_component_points_sum_to_the_score_when_everything_is_available() -> None:
    result = score(
        np.linspace(100, 100.9, N_BARS), volume=np.r_[np.full(N_BARS - 5, 1e5), np.full(5, 1.5e5)]
    )
    assert result.score_coverage == 1.0
    total = sum(c.points for c in result.components if c.points is not None)
    assert result.score == pytest.approx(total, abs=0.01)
    assert {c.name for c in result.components} == {
        "magnitude_1m",
        "magnitude_5m",
        "magnitude_10m",
        "magnitude_15m",
        "confirmation",
        "volume",
    }
    assert sum(c.max_points for c in result.components) == pytest.approx(100.0)


def test_magnitude_points_scale_linearly_up_to_the_full_scale_and_then_cap() -> None:
    half = {w: WINDOW_FULL_SCALE[w] / 2 for w in WINDOWS}
    result = score(with_tail(half), volume=None)
    magnitude = {c.name: c.points for c in result.components if c.name.startswith("magnitude")}
    for window in WINDOWS:
        assert magnitude[f"magnitude_{window}m"] == pytest.approx(
            WINDOW_POINTS[window] / 2, abs=1e-3
        )
    over = {w: WINDOW_FULL_SCALE[w] * 5 for w in WINDOWS}
    capped = score(with_tail(over), volume=None)
    for comp in capped.components:
        if comp.name.startswith("magnitude"):
            assert comp.points == pytest.approx(comp.max_points)


# ---------------------------------------------------------------------------
# Score boundaries
# ---------------------------------------------------------------------------


def test_maximum_score_is_exactly_100() -> None:
    full = {w: WINDOW_FULL_SCALE[w] for w in WINDOWS}
    volume = np.r_[np.full(N_BARS - 5, 1e5), np.full(5, 2e5)]
    result = score(with_tail(full), volume=volume)
    assert result.direction == "UP"
    assert result.status == "OK"
    assert result.score == 100.0
    assert result.timeframe_confirmation == "FULL"
    assert result.volume_state == "CONFIRMED"


def test_minimum_score_is_exactly_zero_for_a_flat_tape() -> None:
    result = score(flat())
    assert result.score == 0.0
    assert result.direction == "NEUTRAL"
    assert result.timeframe_confirmation == "NONE"


def test_down_moves_score_the_same_as_mirrored_up_moves() -> None:
    up = {1: 0.002, 5: 0.004, 10: 0.006, 15: 0.008}
    down = {w: -r for w, r in up.items()}
    a, b = score(with_tail(up)), score(with_tail(down))
    assert (a.direction, b.direction) == ("UP", "DOWN")
    assert a.score == pytest.approx(b.score, abs=0.5)  # log asymmetry only


def test_score_is_always_within_bounds_for_extreme_but_valid_inputs() -> None:
    rng = np.random.default_rng(3)
    for _ in range(50):
        closes = 100 * np.exp(np.cumsum(rng.normal(0, 0.003, N_BARS)))
        volume = np.exp(rng.normal(11, 1.0, N_BARS))
        result = score(closes, volume)
        if result.score is not None:
            assert 0.0 <= result.score <= 100.0


def test_score_label_says_it_is_not_a_probability() -> None:
    assert SCORE_TYPE == "momentum_strength_0_100_not_a_probability"
    assert score(flat()).score_type == SCORE_TYPE


# ---------------------------------------------------------------------------
# Direction labels and boundaries
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("returns", "expected"),
    [
        ({1: 0.001, 5: 0.002, 10: 0.003, 15: 0.004}, "UP"),
        ({1: -0.001, 5: -0.002, 10: -0.003, 15: -0.004}, "DOWN"),
        ({1: 0.0, 5: 0.0, 10: 0.0, 15: 0.0}, "NEUTRAL"),
        ({1: 0.001, 5: -0.002, 10: 0.003, 15: -0.004}, "MIXED"),
        ({1: 0.002, 5: 0.002, 10: -0.002, 15: -0.002}, "MIXED"),
        # One short-term wobble against a strong trend is still UP (weight share 50/60).
        ({1: -0.001, 5: 0.002, 10: 0.003, 15: 0.004}, "UP"),
        # The 5m window carries more weight: opposing it drops the share to 40/60.
        ({1: 0.001, 5: -0.002, 10: 0.003, 15: 0.004}, "MIXED"),
        # Exactly 75% of the weight (10m opposes: 45/60) is enough.
        ({1: 0.001, 5: 0.002, 10: -0.003, 15: 0.004}, "UP"),
    ],
)
def test_direction_labels(returns, expected) -> None:
    assert classify_direction(returns)[0] == expected


def test_flat_band_boundary_is_inclusive_and_float_safe() -> None:
    band = MomentumConfig().flat_band
    assert classify_direction({1: band, 5: band})[0] == "NEUTRAL"
    assert classify_direction({1: -band, 5: -band})[0] == "NEUTRAL"
    assert classify_direction({1: band * 1.01, 5: band * 1.01})[0] == "UP"
    assert classify_direction({1: -band * 1.01, 5: -band * 1.01})[0] == "DOWN"
    # A flat window never votes: UP rests on the non-flat window alone.
    assert classify_direction({1: 0.0, 5: 0.003})[0] == "UP"


def test_direction_share_boundary_follows_the_config() -> None:
    returns = {1: 0.001, 5: 0.002, 10: -0.003, 15: 0.004}  # exactly 0.75
    assert classify_direction(returns, MomentumConfig(direction_share=0.75))[0] == "UP"
    assert classify_direction(returns, MomentumConfig(direction_share=0.76))[0] == "MIXED"


def test_no_windows_means_neutral_not_a_guess() -> None:
    direction, agreeing, available, share = classify_direction({w: None for w in WINDOWS})
    assert (direction, agreeing, available, share) == ("NEUTRAL", 0, 0, 0.0)


def test_mixed_direction_gets_no_confirmation_or_volume_credit() -> None:
    returns = {1: 0.004, 5: -0.004, 10: 0.0, 15: 0.0}
    volume = np.r_[np.full(N_BARS - 5, 1e5), np.full(5, 3e5)]
    result = score(with_tail(returns), volume=volume)
    assert result.direction == "MIXED"
    by_name = {c.name: c for c in result.components}
    assert by_name["confirmation"].points == 0.0
    assert by_name["volume"].points == 0.0  # surge is reported but not a confirmation
    assert result.volume_state == "CONFIRMED"
    assert result.timeframe_confirmation == "NONE"


def test_opposing_windows_earn_no_magnitude_points() -> None:
    result = score(with_tail({1: -0.004, 5: 0.004, 10: 0.006, 15: 0.008}), volume=None)
    assert result.direction == "UP"
    by_name = {c.name: c for c in result.components}
    assert by_name["magnitude_1m"].points == 0.0
    assert "not with the dominant side" in by_name["magnitude_1m"].detail
    assert result.timeframe_confirmation == "PARTIAL"
    assert result.agreeing_windows == 3 and result.available_windows == 4


# ---------------------------------------------------------------------------
# Volume confirmation
# ---------------------------------------------------------------------------


def volume_series(recent_ratio: float, baseline: float = 1e5) -> np.ndarray:
    return np.r_[np.full(N_BARS - 5, baseline), np.full(5, baseline * recent_ratio)]


@pytest.mark.parametrize(
    ("ratio", "state"),
    [
        (2.0, "CONFIRMED"),
        (1.5, "CONFIRMED"),
        (1.4999, "NORMAL"),
        (1.0, "NORMAL"),
        (0.8, "NORMAL"),
        (0.7999, "WEAK"),
        (0.2, "WEAK"),
    ],
)
def test_volume_state_boundaries(ratio, state) -> None:
    value, label = volume_confirmation(bars(flat(), volume_series(ratio)))
    assert label == state
    assert value == pytest.approx(ratio, rel=1e-9)


@pytest.mark.parametrize(
    ("ratio", "points"), [(1.0, 0.0), (1.5, 10.0), (2.0, 20.0), (5.0, 20.0), (0.5, 0.0)]
)
def test_volume_points_are_linear_between_1x_and_the_full_ratio(ratio, points) -> None:
    closes = with_tail({w: WINDOW_FULL_SCALE[w] for w in WINDOWS})
    result = score(closes, volume=volume_series(ratio))
    volume = next(c for c in result.components if c.name == "volume")
    assert volume.points == pytest.approx(points, abs=1e-3)


def test_volume_baseline_excludes_the_recent_surge() -> None:
    # A huge surge in the recent bars must not inflate its own baseline.
    value, _ = volume_confirmation(bars(flat(), volume_series(10.0)))
    assert value == pytest.approx(10.0)


def test_volume_baseline_uses_the_median_so_one_spike_does_not_distort_it() -> None:
    volume = volume_series(1.0)
    volume[-10] = 1e9  # one-off block trade inside the baseline window
    value, label = volume_confirmation(bars(flat(), volume))
    assert value == pytest.approx(1.0) and label == "NORMAL"


@pytest.mark.parametrize(
    "volume",
    [None, 0.0, np.nan],
    ids=["no_column", "zero_volume_index", "nan_volume"],
)
def test_missing_volume_is_unavailable_and_the_score_is_rescaled_not_zeroed(volume) -> None:
    closes = with_tail({w: WINDOW_FULL_SCALE[w] for w in WINDOWS})
    result = score(closes, volume=volume)
    assert result.volume_state == "UNAVAILABLE" and result.volume_ratio is None
    assert result.status == "PARTIAL" and "volume_unavailable" in result.reasons
    assert result.score_coverage == pytest.approx(0.8)
    assert result.score == 100.0  # full evidence on everything that exists
    assert next(c for c in result.components if c.name == "volume").points is None


def test_too_little_session_history_for_a_volume_baseline_is_unavailable() -> None:
    result = score(with_tail({1: 0.002, 5: 0.004}, n=12), volume=1e5)
    assert result.volume_state == "UNAVAILABLE"


# ---------------------------------------------------------------------------
# Missing, stale, insufficient and invalid data
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("frame", [None, pd.DataFrame()], ids=["none", "empty"])
def test_no_data_gives_insufficient_and_no_score(frame) -> None:
    result = compute_momentum(frame, as_of=AS_OF, symbol="X")
    assert result.status == "INSUFFICIENT" and result.score is None
    assert result.reasons == ("no_data",) and not result.is_scored
    assert result.symbol == "X"


def test_missing_close_column_is_invalid() -> None:
    frame = bars(flat()).rename(columns={"Close": "Price"})
    result = compute_momentum(frame, as_of=AS_OF)
    assert result.status == "INVALID" and result.score is None
    assert "missing_close_column" in result.reasons


def test_single_bar_is_insufficient() -> None:
    result = score([100.0])
    assert result.status == "INSUFFICIENT" and result.score is None


def test_only_the_windows_that_fit_are_used_and_the_result_is_partial() -> None:
    closes = with_tail({1: 0.002, 5: 0.004}, n=8)  # 8 bars: 1m and 5m exist, 10m/15m do not
    result = score(closes, volume=None)
    assert result.returns[1] is not None and result.returns[5] is not None
    assert result.returns[10] is None and result.returns[15] is None
    assert result.window_notes[10] == "insufficient_history"
    assert result.status == "PARTIAL" and result.available_windows == 2
    assert any(r.startswith("windows_unavailable:10m,15m") for r in result.reasons)
    magnitude = [c for c in result.components if c.name in {"magnitude_10m", "magnitude_15m"}]
    assert all(c.points is None for c in magnitude)


def test_fewer_than_min_windows_is_insufficient_with_the_reason() -> None:
    result = score(with_tail({1: 0.002}, n=3), volume=None)  # only the 1m window fits
    assert result.status == "INSUFFICIENT" and result.score is None
    assert "only_1_of_4_windows" in result.reasons[0]
    assert compute_momentum(
        bars(with_tail({1: 0.002}, n=3), None), as_of=AS_OF, config=MomentumConfig(min_windows=1)
    ).is_scored


@pytest.mark.parametrize(
    ("age_seconds", "stale"),
    [(20, False), (180, False), (181, True), (900, True)],
)
def test_staleness_boundary_uses_the_age_of_the_latest_completed_bar(age_seconds, stale) -> None:
    # Bar 11:29 ends 11:30:00, so as_of = 11:30:00 + age.
    as_of = DAY.replace(hour=11, minute=30) + timedelta(seconds=age_seconds)
    result = compute_momentum(bars(np.linspace(100, 101, N_BARS)), as_of=as_of)
    assert result.data_age_seconds == pytest.approx(age_seconds)
    if stale:
        assert result.status == "STALE" and result.score is None
        assert result.direction == "NEUTRAL" and result.timeframe_confirmation == "NONE"
        assert result.last_bar_time == LAST
    else:
        assert result.is_scored


def test_stale_threshold_is_configurable() -> None:
    as_of = DAY.replace(hour=11, minute=30) + timedelta(seconds=60)
    result = compute_momentum(
        bars(np.linspace(100, 101, N_BARS)),
        as_of=as_of,
        config=MomentumConfig(stale_after_seconds=30),
    )
    assert result.status == "STALE"


def test_after_the_close_data_is_stale_not_presented_as_live() -> None:
    last = DAY.replace(hour=15, minute=29)
    frame = bars(np.linspace(100, 101, N_BARS), last=last)
    result = compute_momentum(frame, as_of=DAY.replace(hour=18, minute=0))
    assert result.status == "STALE" and result.score is None


def test_a_missing_minute_within_tolerance_still_finds_the_window_start() -> None:
    frame = bars(np.linspace(100, 101, N_BARS))
    target = frame.index[-1] - pd.Timedelta(minutes=5)
    reference = frame["Close"].loc[target - pd.Timedelta(minutes=1)]
    result = compute_momentum(frame.drop(index=target), as_of=AS_OF)
    assert result.returns[5] == pytest.approx(frame["Close"].iloc[-1] / reference - 1)


def test_a_gap_beyond_tolerance_makes_the_window_unavailable_not_stretched() -> None:
    frame = bars(np.linspace(100, 101, N_BARS))
    last = frame.index[-1]
    gap = [last - pd.Timedelta(minutes=m) for m in (5, 6, 7)]
    result = compute_momentum(frame.drop(index=gap), as_of=AS_OF)
    assert result.returns[5] is None and result.window_notes[5] == "missing_bar"
    assert result.returns[1] is not None and result.returns[15] is not None
    assert result.status == "PARTIAL"


def test_invalid_prices_are_removed_never_repaired() -> None:
    closes = np.linspace(100, 101, N_BARS)
    closes[-20] = np.nan
    closes[-30] = -5.0
    closes[-40] = 0.0
    closes[-50] = np.inf
    result = score(closes)
    assert any(r.startswith("dropped_invalid_prices:4") for r in result.reasons)
    assert result.is_scored
    assert result.returns[15] == pytest.approx(closes[-1] / closes[-16] - 1)


def test_all_invalid_prices_give_insufficient() -> None:
    result = score(np.full(N_BARS, np.nan))
    assert result.status == "INSUFFICIENT" and result.score is None


def test_a_bad_tick_in_a_window_start_is_flagged_not_scored() -> None:
    closes = flat().copy()
    closes[-6] = 40.0  # +150% over 5m would be a fantasy score
    result = score(closes)
    assert result.returns[5] is None and result.window_notes[5] == "unverified_extreme_move"
    assert result.returns[1] == pytest.approx(0.0)
    assert "windows_unavailable" in " ".join(result.reasons)


def test_non_numeric_close_values_are_treated_as_invalid() -> None:
    frame = bars(np.linspace(100, 101, N_BARS)).astype({"Close": object})
    frame.iloc[-20, frame.columns.get_loc("Close")] = "n/a"
    assert score_from_frame(frame).is_scored


def score_from_frame(frame):
    return compute_momentum(frame, as_of=AS_OF)


def test_duplicate_timestamps_keep_the_last_and_unsorted_input_is_sorted() -> None:
    frame = bars(np.linspace(100, 101, N_BARS))
    shuffled = pd.concat([frame, frame.iloc[[-1]].assign(Close=101.5)]).iloc[::-1]
    expected = compute_momentum(
        pd.concat([frame.iloc[:-1], frame.iloc[[-1]].assign(Close=101.5)]), as_of=AS_OF
    )
    result = score_from_frame(shuffled)
    assert result.returns == expected.returns


def test_bars_from_a_previous_day_are_not_used_for_intraday_windows() -> None:
    today = bars(np.linspace(100, 101, 4), last=LAST)  # only 4 bars today
    yesterday = bars(np.full(60, 50.0), last=LAST - timedelta(days=1))
    result = compute_momentum(pd.concat([yesterday, today]), as_of=AS_OF)
    assert result.returns[5] is None  # would be +100% against yesterday's 50.0
    assert result.returns[1] == pytest.approx(today["Close"].iloc[-1] / today["Close"].iloc[-2] - 1)


def test_previous_day_volume_never_forms_todays_volume_baseline() -> None:
    today = bars(np.linspace(100, 101, 8), volume=1e5, last=LAST)  # too few bars for a baseline
    yesterday = bars(np.full(60, 100.0), volume=1e5, last=LAST - timedelta(days=1))
    result = compute_momentum(pd.concat([yesterday, today]), as_of=AS_OF)
    assert result.volume_state == "UNAVAILABLE" and result.volume_ratio is None
    assert "volume_unavailable" in result.reasons


def test_timezone_handling_naive_is_ist_and_utc_is_converted() -> None:
    aware = bars(np.linspace(100, 101, N_BARS))
    naive = aware.tz_localize(None)
    utc = aware.tz_convert("UTC")
    expected = compute_momentum(aware, as_of=AS_OF)
    for frame in (naive, utc):
        assert compute_momentum(frame, as_of=AS_OF).returns == expected.returns
    naive_now = AS_OF.replace(tzinfo=None)
    assert compute_momentum(aware, as_of=naive_now).returns == expected.returns


# ---------------------------------------------------------------------------
# No look-ahead
# ---------------------------------------------------------------------------


def test_the_forming_bar_is_never_used() -> None:
    closes = np.linspace(100, 101, N_BARS)
    complete = bars(closes)
    forming = pd.concat(
        [complete, pd.DataFrame({"Close": [250.0], "Volume": [9e9]}, index=[LAST + BAR_ONE])]
    )
    as_of = LAST + BAR_ONE + timedelta(seconds=20)  # 11:30:20: bar 11:30 is still forming
    baseline = compute_momentum(complete, as_of=AS_OF)
    result = compute_momentum(forming, as_of=as_of)
    assert result.last_bar_time == LAST
    assert result.returns[1] == baseline.returns[1]
    assert any("dropped_incomplete_or_future_bars:1" in r for r in result.reasons)


BAR_ONE = timedelta(minutes=1)


def test_a_bar_becomes_usable_exactly_when_it_completes() -> None:
    closes = np.linspace(100, 101, N_BARS)
    frame = bars(closes, last=LAST + BAR_ONE)  # includes the 11:30 bar
    just_before = DAY.replace(hour=11, minute=30, second=59)
    just_after = DAY.replace(hour=11, minute=31, second=0)
    assert compute_momentum(frame, as_of=just_before).last_bar_time == LAST
    assert compute_momentum(frame, as_of=just_after).last_bar_time == LAST + BAR_ONE


def test_changing_any_bar_after_as_of_cannot_change_the_result() -> None:
    rng = np.random.default_rng(11)
    closes = 100 * np.exp(np.cumsum(rng.normal(0, 0.001, N_BARS + 30)))
    volume = np.exp(rng.normal(11, 0.3, N_BARS + 30))
    full = bars(closes, volume, last=LAST + timedelta(minutes=30))
    poisoned = full.copy()
    poisoned.loc[poisoned.index > LAST, ["Close", "Volume"]] = [9999.0, 1e12]
    a = compute_momentum(full, as_of=AS_OF)
    b = compute_momentum(poisoned, as_of=AS_OF)
    assert a == b


def test_replaying_the_past_matches_what_was_known_then() -> None:
    rng = np.random.default_rng(5)
    closes = 100 * np.exp(np.cumsum(rng.normal(0, 0.001, N_BARS)))
    volume = np.exp(rng.normal(11, 0.3, N_BARS))
    full = bars(closes, volume)
    earlier_as_of = AS_OF - timedelta(minutes=20)
    truncated = full[full.index + BAR_ONE <= pd.Timestamp(earlier_as_of)]
    replayed = compute_momentum(full, as_of=earlier_as_of)
    known_then = compute_momentum(truncated, as_of=earlier_as_of)
    # The only legitimate difference is the informational note that later bars were ignored.
    assert any(r.startswith("dropped_incomplete_or_future_bars") for r in replayed.reasons)
    assert dataclasses.replace(replayed, reasons=()) == dataclasses.replace(known_then, reasons=())
    assert replayed.score == known_then.score and replayed.status == known_then.status


# ---------------------------------------------------------------------------
# Determinism, purity and batch behaviour
# ---------------------------------------------------------------------------


def test_results_are_deterministic_and_the_input_is_not_modified() -> None:
    frame = bars(np.linspace(100, 101, N_BARS), volume_series(1.7))
    snapshot = frame.copy(deep=True)
    first = compute_momentum(frame, as_of=AS_OF)
    second = compute_momentum(frame, as_of=AS_OF)
    assert first == second
    pd.testing.assert_frame_equal(frame, snapshot)


def test_batch_matches_single_calls_and_isolates_bad_symbols() -> None:
    good = bars(np.linspace(100, 101, N_BARS), volume_series(2.0))
    frames = {
        "GOOD.NS": good,
        "EMPTY.NS": pd.DataFrame(),
        "NONE.NS": None,
        "NOCLOSE.NS": good.rename(columns={"Close": "Last"}),
        "STALE.NS": bars(np.linspace(100, 101, N_BARS), last=LAST - timedelta(minutes=30)),
    }
    results = compute_momentum_batch(frames, as_of=AS_OF)
    assert list(results) == list(frames)
    assert results["GOOD.NS"] == compute_momentum(good, as_of=AS_OF, symbol="GOOD.NS")
    assert [results[k].status for k in frames] == [
        "OK",
        "INSUFFICIENT",
        "INSUFFICIENT",
        "INVALID",
        "STALE",
    ]
    assert results["GOOD.NS"].symbol == "GOOD.NS"


def test_batch_resolves_one_shared_as_of() -> None:
    frames = {f"S{i}.NS": bars(np.linspace(100, 101, N_BARS)) for i in range(5)}
    results = compute_momentum_batch(frames)  # default now(IST): data is old, so all stale
    assert {r.as_of for r in results.values()} == {next(iter(results.values())).as_of}
    assert {r.status for r in results.values()} == {"STALE"}


def test_a_large_watchlist_scores_quickly() -> None:
    rng = np.random.default_rng(1)
    frames = {
        f"S{i}.NS": bars(
            100 * np.exp(np.cumsum(rng.normal(0, 0.001, 375))), np.exp(rng.normal(11, 0.3, 375))
        )
        for i in range(500)
    }
    import time

    started = time.perf_counter()
    results = compute_momentum_batch(frames, as_of=AS_OF)
    elapsed = time.perf_counter() - started
    assert len(results) == 500 and all(r.is_scored for r in results.values())
    assert elapsed < 10.0  # generous ceiling; guards against accidental O(n^2) work


def test_to_dict_is_display_ready() -> None:
    row = score(np.linspace(100, 110, N_BARS), volume_series(2.0), symbol="ABC.NS").to_dict()
    assert row["Symbol"] == "ABC.NS" and row["Status"] == "OK"
    assert row["Direction"] == "UP" and row["Agreeing windows"] == "4/4"
    assert {"1m %", "5m %", "10m %", "15m %", "Momentum score", "Volume state"} <= set(row)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"flat_band": 0.0},
        {"direction_share": 0.5},
        {"direction_share": 1.1},
        {"min_windows": 0},
        {"min_windows": 5},
        {"stale_after_seconds": float("nan")},
        {"volume_weak_ratio": 2.0},
        {"volume_full_ratio": 1.0},
        {"volume_recent_minutes": 0},
    ],
)
def test_invalid_configuration_is_rejected(kwargs) -> None:
    with pytest.raises(ValueError):
        MomentumConfig(**kwargs)
