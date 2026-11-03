"""Tests for the next-business-day upside candidate scanner."""

from __future__ import annotations

from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from scanner.next_day_movers import (
    FACTOR_WEIGHTS,
    SCORE_TYPE,
    Instrument,
    ScannerConfig,
    add_relative_strength,
    build_universe,
    clean_ohlcv,
    compute_feature_frame,
    ineligibility_flags,
    resolve_prediction_cutoff,
    scan_next_day_movers,
    score_panel,
    ticker_for,
)
from scanner.universe import NSE_CANDIDATES
from services.market_calendar import CalendarUnavailableError

IST = ZoneInfo("Asia/Kolkata")
CUTOFF = date(2026, 11, 3)  # Tuesday, a regular session
NOW = datetime(2026, 11, 3, 17, 30, tzinfo=IST)
SYMBOLS = NSE_CANDIDATES[:14]


def make_frame(
    seed: int,
    n: int = 200,
    end: date = CUTOFF,
    price0: float = 500.0,
    drift: float = 0.0,
    vol: float = 0.012,
    base_volume: float = 1_000_000.0,
) -> pd.DataFrame:
    """Random-walk daily bars ending on ``end`` (business days only)."""
    rng = np.random.default_rng(seed)
    index = pd.bdate_range(end=end, periods=n)
    close = price0 * np.exp(np.cumsum(rng.normal(drift, vol, n)))
    open_ = np.r_[price0, close[:-1]] * (1 + rng.normal(0, 0.003, n))
    high = np.maximum(open_, close) * (1 + np.abs(rng.normal(0, 0.004, n)))
    low = np.minimum(open_, close) * (1 - np.abs(rng.normal(0, 0.004, n)))
    volume = base_volume * np.exp(rng.normal(0, 0.3, n))
    return pd.DataFrame(
        {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": volume}, index=index
    )


def make_market(symbols: list[str], suffix: str = ".NS") -> dict[str, pd.DataFrame]:
    frames = {f"{s}{suffix}": make_frame(i, price0=200.0 + 40 * i) for i, s in enumerate(symbols)}
    frames["^NSEI"] = make_frame(900, price0=24000.0, vol=0.008, base_volume=0.0)
    frames["^BSESN"] = make_frame(901, price0=80000.0, vol=0.008, base_volume=0.0)
    return frames


def fetcher_for(frames: dict[str, pd.DataFrame]):
    def fetch(tickers: list[str]):
        usable = {t: frames[t] for t in tickers if t in frames}
        return usable, {"requested": len(tickers), "usable": len(usable)}

    return fetch


def nse_config(**overrides) -> ScannerConfig:
    base = {"exchanges": ("NSE",), "top_n": 5, "check_surveillance": False}
    base.update(overrides)
    return ScannerConfig(**base)


def scan(frames=None, config=None, universe=None, **kwargs):
    frames = make_market(SYMBOLS) if frames is None else frames
    return scan_next_day_movers(
        config or nse_config(),
        now=kwargs.pop("now", NOW),
        universe=universe or [(s, "NSE") for s in SYMBOLS],
        fetcher=kwargs.pop("fetcher", fetcher_for(frames)),
        **kwargs,
    )


# --------------------------------------------------------------------------- calendar


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (datetime(2026, 11, 3, 17, 30, tzinfo=IST), (date(2026, 11, 3), date(2026, 11, 4))),
        (datetime(2026, 11, 3, 15, 40, tzinfo=IST), (date(2026, 11, 2), date(2026, 11, 3))),
        (datetime(2026, 11, 3, 11, 0, tzinfo=IST), (date(2026, 11, 2), date(2026, 11, 3))),
        (datetime(2026, 11, 7, 12, 0, tzinfo=IST), (date(2026, 11, 6), date(2026, 11, 9))),
        (datetime(2026, 11, 6, 18, 0, tzinfo=IST), (date(2026, 11, 6), date(2026, 11, 9))),
        (datetime(2026, 11, 9, 18, 0, tzinfo=IST), (date(2026, 11, 9), date(2026, 11, 11))),
        (datetime(2026, 11, 10, 18, 0, tzinfo=IST), (date(2026, 11, 9), date(2026, 11, 11))),
        (datetime(2026, 11, 3, 12, 30, tzinfo=UTC), (date(2026, 11, 3), date(2026, 11, 4))),
        (datetime(2026, 11, 3, 17, 30), (date(2026, 11, 3), date(2026, 11, 4))),  # naive = IST
    ],
)
def test_cutoff_and_target_respect_weekends_holidays_and_close(now, expected) -> None:
    assert resolve_prediction_cutoff(now) == expected


def test_cutoff_fails_closed_without_calendar_year() -> None:
    with pytest.raises(CalendarUnavailableError):
        resolve_prediction_cutoff(datetime(2027, 1, 4, 18, 0, tzinfo=IST))
    with pytest.raises(CalendarUnavailableError):
        # Target would fall in an unconfigured year, so no date is guessed.
        resolve_prediction_cutoff(datetime(2026, 12, 31, 18, 0, tzinfo=IST))


def test_scan_reports_unavailable_when_calendar_missing() -> None:
    result = scan(now=datetime(2027, 1, 4, 18, 0, tzinfo=IST))
    assert result.status == "UNAVAILABLE"
    assert result.candidates == ()
    assert result.target_business_date is None
    assert "calendar" in result.warnings[0].lower()


# --------------------------------------------------------------------------- universe


def test_universe_deduplicates_and_reports_reasons() -> None:
    entries = [
        ("tcs", "NSE"),
        ("TCS", "nse"),
        ("INFY.NS", "NSE"),
        ("INFY", "NSE"),
        ("WIPRO.BO", "NSE"),
        ("", "NSE"),
        ("BAD SYMBOL", "NSE"),
        ("123", "BSE"),
        ("RELIANCE", "NYSE"),
    ]
    accepted, excluded = build_universe(entries, ScannerConfig())
    assert [(i.symbol, i.exchange) for i in accepted] == [("TCS", "NSE"), ("INFY", "NSE")]
    reasons = {(e.symbol, e.exchange): e.reasons[0] for e in excluded}
    assert reasons[("TCS", "NSE")] == "duplicate_symbol"
    assert reasons[("INFY", "NSE")] == "duplicate_symbol"
    assert reasons[("WIPRO.BO", "NSE")] == "exchange_suffix_mismatch"
    assert reasons[("", "NSE")] == "invalid_symbol"
    assert reasons[("BAD SYMBOL", "NSE")] == "invalid_symbol"
    assert reasons[("123", "BSE")] == "invalid_bse_scrip_code"
    assert reasons[("RELIANCE", "NYSE")] == "unsupported_exchange"


def test_universe_handles_nse_and_bse_and_cross_listings() -> None:
    entries = [("RELIANCE", "NSE"), ("500325", "BSE"), ("532540", "BSE")]
    accepted, excluded = build_universe(entries, ScannerConfig())
    assert accepted == [Instrument("RELIANCE", "NSE"), Instrument("532540", "BSE")]
    assert excluded[0].symbol == "500325"
    assert excluded[0].reasons == ("cross_listed_duplicate_of_nse",)

    kept, _ = build_universe(entries, ScannerConfig(prefer_nse_for_cross_listed=False))
    assert len(kept) == 3
    nse_only, _ = build_universe(entries, ScannerConfig(exchanges=("NSE",)))
    assert [i.exchange for i in nse_only] == ["NSE"]


def test_ticker_conventions_follow_repository_mapping() -> None:
    assert ticker_for(Instrument("TCS", "NSE")) == "TCS.NS"
    assert ticker_for(Instrument("M&M", "NSE")) == "M&M.NS"
    assert ticker_for(Instrument("500325", "BSE")) == "RELIANCE.BO"
    assert ticker_for(Instrument("999999", "BSE")) is None


def test_scanner_config_validation() -> None:
    for kwargs in (
        {"exchanges": ()},
        {"exchanges": ("LSE",)},
        {"top_n": 0},
        {"min_cross_section": 1},
        {"min_price": 0.0},
        {"min_median_turnover": float("nan")},
        {"min_factor_coverage": 0.0},
        {"min_universe_coverage": 1.5},
    ):
        with pytest.raises(ValueError):
            ScannerConfig(**kwargs)


# --------------------------------------------------------------------------- cleaning


def test_clean_drops_bars_after_cutoff_to_prevent_leakage() -> None:
    frame = make_frame(1, n=120, end=date(2026, 11, 4))  # includes a bar after the cutoff
    cleaned, reasons = clean_ohlcv(frame, CUTOFF)
    assert reasons == []
    assert cleaned is not None
    assert cleaned.index[-1].date() == CUTOFF


def test_clean_removes_invalid_rows_and_duplicates() -> None:
    frame = make_frame(2, n=120)
    frame.iloc[10, frame.columns.get_loc("Close")] = -5.0
    frame.iloc[20, frame.columns.get_loc("Volume")] = -1.0
    frame.iloc[30, frame.columns.get_loc("Open")] = np.nan
    frame.iloc[40, frame.columns.get_loc("High")] = frame.iloc[40]["Low"] * 0.5  # High < Low
    duplicated = pd.concat([frame, frame.iloc[[-1]]])
    cleaned, reasons = clean_ohlcv(duplicated, CUTOFF)
    assert reasons == []
    assert cleaned is not None
    assert cleaned.index.is_unique
    assert len(cleaned) == 120 - 4
    assert (cleaned[["Open", "High", "Low", "Close"]] > 0).all().all()
    assert (cleaned["Volume"] >= 0).all()


def test_clean_rejects_unreliable_and_empty_records() -> None:
    frame = make_frame(3, n=120)
    frame.iloc[-10:, frame.columns.get_loc("Close")] = np.nan
    cleaned, reasons = clean_ohlcv(frame, CUTOFF)
    assert cleaned is None
    assert reasons[0].startswith("unreliable_records")
    assert clean_ohlcv(None)[1] == ["no_data"]
    assert clean_ohlcv(pd.DataFrame())[1] == ["no_data"]
    assert clean_ohlcv(frame.drop(columns=["Volume"]))[1] == ["missing_columns:Volume"]


def test_clean_normalises_timezone_aware_index() -> None:
    frame = make_frame(4, n=120)
    frame.index = frame.index.tz_localize(IST)
    cleaned, _ = clean_ohlcv(frame, CUTOFF)
    assert cleaned is not None
    assert cleaned.index.tz is None
    assert cleaned.index[-1].date() == CUTOFF


# --------------------------------------------------------------------------- features


def test_features_use_no_future_information() -> None:
    cleaned, _ = clean_ohlcv(make_frame(5, n=220), CUTOFF)
    assert cleaned is not None
    full = compute_feature_frame(cleaned)
    for length in (80, 120, 170, 219):
        truncated = compute_feature_frame(cleaned.iloc[:length])
        pd.testing.assert_frame_equal(truncated, full.iloc[:length])


def test_changing_future_bars_cannot_change_past_features() -> None:
    cleaned, _ = clean_ohlcv(make_frame(6, n=220), CUTOFF)
    assert cleaned is not None
    altered = cleaned.copy()
    altered.iloc[-10:, :4] *= 3.0
    altered.iloc[-10:, 4] *= 25.0
    base = compute_feature_frame(cleaned)
    changed = compute_feature_frame(altered)
    pd.testing.assert_frame_equal(base.iloc[:-10], changed.iloc[:-10])
    assert not base.iloc[-1].equals(changed.iloc[-1])


def test_feature_computation_does_not_mutate_input() -> None:
    cleaned, _ = clean_ohlcv(make_frame(7), CUTOFF)
    assert cleaned is not None
    before = cleaned.copy()
    compute_feature_frame(cleaned)
    pd.testing.assert_frame_equal(cleaned, before)


def flags_for(frame: pd.DataFrame, config: ScannerConfig | None = None) -> pd.Series:
    cleaned, _ = clean_ohlcv(frame, CUTOFF)
    assert cleaned is not None
    return ineligibility_flags(compute_feature_frame(cleaned), config or ScannerConfig()).iloc[-1]


def test_healthy_symbol_has_no_ineligibility_flags() -> None:
    assert not flags_for(make_frame(8)).any()


def test_low_liquidity_and_low_price_are_flagged() -> None:
    illiquid = make_frame(9)
    illiquid["Volume"] *= 0.001
    assert flags_for(illiquid)["low_liquidity"]

    cheap = make_frame(10)
    cheap[["Open", "High", "Low", "Close"]] *= 0.02
    assert flags_for(cheap)["price_below_minimum"]


def test_no_trading_on_cutoff_session_is_flagged() -> None:
    frame = make_frame(11)
    frame.iloc[-1, frame.columns.get_loc("Volume")] = 0.0
    assert flags_for(frame)["no_trading_on_cutoff_session"]


def test_frequent_zero_volume_marks_possible_suspension() -> None:
    frame = make_frame(12)
    frame.iloc[-6:-1, frame.columns.get_loc("Volume")] = 0.0
    assert flags_for(frame)["frequent_zero_volume"]


def test_extreme_move_and_data_gap_and_short_history_are_flagged() -> None:
    jump = make_frame(13)
    jump.iloc[-10:, :4] *= 1.7
    assert flags_for(jump)["extreme_move_unverified"]

    gappy = make_frame(14).drop(make_frame(14).index[150:160])
    assert flags_for(gappy)["data_gap"]

    short = make_frame(15, n=50)
    assert flags_for(short)["insufficient_history"]


# --------------------------------------------------------------------------- scoring


def monotone_panel(n: int = 12) -> pd.DataFrame:
    """A panel in which every positive factor improves with the row number."""
    tickers = [f"T{i:02d}.NS" for i in range(n)]
    base = np.linspace(-0.05, 0.05, n)
    panel = pd.DataFrame(index=tickers)
    for name in FACTOR_WEIGHTS:
        panel[name] = base
    panel["atr_pct"] = 0.02
    panel["gap_std_60"] = 0.01
    panel["rsi14"] = 55.0
    panel["ret_1d"] = base
    return panel


def test_factor_weights_sum_to_one() -> None:
    assert sum(FACTOR_WEIGHTS.values()) == pytest.approx(1.0)


def test_score_orders_stronger_stocks_higher_and_is_bounded() -> None:
    scores, _ = score_panel(monotone_panel(), ScannerConfig())
    assert scores["score"].is_monotonic_increasing
    assert scores["score"].between(0, 100).all()
    assert scores["factor_coverage"].eq(1.0).all()
    assert scores["positive_score"].iloc[-1] == pytest.approx(100.0)


def test_overbought_and_extended_moves_are_penalised() -> None:
    panel = monotone_panel()
    baseline, _ = score_panel(panel, ScannerConfig())
    panel.loc["T05.NS", ["rsi14", "ret_1d"]] = [85.0, 0.10]
    penalised, _ = score_panel(panel, ScannerConfig())
    extra = penalised.loc["T05.NS", "penalty"] - baseline.loc["T05.NS", "penalty"]
    assert extra == pytest.approx(10.0)


def test_higher_volatility_and_gap_risk_lower_the_score() -> None:
    panel = monotone_panel()
    panel["atr_pct"] = np.linspace(0.01, 0.05, len(panel))[::-1]  # top rows calmer
    panel["gap_std_60"] = np.linspace(0.005, 0.03, len(panel))[::-1]
    calm, _ = score_panel(panel, ScannerConfig())
    panel.loc["T11.NS", ["atr_pct", "gap_std_60"]] = [0.2, 0.2]
    wild, _ = score_panel(panel, ScannerConfig())
    assert wild.loc["T11.NS", "score"] < calm.loc["T11.NS", "score"]


def test_missing_factors_reduce_coverage_and_renormalise_weights() -> None:
    panel = monotone_panel()
    panel["rs_sector_5d"] = np.nan
    scores, ranks = score_panel(panel, ScannerConfig())
    assert scores["factor_coverage"].iloc[0] == pytest.approx(1.0 - FACTOR_WEIGHTS["rs_sector_5d"])
    assert ranks["rs_sector_5d"].isna().all()
    assert scores["positive_score"].iloc[-1] == pytest.approx(100.0)

    sparse = monotone_panel()
    sparse.loc[sparse.index[3:], "rs_sector_5d"] = np.nan  # only 3 values: too few to rank
    sparse_scores, _ = score_panel(sparse, ScannerConfig())
    assert sparse_scores["factor_coverage"].iloc[0] == pytest.approx(0.92)


def test_relative_strength_uses_index_and_same_sector_peers_excluding_self() -> None:
    panel = pd.DataFrame(
        {
            "ret_5d": [0.10, 0.02, 0.04, 0.06, 0.08, 0.05],
            "ret_20d": [0.20, 0.10, 0.10, 0.10, 0.10, 0.10],
            "bm_ret_5d": 0.01,
            "bm_ret_20d": 0.05,
            "sector": ["IT", "IT", "IT", "IT", "IT", "Unclassified"],
        },
        index=list("ABCDEF"),
    )
    result = add_relative_strength(panel)
    assert result.loc["A", "rs_market_5d"] == pytest.approx(0.09)
    assert result.loc["A", "rs_market_20d"] == pytest.approx(0.15)
    # A's peers are B, C, D, E (median 0.05), so A is 0.05 above them; self is excluded.
    assert result.loc["A", "rs_sector_5d"] == pytest.approx(0.05)
    assert result.loc["B", "rs_sector_5d"] == pytest.approx(
        0.02 - np.median([0.10, 0.04, 0.06, 0.08])
    )
    assert np.isnan(result.loc["F", "rs_sector_5d"])  # unclassified stocks get no sector strength


def test_sector_strength_needs_enough_peers_and_missing_index_is_nan() -> None:
    panel = pd.DataFrame(
        {"ret_5d": [0.1, 0.2, 0.3], "ret_20d": [0.1, 0.2, 0.3], "sector": ["IT"] * 3},
        index=list("ABC"),
    )
    result = add_relative_strength(panel)
    assert result["rs_sector_5d"].isna().all()  # only two peers each: below the minimum
    assert result["rs_market_5d"].isna().all()  # no index columns supplied


def test_score_is_never_labelled_as_probability() -> None:
    result = scan()
    assert result.score_type == SCORE_TYPE
    assert "not_a_probability" in result.score_type
    assert result.candidates
    candidate = result.candidates[0]
    assert candidate.score_type == SCORE_TYPE
    assert not hasattr(candidate, "probability")
    for column in result.to_frame().columns:
        assert "probab" not in column.lower() or "not a probability" in column.lower()


# --------------------------------------------------------------------------- scan: happy path


def test_scan_returns_ranked_shortlist_with_required_fields() -> None:
    result = scan()
    assert result.status == "OK"
    assert result.prediction_cutoff == datetime(2026, 11, 3, 15, 30, tzinfo=IST)
    assert result.target_business_date == date(2026, 11, 4)
    assert len(result.candidates) == 5
    assert [c.rank for c in result.candidates] == [1, 2, 3, 4, 5]
    scores = [c.score for c in result.candidates]
    assert scores == sorted(scores, reverse=True)
    for candidate in result.candidates:
        assert candidate.exchange == "NSE"
        assert candidate.ticker == f"{candidate.symbol}.NS"
        assert candidate.data_timestamp == CUTOFF
        assert candidate.target_business_date == date(2026, 11, 4)
        assert candidate.prediction_cutoff == result.prediction_cutoff
        assert candidate.data_source
        assert 0.0 <= candidate.score <= 100.0
        assert candidate.factor_coverage >= 0.8
    frame = result.to_frame()
    assert {
        "Symbol",
        "Exchange",
        "Supporting factors",
        "Risk flags",
        "Target business date",
    } <= set(frame.columns)
    assert result.disclaimer.startswith("Research and paper-trading use only")
    assert any("Delivery" in item for item in result.unavailable_data)
    assert any("News" in item for item in result.unavailable_data)


def test_scan_does_not_use_the_partial_bar_after_the_cutoff() -> None:
    frames = make_market(SYMBOLS)
    extra = pd.bdate_range(start=date(2026, 11, 4), periods=1)
    for ticker, frame in list(frames.items()):
        row = frame.iloc[[-1]].copy() * 1.5
        row.index = extra
        frames[ticker] = pd.concat([frame, row])
    result = scan(frames=frames)
    assert result.status == "OK"
    assert all(c.data_timestamp == CUTOFF for c in result.candidates)


def test_scan_is_deterministic_and_breaks_ties_by_ticker() -> None:
    shared = make_frame(21)
    frames = {f"{s}.NS": shared.copy() for s in SYMBOLS}
    frames["^NSEI"] = make_frame(900, price0=24000.0, vol=0.008, base_volume=0.0)
    first = scan(frames=frames, config=nse_config(top_n=14))
    second = scan(frames=frames, config=nse_config(top_n=14))
    assert [c.ticker for c in first.candidates] == [c.ticker for c in second.candidates]
    assert [c.ticker for c in first.candidates] == sorted(c.ticker for c in first.candidates)


def test_duplicate_symbols_in_input_produce_one_row() -> None:
    universe = [(s, "NSE") for s in SYMBOLS] + [("tcs", "NSE"), ("TCS.NS", "NSE")]
    result = scan(universe=universe, config=nse_config(top_n=50))
    tickers = [c.ticker for c in result.candidates]
    assert len(tickers) == len(set(tickers))
    assert sum(1 for e in result.excluded if "duplicate_symbol" in e.reasons) == 2


def test_nse_and_bse_listings_are_handled_together() -> None:
    nse = [s for s in SYMBOLS if s != "TCS"]
    frames = make_market(nse)
    frames["TCS.BO"] = make_frame(77, price0=3000.0)
    universe = [(s, "NSE") for s in nse] + [("532540", "BSE"), ("500325", "BSE")]
    config = ScannerConfig(top_n=50, check_surveillance=False)
    result = scan(frames=frames, config=config, universe=universe)
    bse = [c for c in result.candidates if c.exchange == "BSE"]
    assert [c.ticker for c in bse] == ["TCS.BO"]
    assert "bse_surveillance_not_checked" in bse[0].risk_flags
    assert any(
        e.symbol == "500325" and "cross_listed_duplicate_of_nse" in e.reasons
        for e in result.excluded
    )


# --------------------------------------------------------------------------- scan: data quality


def test_stale_symbol_is_excluded_not_substituted() -> None:
    frames = make_market(SYMBOLS)
    stale_ticker = f"{SYMBOLS[0]}.NS"
    frames[stale_ticker] = make_frame(31, end=date(2026, 10, 30))
    result = scan(frames=frames, config=nse_config(top_n=50))
    assert stale_ticker not in [c.ticker for c in result.candidates]
    record = next(e for e in result.excluded if e.ticker == stale_ticker)
    assert record.reasons[0].startswith("stale_data")
    assert "2026-10-30" in record.reasons[0]
    assert result.data_quality["stale_symbols"] == 1


def test_missing_invalid_and_illiquid_symbols_are_excluded_with_reasons() -> None:
    frames = make_market(SYMBOLS)
    del frames[f"{SYMBOLS[0]}.NS"]
    bad = frames[f"{SYMBOLS[1]}.NS"].copy()
    bad.iloc[-1, bad.columns.get_loc("Close")] = -1.0
    bad.iloc[-2, bad.columns.get_loc("Close")] = np.nan
    bad.iloc[-3, bad.columns.get_loc("Close")] = 0.0
    bad.iloc[-4, bad.columns.get_loc("Close")] = np.nan
    frames[f"{SYMBOLS[1]}.NS"] = bad
    thin = frames[f"{SYMBOLS[2]}.NS"].copy()
    thin["Volume"] *= 0.0001
    frames[f"{SYMBOLS[2]}.NS"] = thin
    result = scan(frames=frames, config=nse_config(top_n=50))
    reasons = {e.symbol: e.reasons for e in result.excluded}
    assert reasons[SYMBOLS[0]] == ("no_data",)
    assert reasons[SYMBOLS[1]][0].startswith("unreliable_records")
    assert "low_liquidity" in reasons[SYMBOLS[2]]
    ranked = {c.symbol for c in result.candidates}
    assert not ranked & set(SYMBOLS[:3])
    assert result.data_quality["eligible"] == len(SYMBOLS) - 3


def test_provider_exception_returns_unavailable_without_fallback() -> None:
    def broken(_tickers):
        raise TimeoutError("yahoo timed out")

    result = scan(fetcher=broken)
    assert result.status == "UNAVAILABLE"
    assert result.candidates == ()
    assert "TimeoutError" in result.warnings[0]
    assert result.errors == ("TimeoutError: yahoo timed out",)
    assert result.to_frame().empty


def test_empty_provider_response_returns_unavailable() -> None:
    result = scan(fetcher=lambda tickers: ({}, {"requested": len(tickers), "usable": 0}))
    assert result.status == "UNAVAILABLE"
    assert result.candidates == ()
    assert "eligible symbols" in result.warnings[0]


def test_too_few_eligible_symbols_gives_no_ranking() -> None:
    frames = make_market(SYMBOLS[:6])
    result = scan(frames=frames, universe=[(s, "NSE") for s in SYMBOLS[:6]])
    assert result.status == "UNAVAILABLE"
    assert result.candidates == ()


def test_missing_benchmark_degrades_status_and_is_reported() -> None:
    frames = make_market(SYMBOLS)
    del frames["^NSEI"]
    result = scan(frames=frames)
    assert result.status == "DEGRADED"
    assert any("Market-relative strength unavailable" in item for item in result.unavailable_data)
    assert any("Market-relative strength missing" in item for item in result.warnings)
    assert result.candidates
    assert all(c.factor_coverage < 1.0 for c in result.candidates)


def test_low_universe_coverage_is_flagged() -> None:
    symbols = NSE_CANDIDATES[:20]
    frames = make_market(symbols)
    for symbol in symbols[:6]:
        del frames[f"{symbol}.NS"]
    result = scan(
        frames=frames,
        universe=[(s, "NSE") for s in symbols],
        config=nse_config(min_universe_coverage=0.9),
    )
    assert result.status == "DEGRADED"
    assert result.candidates
    assert any("usable data" in item for item in result.warnings)
    assert result.data_quality["coverage_pct"] == pytest.approx(14 / 20 * 100, abs=0.1)


# --------------------------------------------------------------------------- surveillance


def test_surveillance_flagged_symbols_are_excluded() -> None:
    target = SYMBOLS[3]

    def safety(symbols, as_of):
        assert as_of == CUTOFF
        frame = pd.DataFrame(
            {
                "Symbol": symbols,
                "Safety flags": ["" if s != target else "ASM Stage 2" for s in symbols],
            }
        )
        return frame, None

    result = scan(config=nse_config(check_surveillance=True, top_n=50), safety_fetcher=safety)
    assert target not in [c.symbol for c in result.candidates]
    record = next(e for e in result.excluded if e.symbol == target)
    assert record.reasons == ("nse_surveillance:ASM Stage 2",)


def test_surveillance_failure_is_reported_not_hidden() -> None:
    def failing(_symbols, _as_of):
        return pd.DataFrame(), "NSE surveillance archive unavailable."

    result = scan(config=nse_config(check_surveillance=True), safety_fetcher=failing)
    assert result.status == "DEGRADED"
    assert any("surveillance" in item.lower() for item in result.unavailable_data)
    assert all("nse_surveillance_check_unavailable" in c.risk_flags for c in result.candidates)

    def raising(_symbols, _as_of):
        raise ConnectionError("blocked")

    raised = scan(config=nse_config(check_surveillance=True), safety_fetcher=raising)
    assert raised.status == "DEGRADED"
    assert any("ConnectionError" in item for item in raised.unavailable_data)
