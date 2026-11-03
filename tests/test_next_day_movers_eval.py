"""Tests for the next-business-day walk-forward evaluation (leakage, costs, metrics)."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from algorithmic_trading.trading_costs import IndiaEquityCostModel
from scanner.next_day_movers import Instrument, ScannerConfig
from scanner.next_day_movers_eval import (
    EvalConfig,
    EvaluationDataError,
    _pooled_precision,
    _series_row,
    block_bootstrap_ci,
    build_evaluation_panel,
    build_folds,
    default_intraday_cost_model,
    evaluate_from_provider,
    round_trip_cost_fraction,
    run_walk_forward,
)
from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES

END = date(2026, 11, 3)
N_DAYS = 420


def ar_frame(seed: int, phi: float, n: int = N_DAYS, price0: float = 500.0) -> pd.DataFrame:
    """Daily bars whose close-to-close returns follow an AR(1) process (phi=0: random walk)."""
    rng = np.random.default_rng(seed)
    index = pd.bdate_range(end=END, periods=n)
    eps = rng.normal(0.0, 0.015, n)
    returns = np.zeros(n)
    for i in range(1, n):
        returns[i] = phi * returns[i - 1] + eps[i]
    close = price0 * np.cumprod(1.0 + returns)
    prev_close = np.r_[price0, close[:-1]]
    open_ = prev_close * (1.0 + rng.normal(0.0, 0.0005, n))
    high = np.maximum(open_, close) * (1.0 + np.abs(rng.normal(0.0, 0.003, n)))
    low = np.minimum(open_, close) * (1.0 - np.abs(rng.normal(0.0, 0.003, n)))
    volume = 1_000_000.0 * np.exp(rng.normal(0.0, 0.3, n))
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=index
    )


def market(phi: float, n_symbols: int = 30, seed0: int = 100):
    symbols = NSE_CANDIDATES[:n_symbols]
    instruments = {f"{s}.NS": Instrument(s, "NSE") for s in symbols}
    frames = {t: ar_frame(seed0 + i, phi) for i, t in enumerate(instruments)}
    benchmark = ar_frame(seed0 + 999, 0.0, price0=24000.0)
    benchmark["Volume"] = 0.0
    return frames, instruments, {"NSE": benchmark}


def quick_config(**overrides) -> EvalConfig:
    base = {"top_k": 5, "bootstrap_samples": 400}
    base.update(overrides)
    return EvalConfig(**base)


# --------------------------------------------------------------------------- leakage


def test_outcomes_use_the_next_market_session_including_weekends() -> None:
    frames, instruments, benchmarks = market(0.0, n_symbols=4)
    panel, index_outcomes, _ = build_evaluation_panel(
        frames, instruments, benchmarks, ScannerConfig()
    )
    ticker = "RELIANCE.NS"
    frame = frames[ticker]
    friday = next(d for d in frame.index[100:] if d.weekday() == 4)
    monday = frame.index[frame.index.get_loc(friday) + 1]
    assert monday.weekday() == 0
    row = panel.loc[(friday, ticker)]
    assert row["o2c"] == pytest.approx(frame.loc[monday, "Close"] / frame.loc[monday, "Open"] - 1)
    assert row["c2c"] == pytest.approx(frame.loc[monday, "Close"] / frame.loc[friday, "Close"] - 1)
    idx = benchmarks["NSE"]
    assert index_outcomes.loc[friday, "o2c"] == pytest.approx(
        idx.loc[monday, "Close"] / idx.loc[monday, "Open"] - 1
    )
    last = frame.index[-1]
    assert np.isnan(panel.loc[(last, ticker), "o2c"])  # no next session yet


def test_missing_next_bar_gives_no_outcome_instead_of_a_later_bar() -> None:
    frames, instruments, benchmarks = market(0.0, n_symbols=4)
    ticker = "TCS.NS"
    day = frames[ticker].index[200]
    suspended = frames[ticker].drop(frames[ticker].index[201])  # other symbols still trade
    frames[ticker] = suspended
    panel, _, _ = build_evaluation_panel(frames, instruments, benchmarks, ScannerConfig())
    assert np.isnan(panel.loc[(day, ticker), "o2c"])
    assert np.isnan(panel.loc[(day, ticker), "c2c"])
    assert not np.isnan(panel.loc[(day, "INFY.NS"), "o2c"])


def test_features_and_eligibility_ignore_everything_after_the_decision_date() -> None:
    frames, instruments, benchmarks = market(0.0, n_symbols=6)
    base, _, _ = build_evaluation_panel(frames, instruments, benchmarks, ScannerConfig())
    altered_frames = {}
    for ticker, frame in frames.items():
        altered = frame.copy()
        altered.iloc[-15:, :4] *= 2.5
        altered.iloc[-15:, 4] *= 40.0
        altered_frames[ticker] = altered
    changed, _, _ = build_evaluation_panel(altered_frames, instruments, benchmarks, ScannerConfig())

    cutoff = frames["TCS.NS"].index[-16]  # last unaltered decision date
    outcome_columns = ["o2c", "c2c"]
    feature_columns = [c for c in base.columns if c not in outcome_columns]
    before = base.loc[base.index.get_level_values("date") <= cutoff, feature_columns]
    after = changed.loc[changed.index.get_level_values("date") <= cutoff, feature_columns]
    pd.testing.assert_frame_equal(before, after)
    # The close-to-close outcome on the cutoff date legitimately changes: it is the *next*
    # session. (Open-to-close is unchanged because every price was scaled by the same factor.)
    assert base.loc[(cutoff, "TCS.NS"), "c2c"] != pytest.approx(
        changed.loc[(cutoff, "TCS.NS"), "c2c"]
    )


def test_selections_on_past_dates_do_not_depend_on_later_prices() -> None:
    frames, instruments, benchmarks = market(0.0, n_symbols=14)
    config = quick_config()
    original = run_walk_forward(frames, instruments, benchmarks, config)
    altered_frames = {}
    for ticker, frame in frames.items():
        altered = frame.copy()
        altered.iloc[-20:, :4] *= 3.0
        altered_frames[ticker] = altered
    altered_result = run_walk_forward(altered_frames, instruments, benchmarks, config)
    safe_until = frames["TCS.NS"].index[-22]  # next-day outcome of this date is still unaltered
    shared = original.daily.index[original.daily.index <= safe_until]
    assert len(shared) > 100
    pd.testing.assert_series_equal(
        original.daily.loc[shared, "score_picks"], altered_result.daily.loc[shared, "score_picks"]
    )
    pd.testing.assert_series_equal(
        original.daily.loc[shared, "score_o2c"], altered_result.daily.loc[shared, "score_o2c"]
    )


# --------------------------------------------------------------------------- edge detection


def test_pipeline_detects_a_planted_next_day_signal() -> None:
    frames, instruments, benchmarks = market(0.4)
    result = run_walk_forward(frames, instruments, benchmarks, quick_config())
    assert result.assessment["edge_supported"] is True
    assert result.assessment["net_excess_vs_universe_ci95_bps"][0] > 0
    quintiles = result.quintiles
    assert quintiles.loc[5, "mean_o2c_bps"] > quintiles.loc[1, "mean_o2c_bps"]
    precision = result.assessment["precision"]
    assert (
        precision["Score top-k precision (open->close, gross)"]
        > precision["Universe base rate (open->close, gross)"]
    )


def test_pipeline_reports_no_edge_on_random_walks_after_costs() -> None:
    frames, instruments, benchmarks = market(0.0)
    result = run_walk_forward(frames, instruments, benchmarks, quick_config())
    assert result.assessment["edge_supported"] is False
    assert "No evidence of a predictive edge" in result.assessment["verdict"]
    assert result.assessment["mean_net_return_bps"] < 0
    assert result.assessment["checks"]["net_return_positive"] is False


def test_random_walks_without_costs_do_not_clear_the_pre_registered_rule() -> None:
    frames, instruments, benchmarks = market(0.0, seed0=500)
    free = quick_config(cost_model=IndiaEquityCostModel())
    result = run_walk_forward(frames, instruments, benchmarks, free)
    assert result.round_trip_cost_bps == 0.0
    assert result.assessment["edge_supported"] is False


# --------------------------------------------------------------------------- costs and metrics


def test_costs_are_deducted_from_open_to_close_returns() -> None:
    frames, instruments, benchmarks = market(0.0, n_symbols=14)
    config = quick_config(cost_model=IndiaEquityCostModel(slippage_bps=10.0))
    assert round_trip_cost_fraction(config.cost_model) == pytest.approx(0.002)
    result = run_walk_forward(frames, instruments, benchmarks, config)
    gross = result.summary.loc["Score top-k, gross (open->close)", "mean_bps"]
    net = result.summary.loc["Score top-k, net of costs (open->close)", "mean_bps"]
    assert gross - net == pytest.approx(20.0, abs=1e-6)


def test_default_cost_model_includes_brokerage_taxes_and_slippage() -> None:
    model = default_intraday_cost_model()
    assert model.slippage_bps > 0 and model.stt_sell_bps > 0 and model.brokerage_bps > 0
    assert 0.0005 < round_trip_cost_fraction(model) < 0.005


def test_metrics_match_hand_computed_values() -> None:
    benchmark = pd.Series([0.0, 0.0, 0.0])
    row = _series_row("s", pd.Series([0.01, -0.02, 0.01]), benchmark)
    assert row["days"] == 3
    assert row["mean_bps"] == pytest.approx(0.0, abs=1e-9)
    assert row["day_hit_rate"] == pytest.approx(2 / 3)
    assert row["cumulative_return"] == pytest.approx(1.01 * 0.98 * 1.01 - 1)
    assert row["max_drawdown"] == pytest.approx(0.98 / 1.0 - 1, abs=1e-9)

    daily = pd.DataFrame(
        {
            "score_o2c_pos": [3, 1],
            "score_o2c_valid": [5, 5],
            "universe_o2c_pos": [10, 12],
            "universe_o2c_valid": [20, 20],
        }
    )
    assert _pooled_precision(daily, "score", "o2c") == pytest.approx(0.4)
    assert _pooled_precision(daily, "universe", "o2c") == pytest.approx(0.55)


def test_block_bootstrap_interval_behaviour() -> None:
    rng = np.random.default_rng(3)
    noise = rng.normal(0.0, 1.0, 600)
    low, high = block_bootstrap_ci(noise, block=5, samples=500, seed=1)
    assert low < noise.mean() < high
    assert low < 0.0 < high
    shifted_low, _ = block_bootstrap_ci(noise + 1.0, block=5, samples=500, seed=1)
    assert shifted_low > 0.0
    assert all(np.isnan(v) for v in block_bootstrap_ci(np.ones(6), block=5, samples=500, seed=1))
    assert block_bootstrap_ci(noise, block=5, samples=500, seed=9) == block_bootstrap_ci(
        noise, block=5, samples=500, seed=9
    )


def test_folds_are_sequential_non_overlapping_and_cover_all_dates() -> None:
    index = pd.bdate_range("2025-01-01", periods=100)
    rng = np.random.default_rng(0)
    daily = pd.DataFrame(
        {
            "score_o2c": rng.normal(0, 0.01, 100),
            "universe_o2c": rng.normal(0, 0.01, 100),
            "index_o2c": rng.normal(0, 0.01, 100),
            "score_o2c_pos": 3,
            "score_o2c_valid": 5,
            "universe_o2c_pos": 10,
            "universe_o2c_valid": 20,
        },
        index=index,
    )
    folds = build_folds(daily, EvalConfig(n_splits=5))
    assert folds["days"].tolist() == [20] * 5
    starts = pd.to_datetime(folds["start"])
    ends = pd.to_datetime(folds["end"])
    assert (starts.iloc[1:].to_numpy() > ends.iloc[:-1].to_numpy()).all()
    assert folds["days"].sum() == 100


# --------------------------------------------------------------------------- coverage and reporting


def test_result_reports_sample_coverage_and_limitations() -> None:
    frames, instruments, benchmarks = market(0.0, n_symbols=14)
    result = run_walk_forward(frames, instruments, benchmarks, quick_config())
    coverage = result.coverage
    assert coverage["symbols_requested"] == coverage["symbols_used"] == 14
    assert coverage["dates_evaluated"] == len(result.daily)
    assert coverage["dates_skipped"]["too_few_eligible"] > 0  # warm-up period
    assert coverage["pick_outcomes_valid_share"] == pytest.approx(1.0)
    assert coverage["benchmark_available"] is True
    assert result.assessment["rule"]
    assert any("Survivorship" in item for item in result.limitations)
    assert result.disclaimer.startswith("Research and paper-trading use only")
    for label in (
        "Score top-k, net of costs (open->close)",
        "Momentum-5d top-k, net of costs (open->close)",
        "Equal-weight eligible universe, gross (open->close)",
        "Index, gross (open->close)",
    ):
        assert label in result.summary.index
    assert {"mean_excess_vs_index_bps", "max_drawdown", "day_hit_rate"} <= set(
        result.summary.columns
    )


def test_evaluation_is_deterministic() -> None:
    frames, instruments, benchmarks = market(0.0, n_symbols=14)
    first = run_walk_forward(frames, instruments, benchmarks, quick_config())
    second = run_walk_forward(frames, instruments, benchmarks, quick_config())
    pd.testing.assert_frame_equal(first.summary, second.summary)
    assert first.assessment["net_excess_vs_universe_ci95_bps"] == pytest.approx(
        second.assessment["net_excess_vs_universe_ci95_bps"]
    )


def test_missing_benchmark_is_reported_and_does_not_crash() -> None:
    frames, instruments, _ = market(0.0, n_symbols=14)
    result = run_walk_forward(frames, instruments, {}, quick_config())
    assert result.coverage["benchmark_available"] is False
    assert np.isnan(result.summary.loc["Index, gross (open->close)", "mean_bps"])


def test_bse_instruments_use_the_bse_benchmark() -> None:
    instruments = {
        f"S{i}.BO": Instrument(code, "BSE") for i, code in enumerate(BSE_CANDIDATES[:14])
    }
    frames = {t: ar_frame(300 + i, 0.0) for i, t in enumerate(instruments)}
    benchmark = ar_frame(399, 0.0, price0=80000.0)
    benchmark["Volume"] = 0.0
    result = run_walk_forward(frames, instruments, {"BSE": benchmark}, quick_config())
    assert result.coverage["benchmark_available"] is True
    assert result.coverage["symbols_used"] == 14


def test_too_little_history_raises_instead_of_reporting_empty_statistics() -> None:
    frames = {f"{s}.NS": ar_frame(i, 0.0, n=40) for i, s in enumerate(NSE_CANDIDATES[:14])}
    instruments = {f"{s}.NS": Instrument(s, "NSE") for s in NSE_CANDIDATES[:14]}
    with pytest.raises(ValueError, match="no evaluable dates"):
        run_walk_forward(frames, instruments, {}, quick_config())
    with pytest.raises(EvaluationDataError):
        run_walk_forward({}, instruments, {}, quick_config())


def test_invalid_and_unusable_histories_are_dropped_with_reasons() -> None:
    frames, instruments, benchmarks = market(0.0, n_symbols=14)
    frames["TCS.NS"] = pd.DataFrame()
    broken = frames["INFY.NS"].copy()
    broken.iloc[-30:, broken.columns.get_loc("Close")] = np.nan
    frames["INFY.NS"] = broken
    result = run_walk_forward(frames, instruments, benchmarks, quick_config())
    assert set(result.coverage["symbols_dropped"]) == {"TCS.NS", "INFY.NS"}
    assert result.coverage["symbols_used"] == 12


# --------------------------------------------------------------------------- provider boundary


def test_provider_failure_is_reported_as_typed_error() -> None:
    def broken(_tickers):
        raise TimeoutError("provider timeout")

    with pytest.raises(EvaluationDataError, match="TimeoutError"):
        evaluate_from_provider(quick_config(), universe=[("TCS", "NSE")], fetcher=broken)


def test_empty_provider_response_is_reported() -> None:
    empty = lambda tickers: ({}, {"requested": len(tickers)})  # noqa: E731
    with pytest.raises(EvaluationDataError, match="no usable stock history"):
        evaluate_from_provider(quick_config(), universe=[("TCS", "NSE")], fetcher=empty)


def test_evaluate_from_provider_runs_end_to_end_with_injected_fetcher() -> None:
    frames, instruments, benchmarks = market(0.0, n_symbols=14)
    provider_frames = {**frames, "^NSEI": benchmarks["NSE"]}

    def fetch(tickers):
        return {t: provider_frames[t] for t in tickers if t in provider_frames}, {"usable": 1}

    result = evaluate_from_provider(
        quick_config(),
        universe=[(i.symbol, "NSE") for i in instruments.values()],
        fetcher=fetch,
    )
    assert result.coverage["symbols_used"] == 14
    assert result.coverage["benchmark_available"] is True
