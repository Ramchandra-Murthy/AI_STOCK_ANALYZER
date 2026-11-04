"""Validation tests for the next-day scanner: live shortlist correctness, calendar/session
boundaries, live-vs-evaluation parity, look-ahead, costs and bad-data handling.

All data is synthetic and injected, so nothing here contacts a market-data provider and none
of it says anything about real-world accuracy.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from algorithmic_trading.trading_costs import IndiaEquityCostModel
from scanner.next_day_movers import (
    DATA_SOURCE,
    Instrument,
    ScannerConfig,
    add_relative_strength,
    build_universe,
    calendar_conflicts,
    clean_ohlcv,
    clean_ohlcv_history,
    compute_feature_frame,
    rankable,
    resolve_prediction_cutoff,
    scan_next_day_movers,
    score_panel,
    ticker_for,
    unreliable_record_flags,
)
from scanner.next_day_movers_eval import (
    EvalConfig,
    build_evaluation_panel,
    default_intraday_cost_model,
    round_trip_cost_fraction,
    run_walk_forward,
)
from scanner.universe import BSE_CANDIDATES, NSE_CANDIDATES
from services.market_calendar import (
    CalendarUnavailableError,
    is_equity_trading_day,
    next_equity_trading_day,
    previous_equity_trading_day,
)

IST = ZoneInfo("Asia/Kolkata")
CUTOFF = date(2026, 11, 3)  # Tuesday, a regular session
NOW = datetime(2026, 11, 3, 17, 30, tzinfo=IST)
SYMBOLS = NSE_CANDIDATES[:16]


def frame(
    seed: int,
    n: int = 220,
    end: date = CUTOFF,
    price0: float = 500.0,
    base_volume: float = 1_000_000.0,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    index = pd.bdate_range(end=end, periods=n)
    close = price0 * np.exp(np.cumsum(rng.normal(0.0, 0.012, n)))
    open_ = np.r_[price0, close[:-1]] * (1 + rng.normal(0, 0.003, n))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.004, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.004, n)))
    volume = base_volume * np.exp(rng.normal(0, 0.3, n))
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=index
    )


def market(end: date = CUTOFF, symbols: list[str] | None = None) -> dict[str, pd.DataFrame]:
    names = symbols or SYMBOLS
    frames = {f"{s}.NS": frame(i, end=end, price0=200.0 + 40 * i) for i, s in enumerate(names)}
    frames["^NSEI"] = frame(900, end=end, price0=24000.0, base_volume=0.0)
    return frames


def fetcher_for(frames: dict[str, pd.DataFrame]):
    calls: list[list[str]] = []

    def fetch(tickers: list[str]):
        calls.append(list(tickers))
        usable = {t: frames[t] for t in tickers if t in frames}
        return usable, {"requested": len(tickers), "usable": len(usable)}

    fetch.calls = calls  # type: ignore[attr-defined]
    return fetch


def config(**overrides) -> ScannerConfig:
    base = {"exchanges": ("NSE",), "top_n": 5, "check_surveillance": False}
    base.update(overrides)
    return ScannerConfig(**base)


def scan(frames, now=NOW, cfg=None, universe=None, fetcher=None):
    return scan_next_day_movers(
        cfg or config(),
        now=now,
        universe=universe or [(s, "NSE") for s in SYMBOLS],
        fetcher=fetcher or fetcher_for(frames),
    )


# ======================================================================================
# Market calendar and session boundaries
# ======================================================================================


def at(day: date, hour: int, minute: int = 0, second: int = 0) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute, second, tzinfo=IST)


@pytest.mark.parametrize(
    ("label", "now", "cutoff", "target"),
    [
        ("pre-market", at(date(2026, 11, 3), 8, 59), date(2026, 11, 2), date(2026, 11, 3)),
        ("at the open", at(date(2026, 11, 3), 9, 15), date(2026, 11, 2), date(2026, 11, 3)),
        ("mid-session", at(date(2026, 11, 3), 12, 0), date(2026, 11, 2), date(2026, 11, 3)),
        ("at the close", at(date(2026, 11, 3), 15, 30), date(2026, 11, 2), date(2026, 11, 3)),
        ("inside buffer", at(date(2026, 11, 3), 15, 44, 59), date(2026, 11, 2), date(2026, 11, 3)),
        ("buffer edge", at(date(2026, 11, 3), 15, 45), date(2026, 11, 3), date(2026, 11, 4)),
        ("after hours", at(date(2026, 11, 3), 23, 59), date(2026, 11, 3), date(2026, 11, 4)),
        ("Saturday", at(date(2026, 11, 7), 11, 0), date(2026, 11, 6), date(2026, 11, 9)),
        ("Sunday", at(date(2026, 11, 8), 20, 0), date(2026, 11, 6), date(2026, 11, 9)),
        ("Friday evening", at(date(2026, 11, 6), 19, 0), date(2026, 11, 6), date(2026, 11, 9)),
        # 10 Nov 2026 is a configured holiday: the target skips it.
        ("before holiday", at(date(2026, 11, 9), 18, 0), date(2026, 11, 9), date(2026, 11, 11)),
        ("on holiday", at(date(2026, 11, 10), 18, 0), date(2026, 11, 9), date(2026, 11, 11)),
        # 25 Dec 2026 (Friday) holiday: Thursday evening targets the next Monday.
        ("Christmas", at(date(2026, 12, 25), 18, 0), date(2026, 12, 24), date(2026, 12, 28)),
    ],
)
def test_cutoff_and_target_across_session_boundaries(label, now, cutoff, target) -> None:
    assert resolve_prediction_cutoff(now) == (cutoff, target), label


def test_cutoff_is_never_the_target_and_target_is_always_a_trading_day() -> None:
    start = datetime(2026, 10, 1, 0, 0, tzinfo=IST)
    for hours in range(0, 24 * 85, 5):
        now = start + timedelta(hours=hours)
        cutoff, target = resolve_prediction_cutoff(now)
        assert cutoff < target
        assert is_equity_trading_day(cutoff) and is_equity_trading_day(target)
        assert next_equity_trading_day(cutoff) == target
        # A cutoff is a completed session: its settled close is not in the future.
        assert datetime.combine(cutoff, datetime.min.time(), IST) <= now


def test_zero_buffer_uses_the_close_itself() -> None:
    cfg = config(close_buffer_minutes=0)
    assert resolve_prediction_cutoff(at(date(2026, 11, 3), 15, 30), cfg)[0] == CUTOFF
    assert resolve_prediction_cutoff(at(date(2026, 11, 3), 15, 29), cfg)[0] == date(2026, 11, 2)


@pytest.mark.parametrize(
    "now",
    [
        at(date(2026, 12, 31), 18, 0),  # target would be 1 Jan 2027
        at(date(2027, 1, 4), 18, 0),
        at(date(2027, 6, 15), 18, 0),
    ],
)
def test_unconfigured_calendar_years_fail_closed_and_are_not_invented(now) -> None:
    with pytest.raises(CalendarUnavailableError):
        resolve_prediction_cutoff(now)
    result = scan(market(), now=now)
    assert result.status == "UNAVAILABLE"
    assert result.candidates == ()
    assert result.target_business_date is None
    assert any("calendar" in message.lower() for message in (*result.warnings, *result.errors))


def test_calendar_helpers_refuse_to_guess_for_unknown_years() -> None:
    for call in (
        is_equity_trading_day,
        next_equity_trading_day,
        previous_equity_trading_day,
    ):
        with pytest.raises(CalendarUnavailableError):
            call(date(2099, 3, 4))


def test_dec_30_still_resolves_because_the_target_is_inside_the_configured_year() -> None:
    assert resolve_prediction_cutoff(at(date(2026, 12, 30), 18, 0)) == (
        date(2026, 12, 30),
        date(2026, 12, 31),
    )


def test_session_on_a_day_the_calendar_marks_closed_makes_the_scan_unavailable() -> None:
    # Stocks traded on Saturday 7 Nov (e.g. a special session the calendar does not know).
    saturday = date(2026, 11, 7)
    friday = date(2026, 11, 6)
    frames = market(end=friday)
    for ticker, bars in list(frames.items()):
        if ticker.endswith(".NS"):
            extra = bars.iloc[[-1]].copy()
            extra.index = pd.DatetimeIndex([pd.Timestamp(saturday)])
            frames[ticker] = pd.concat([bars, extra])
    fetch = fetcher_for(frames)
    result = scan(frames, now=at(date(2026, 11, 8), 12, 0), fetcher=fetch)
    assert result.status == "UNAVAILABLE"
    assert result.candidates == ()
    assert any("Calendar conflict" in message for message in result.warnings)
    assert result.data_quality["calendar_conflicts"] == [saturday.isoformat()]


def test_isolated_or_zero_volume_bars_on_closed_days_are_not_a_calendar_conflict() -> None:
    friday = date(2026, 11, 6)
    saturday = date(2026, 11, 7)
    frames = market(end=friday)
    tickers = [f"{s}.NS" for s in SYMBOLS]

    def with_saturday(bars: pd.DataFrame, volume: float) -> pd.DataFrame:
        extra = bars.iloc[[-1]].copy()
        extra["Volume"] = volume
        extra.index = pd.DatetimeIndex([pd.Timestamp(saturday)])
        return pd.concat([bars, extra])

    # One stray stock bar (below the threshold) ...
    one = dict(frames)
    one[tickers[0]] = with_saturday(frames[tickers[0]], 1_000_000.0)
    assert calendar_conflicts(one, tickers, friday, date(2026, 11, 8)) == []
    # ... and many placeholder bars with zero volume.
    many = {t: with_saturday(frames[t], 0.0) if t in tickers else frames[t] for t in frames}
    assert calendar_conflicts(many, tickers, friday, date(2026, 11, 8)) == []
    result = scan(many, now=at(date(2026, 11, 8), 12, 0))
    assert result.status in {"OK", "DEGRADED"}
    assert result.target_business_date == date(2026, 11, 9)


def test_todays_partial_bar_is_neither_a_conflict_nor_used() -> None:
    # 11:00 on a trading day: the cutoff is the previous session; today's bar is partial.
    now = at(date(2026, 11, 3), 11, 0)
    frames = market(end=CUTOFF)
    clean_run = scan(frames, now=now)
    assert clean_run.status in {"OK", "DEGRADED"}
    assert clean_run.prediction_cutoff == datetime(2026, 11, 2, 15, 30, tzinfo=IST)
    assert {c.data_timestamp for c in clean_run.candidates} == {date(2026, 11, 2)}
    # Poisoning today's bar must not change the ranking.
    poisoned = {t: f.copy() for t, f in frames.items()}
    for bars in poisoned.values():
        bars.iloc[-1] = bars.iloc[-1] * 3.0
    again = scan(poisoned, now=now)
    assert [(c.ticker, c.score) for c in again.candidates] == [
        (c.ticker, c.score) for c in clean_run.candidates
    ]


# ======================================================================================
# Live shortlist correctness: timestamps, provenance, exclusions, statuses
# ======================================================================================


def test_shortlist_carries_cutoff_target_timestamp_and_source() -> None:
    result = scan(market())
    assert result.status == "OK"
    assert result.generated_at == NOW
    assert result.prediction_cutoff == datetime(2026, 11, 3, 15, 30, tzinfo=IST)
    assert result.target_business_date == date(2026, 11, 4)
    assert len(result.candidates) == 5
    for rank, cand in enumerate(result.candidates, start=1):
        assert cand.rank == rank
        assert cand.data_timestamp == CUTOFF
        assert cand.prediction_cutoff == result.prediction_cutoff
        assert cand.target_business_date == result.target_business_date
        assert cand.data_source == DATA_SOURCE
        assert 0.0 <= cand.score <= 100.0
    scores = [c.score for c in result.candidates]
    assert scores == sorted(scores, reverse=True)


def test_scored_universe_and_baselines_are_exposed_for_paper_logging() -> None:
    result = scan(market())
    assert set(result.eligible_tickers) == {f"{s}.NS" for s in SYMBOLS}
    assert len(result.momentum5_tickers) == 5
    assert set(result.momentum5_tickers) <= set(result.eligible_tickers)
    assert dict(result.benchmark_tickers) == {"NSE": "^NSEI"}


def _reasons(result, symbol: str) -> tuple[str, ...]:
    return next(r.reasons for r in result.excluded if r.symbol == symbol)


def test_each_bad_symbol_is_excluded_with_its_own_explicit_reason() -> None:
    frames = market()
    s = SYMBOLS
    # stale: last bar two sessions before the cutoff
    frames[f"{s[0]}.NS"] = frames[f"{s[0]}.NS"].iloc[:-2]
    # missing: provider returns nothing for it
    del frames[f"{s[1]}.NS"]
    # missing columns
    frames[f"{s[2]}.NS"] = frames[f"{s[2]}.NS"].drop(columns=["Volume"])
    # empty frame
    frames[f"{s[3]}.NS"] = pd.DataFrame()
    # invalid: many corrupted rows recently
    bad = frames[f"{s[4]}.NS"].copy()
    bad.iloc[-12:, bad.columns.get_loc("Low")] = -5.0
    frames[f"{s[4]}.NS"] = bad
    # insufficient history
    frames[f"{s[5]}.NS"] = frames[f"{s[5]}.NS"].iloc[-40:]
    # illiquid
    frames[f"{s[6]}.NS"] = frames[f"{s[6]}.NS"].assign(Volume=100.0)
    # suspended: no trading on the cutoff session and zero volume in recent days
    sus = frames[f"{s[7]}.NS"].copy()
    sus.iloc[-6:, sus.columns.get_loc("Volume")] = 0.0
    frames[f"{s[7]}.NS"] = sus
    # penny price
    frames[f"{s[8]}.NS"] = frames[f"{s[8]}.NS"] * 0.001 + 0.0
    frames[f"{s[8]}.NS"]["Volume"] = 5_000_000.0

    result = scan(frames)

    assert any(r.startswith("stale_data") for r in _reasons(result, s[0]))
    assert "no_data" in _reasons(result, s[1])
    assert any(r.startswith("missing_columns") for r in _reasons(result, s[2]))
    assert "no_data" in _reasons(result, s[3])
    assert any(r.startswith("unreliable_records") for r in _reasons(result, s[4]))
    assert "insufficient_history" in _reasons(result, s[5])
    assert "low_liquidity" in _reasons(result, s[6])
    assert {"frequent_zero_volume", "low_liquidity"} & set(_reasons(result, s[7]))
    assert "price_below_minimum" in _reasons(result, s[8])
    excluded = {r.symbol for r in result.excluded}
    assert excluded >= set(s[:9])
    assert not excluded & {c.symbol for c in result.candidates}
    assert result.data_quality["stale_symbols"] == 1
    # Only 7 of 16 remain, below the 10-name minimum cross-section: no ranking is produced.
    assert result.status == "UNAVAILABLE"
    assert result.candidates == ()
    assert any("eligible symbols" in w for w in result.warnings)


def test_low_coverage_downgrades_status_and_is_reported() -> None:
    frames = market()
    for symbol in SYMBOLS[:6]:
        del frames[f"{symbol}.NS"]
    result = scan(frames)
    assert result.status == "DEGRADED"
    assert any("usable data" in w for w in result.warnings)
    assert result.data_quality["coverage_pct"] == 62.5


@pytest.mark.parametrize("error", [TimeoutError("timeout"), ConnectionError("down"), KeyError("x")])
def test_provider_errors_give_unavailable_with_no_retry_and_no_substitute(error) -> None:
    calls = []

    def broken(tickers):
        calls.append(tickers)
        raise error

    result = scan(None, fetcher=broken)
    assert result.status == "UNAVAILABLE"
    assert result.candidates == ()
    assert type(error).__name__ in " ".join(result.errors)
    assert len(calls) == 1  # no hidden retry loop and no second (cached/stale) source


def test_all_stale_data_is_unavailable_not_silently_used() -> None:
    old = market(end=date(2026, 10, 27))  # a week old
    result = scan(old)
    assert result.status == "UNAVAILABLE"
    assert result.candidates == ()
    assert result.data_quality["stale_symbols"] == len(SYMBOLS)


def test_stale_benchmark_degrades_instead_of_using_old_index_data() -> None:
    frames = market()
    frames["^NSEI"] = frames["^NSEI"].iloc[:-3]
    result = scan(frames)
    assert result.status == "DEGRADED"
    assert any("Market-relative strength missing" in w for w in result.warnings)
    assert any("Market-relative strength unavailable for NSE" in u for u in result.unavailable_data)


def test_nonfinite_and_inconsistent_values_never_reach_the_ranking() -> None:
    frames = market()
    broken = frames[f"{SYMBOLS[0]}.NS"].copy()
    broken.iloc[-1, broken.columns.get_loc("Close")] = np.inf
    broken.iloc[-2, broken.columns.get_loc("High")] = np.nan
    frames[f"{SYMBOLS[0]}.NS"] = broken
    result = scan(frames)
    # The invalid cutoff-day bar is removed, so the symbol's last bar is stale -> excluded.
    assert SYMBOLS[0] in {r.symbol for r in result.excluded}
    assert SYMBOLS[0] not in {c.symbol for c in result.candidates}
    for cand in result.candidates:
        assert np.isfinite([cand.score, cand.last_close, cand.penalty]).all()


# ---- symbol normalisation and duplicate companies -------------------------------------


def test_symbol_normalisation_accepts_suffix_case_and_whitespace_once() -> None:
    accepted, excluded = build_universe(
        [(" reliance ", "nse"), ("RELIANCE.NS", "NSE"), ("Reliance", "NSE"), ("500325.BO", "BSE")],
        ScannerConfig(prefer_nse_for_cross_listed=False),
    )
    assert [(i.symbol, i.exchange) for i in accepted] == [("RELIANCE", "NSE"), ("500325", "BSE")]
    assert [r.reasons for r in excluded] == [("duplicate_symbol",), ("duplicate_symbol",)]


@pytest.mark.parametrize(
    ("entry", "reason"),
    [
        (("RELIANCE.BO", "NSE"), "exchange_suffix_mismatch"),
        (("RELIANCE.NS", "BSE"), "exchange_suffix_mismatch"),
        (("RELIANCE", "NYSE"), "unsupported_exchange"),
        (("RELIANCE", "BSE"), "invalid_bse_scrip_code"),
        (("5003", "BSE"), "invalid_bse_scrip_code"),
        (("BAD SYMBOL!", "NSE"), "invalid_symbol"),
        (("", "NSE"), "invalid_symbol"),
    ],
)
def test_invalid_symbols_are_rejected_with_a_reason(entry, reason) -> None:
    accepted, excluded = build_universe([entry], ScannerConfig())
    assert accepted == []
    assert excluded[0].reasons == (reason,)


def test_cross_listed_company_is_counted_once_and_prefers_nse() -> None:
    nse, bse = NSE_CANDIDATES[0], BSE_CANDIDATES[0]
    accepted, excluded = build_universe([(nse, "NSE"), (bse, "BSE")], ScannerConfig())
    assert [(i.symbol, i.exchange) for i in accepted] == [(nse, "NSE")]
    assert excluded[0].reasons == ("cross_listed_duplicate_of_nse",)
    # BSE-only mode keeps the BSE listing; opting out keeps both.
    only_bse, _ = build_universe([(bse, "BSE")], ScannerConfig(exchanges=("BSE",)))
    assert [(i.symbol, i.exchange) for i in only_bse] == [(bse, "BSE")]
    both, _ = build_universe(
        [(nse, "NSE"), (bse, "BSE")], ScannerConfig(prefer_nse_for_cross_listed=False)
    )
    assert len(both) == 2
    assert ticker_for(Instrument(nse, "NSE")).endswith(".NS")


def test_nse_bse_scan_never_ranks_the_same_company_twice() -> None:
    pairs = list(zip(NSE_CANDIDATES[:14], BSE_CANDIDATES[:14], strict=True))
    frames = {f"{n}.NS": frame(i, price0=300.0 + 20 * i) for i, (n, _) in enumerate(pairs)}
    universe = [(n, "NSE") for n, _ in pairs] + [(b, "BSE") for _, b in pairs]
    result = scan_next_day_movers(
        ScannerConfig(top_n=50, check_surveillance=False),
        now=NOW,
        universe=universe,
        fetcher=fetcher_for({**frames, "^NSEI": frame(900, price0=24000.0, base_volume=0.0)}),
    )
    assert result.status in {"OK", "DEGRADED"}
    assert {c.exchange for c in result.candidates} == {"NSE"}
    assert len({c.symbol for c in result.candidates}) == len(result.candidates)
    duplicates = [r for r in result.excluded if "cross_listed_duplicate_of_nse" in r.reasons]
    assert len(duplicates) == 14


# ======================================================================================
# Live / evaluation parity and look-ahead
# ======================================================================================


def _eval_side(frames, instruments, benchmarks, day: date, cfg: ScannerConfig):
    panel, _, _ = build_evaluation_panel(frames, instruments, benchmarks, cfg)
    one_day = panel.xs(pd.Timestamp(day), level="date")
    eligible = add_relative_strength(one_day[one_day["eligible"]])
    scores, _ = score_panel(eligible, cfg)
    return rankable(scores, cfg), eligible


def test_live_scan_and_walk_forward_agree_on_scores_for_the_same_day() -> None:
    day = date(2026, 10, 14)  # a regular Wednesday session
    frames = market(end=CUTOFF)
    instruments = {f"{s}.NS": Instrument(s, "NSE") for s in SYMBOLS}
    cfg = config(top_n=len(SYMBOLS))

    # The live run only "sees" bars up to the cutoff, even though the provider hands back
    # everything including 15 later sessions.
    live = scan(frames, now=at(day, 18, 0), cfg=cfg)
    assert live.prediction_cutoff == datetime(2026, 10, 14, 15, 30, tzinfo=IST)
    ranked, eligible = _eval_side(frames, instruments, {"NSE": frames["^NSEI"]}, day, cfg)

    live_scores = {c.ticker: c.score for c in live.candidates}
    eval_scores = ranked["score"].round(2).to_dict()
    assert set(live_scores) == set(eval_scores)
    for ticker, score in live_scores.items():
        assert score == pytest.approx(eval_scores[ticker], abs=1e-9)
    assert set(live.eligible_tickers) == set(eligible.index)
    order_eval = list(
        ranked.assign(t=ranked.index)
        .sort_values(["score", "positive_score", "t"], ascending=[False, False, True])
        .index
    )
    assert [c.ticker for c in live.candidates] == order_eval


def test_live_and_evaluation_use_the_same_scoring_functions() -> None:
    import scanner.next_day_movers as live_module
    import scanner.next_day_movers_eval as eval_module

    for name in (
        "compute_feature_frame",
        "ineligibility_flags",
        "score_panel",
        "rankable",
        "add_relative_strength",
        "benchmark_feature_frame",
        "sector_of",
    ):
        assert getattr(eval_module, name) is getattr(live_module, name), name


def test_live_result_is_independent_of_every_bar_after_the_cutoff() -> None:
    frames = market(end=date(2026, 11, 13))
    baseline = scan(frames, now=at(date(2026, 11, 3), 18, 0))
    altered = {}
    for ticker, bars in frames.items():
        copy = bars.copy()
        copy.loc[copy.index > pd.Timestamp(CUTOFF)] *= 50.0
        altered[ticker] = copy
    shifted = scan(altered, now=at(date(2026, 11, 3), 18, 0))
    assert [(c.ticker, c.score, c.last_close) for c in shifted.candidates] == [
        (c.ticker, c.score, c.last_close) for c in baseline.candidates
    ]


def test_features_at_date_t_ignore_all_later_bars() -> None:
    bars = frame(5)
    t = bars.index[150]
    full = compute_feature_frame(bars)
    for later in (bars.index[151], bars.index[170]):
        mutated = bars.copy()
        mutated.loc[mutated.index >= later] *= 7.0
        again = compute_feature_frame(mutated)
        pd.testing.assert_series_equal(full.loc[t], again.loc[t], check_names=False)


def test_evaluation_outcome_depends_only_on_the_next_session() -> None:
    frames = market()
    instruments = {f"{s}.NS": Instrument(s, "NSE") for s in SYMBOLS}
    benchmarks = {"NSE": frames["^NSEI"]}
    ticker = f"{SYMBOLS[0]}.NS"
    base, _, _ = build_evaluation_panel(frames, instruments, benchmarks, ScannerConfig())
    day = frames[ticker].index[160]
    nxt, after = frames[ticker].index[161], frames[ticker].index[162]

    later = {t: f.copy() for t, f in frames.items()}
    later[ticker].loc[after:] *= 9.0
    changed, _, _ = build_evaluation_panel(later, instruments, benchmarks, ScannerConfig())
    pd.testing.assert_series_equal(
        base.loc[(day, ticker)], changed.loc[(day, ticker)], check_names=False
    )

    nxt_frames = {t: f.copy() for t, f in frames.items()}
    nxt_frames[ticker].loc[nxt, "Close"] *= 1.2
    nxt_frames[ticker].loc[nxt, "High"] *= 1.2
    moved, _, _ = build_evaluation_panel(nxt_frames, instruments, benchmarks, ScannerConfig())
    feature_columns = [c for c in base.columns if c not in {"o2c", "c2c"}]
    pd.testing.assert_series_equal(
        base.loc[(day, ticker), feature_columns],
        moved.loc[(day, ticker), feature_columns],
        check_names=False,
    )
    assert moved.loc[(day, ticker), "o2c"] != base.loc[(day, ticker), "o2c"]


def test_data_quality_rejection_uses_only_information_available_at_each_date() -> None:
    bars = frame(11)
    corrupted = bars.copy()
    corrupted.iloc[-30:-20, corrupted.columns.get_loc("Close")] = -1.0  # 10 bad rows, recent
    flags = unreliable_record_flags(
        pd.Series(
            ~(corrupted["Close"] <= 0),
            index=corrupted.index,
        )
    )
    # Before the corruption the record is reliable; the live rule reaches the same verdict.
    early = corrupted.index[-60]
    assert not bool(flags.loc[early])
    assert clean_ohlcv(corrupted.loc[:early], None)[0] is not None
    # Once the bad rows are inside the trailing window both rules reject.
    late = corrupted.index[-21]
    assert bool(flags.loc[late])
    assert clean_ohlcv(corrupted.loc[:late], None)[0] is None
    # Parity for every date: the per-date flag equals the live whole-record decision.
    valid = ~(corrupted["Close"] <= 0)
    full_flags = unreliable_record_flags(valid)
    for position in range(70, len(corrupted), 7):
        truncated = corrupted.iloc[: position + 1]
        live_rejects = clean_ohlcv(truncated, None)[0] is None
        assert live_rejects == bool(full_flags.iloc[position]), position


def test_history_cleaning_does_not_reject_a_symbol_for_future_bad_rows() -> None:
    bars = frame(12)
    bars.iloc[-25:-15, bars.columns.get_loc("Low")] = -2.0
    assert clean_ohlcv(bars, None)[0] is None  # live at the end of history: rejected
    clean, flags, reasons = clean_ohlcv_history(bars)
    assert clean is not None and flags is not None and reasons == []
    assert not bool(flags.iloc[100])  # earlier dates are not tainted by later bad rows


# ---- costs, slippage and outcomes -----------------------------------------------------


def test_round_trip_cost_includes_slippage_on_both_sides_and_statutory_charges() -> None:
    model = default_intraday_cost_model()
    no_slip = IndiaEquityCostModel(
        **{**model.__dict__, "slippage_bps": 0.0}  # type: ignore[arg-type]
    )
    expected_slippage = 2 * model.slippage_bps / 1e4
    assert round_trip_cost_fraction(model) - round_trip_cost_fraction(no_slip) == pytest.approx(
        expected_slippage
    )
    assert model.slippage_bps > 0
    assert round_trip_cost_fraction(model) > 2 * model.slippage_bps / 1e4  # plus charges
    assert round_trip_cost_fraction(model) < 0.01  # sanity: well under 1% of notional


def test_net_open_to_close_series_is_gross_minus_the_configured_cost() -> None:
    frames = market(symbols=NSE_CANDIDATES[:20])
    instruments = {f"{s}.NS": Instrument(s, "NSE") for s in NSE_CANDIDATES[:20]}
    cfg = EvalConfig(top_k=5, bootstrap_samples=200, scanner=config())
    result = run_walk_forward(frames, instruments, {"NSE": frames["^NSEI"]}, cfg)
    cost = round_trip_cost_fraction(cfg.cost_model)
    gross = result.daily["score_o2c"]
    net_row = result.summary.loc["Score top-k, net of costs (open->close)"]
    gross_row = result.summary.loc["Score top-k, gross (open->close)"]
    assert net_row["mean_bps"] == pytest.approx(gross_row["mean_bps"] - cost * 1e4)
    assert net_row["mean_bps"] == pytest.approx((gross - cost).mean() * 1e4)
    assert result.round_trip_cost_bps == pytest.approx(cost * 1e4)
    # Doubling the assumed slippage must lower the net result by exactly the extra cost.
    pricier = IndiaEquityCostModel(
        **{**cfg.cost_model.__dict__, "slippage_bps": cfg.cost_model.slippage_bps * 2}  # type: ignore[arg-type]
    )
    again = run_walk_forward(
        frames,
        instruments,
        {"NSE": frames["^NSEI"]},
        EvalConfig(top_k=5, bootstrap_samples=200, scanner=config(), cost_model=pricier),
    )
    extra = round_trip_cost_fraction(pricier) - cost
    net_again = again.summary.loc["Score top-k, net of costs (open->close)", "mean_bps"]
    assert net_again == pytest.approx(net_row["mean_bps"] - extra * 1e4)


def test_missing_next_bar_gives_no_outcome_rather_than_a_zero() -> None:
    frames = market(symbols=NSE_CANDIDATES[:6])
    instruments = {f"{s}.NS": Instrument(s, "NSE") for s in NSE_CANDIDATES[:6]}
    ticker = f"{NSE_CANDIDATES[0]}.NS"
    day = frames[ticker].index[160]
    gap = frames[ticker].index[161]
    frames[ticker] = frames[ticker].drop(index=gap)
    panel, _, _ = build_evaluation_panel(frames, instruments, {}, ScannerConfig())
    row = panel.loc[(day, ticker)]
    assert np.isnan(row["o2c"]) and np.isnan(row["c2c"])
    other = f"{NSE_CANDIDATES[1]}.NS"
    assert np.isfinite(panel.loc[(day, other), "o2c"])


def test_history_gate_blocks_early_dates_in_the_evaluation_panel() -> None:
    frames = market(symbols=NSE_CANDIDATES[:6])
    instruments = {f"{s}.NS": Instrument(s, "NSE") for s in NSE_CANDIDATES[:6]}
    cfg = ScannerConfig()
    panel, _, _ = build_evaluation_panel(frames, instruments, {}, cfg)
    one = panel.xs(f"{NSE_CANDIDATES[0]}.NS", level="ticker")
    assert not one["eligible"].iloc[: cfg.min_history - 1].any()
    assert one["eligible"].iloc[-20:].all()


def test_insufficient_history_and_invalid_data_cannot_be_evaluated() -> None:
    names = NSE_CANDIDATES[:14]
    instruments = {f"{s}.NS": Instrument(s, "NSE") for s in names}
    short = {f"{s}.NS": frame(i, n=45) for i, s in enumerate(names)}
    with pytest.raises(ValueError, match="no evaluable dates"):
        run_walk_forward(short, instruments, {}, EvalConfig(top_k=5, bootstrap_samples=200))
    garbage = {t: pd.DataFrame({"Open": [1.0], "Close": [1.0]}) for t in instruments}
    with pytest.raises(RuntimeError):
        run_walk_forward(garbage, instruments, {}, EvalConfig(top_k=5, bootstrap_samples=200))
