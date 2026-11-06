"""Deterministic tests for NSE/BSE momentum ranking (synthetic data only)."""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from scanner.momentum_engine import (
    STATUS_INSUFFICIENT,
    STATUS_OK,
    STATUS_PARTIAL,
    STATUS_STALE,
    MomentumResult,
    compute_momentum,
    compute_momentum_batch,
)
from scanner.momentum_ranking import (
    RANKING_COLUMNS,
    UNRANKED_COLUMNS,
    bare_symbol,
    exchange_of,
    rank_momentum,
    summarize_momentum,
    unranked_table,
    view_ranking,
)

IST = ZoneInfo("Asia/Kolkata")
AS_OF = datetime(2026, 11, 4, 11, 30, 20, tzinfo=IST)


def _result(
    score: float | None,
    *,
    status: str = STATUS_OK,
    confirmation: str = "FULL",
    ratio: float | None = 1.5,
    direction: str = "UP",
    reasons: tuple[str, ...] = (),
) -> MomentumResult:
    return MomentumResult(
        status=status,
        score=score,
        direction=direction,
        as_of=AS_OF,
        last_bar_time=AS_OF - timedelta(seconds=80),
        data_age_seconds=20.0,
        returns={1: 0.001, 5: 0.004, 10: 0.006, 15: 0.008},
        window_notes={},
        components=(),
        score_coverage=1.0,
        volume_ratio=ratio,
        volume_state="CONFIRMED" if ratio is not None else "UNAVAILABLE",
        timeframe_confirmation=confirmation,
        agreeing_windows=4,
        available_windows=4,
        reasons=reasons,
    )


def _unscored(status: str, reason: str) -> MomentumResult:
    return _result(None, status=status, confirmation="NONE", ratio=None, reasons=(reason,))


def test_ranks_by_score_descending_with_one_based_ranks() -> None:
    results = {
        "AAA.NS": _result(40.0),
        "BBB.NS": _result(90.0),
        "CCC.BO": _result(65.0),
    }

    ranking = rank_momentum(results)

    assert list(ranking["Symbol"]) == ["BBB", "CCC", "AAA"]
    assert list(ranking["Rank"]) == [1, 2, 3]
    assert list(ranking["Momentum strength"]) == [90.0, 65.0, 40.0]
    assert tuple(ranking.columns) == RANKING_COLUMNS


def test_ranking_never_changes_the_engine_score() -> None:
    result = _result(73.456)

    ranking = rank_momentum({"AAA.NS": result})

    assert ranking.loc[0, "Momentum strength"] == 73.5  # display rounding only
    assert result.score == 73.456


def test_ties_break_on_confirmation_then_volume_then_ticker() -> None:
    results = {
        "DDD.NS": _result(70.0, confirmation="PARTIAL", ratio=3.0),
        "CCC.NS": _result(70.0, confirmation="FULL", ratio=1.2),
        "BBB.NS": _result(70.0, confirmation="FULL", ratio=2.5),
        "AAA.NS": _result(70.0, confirmation="FULL", ratio=None),
        "EEE.NS": _result(70.0, confirmation="FULL", ratio=2.5),
    }

    ranking = rank_momentum(results)

    # FULL beats PARTIAL; higher volume ratio first; missing volume last; ticker last resort.
    assert list(ranking["Symbol"]) == ["BBB", "EEE", "CCC", "AAA", "DDD"]


def test_missing_volume_never_outranks_a_measured_surge_at_equal_score() -> None:
    results = {
        "AAA.NS": _result(55.0, ratio=None),
        "ZZZ.NS": _result(55.0, ratio=0.1),
    }

    assert list(rank_momentum(results)["Symbol"]) == ["ZZZ", "AAA"]


def test_ranking_is_independent_of_input_order() -> None:
    base = {f"S{i:02d}.NS": _result(float(i % 7) * 10.0, ratio=float(i % 3)) for i in range(30)}
    expected = rank_momentum(base)
    keys = list(base)
    for seed in range(5):
        random.Random(seed).shuffle(keys)
        shuffled = {key: base[key] for key in keys}
        pd.testing.assert_frame_equal(rank_momentum(shuffled), expected)


def test_unscored_symbols_are_never_ranked_and_are_reported() -> None:
    results = {
        "OKK.NS": _result(50.0),
        "PAR.BO": _result(30.0, status=STATUS_PARTIAL, reasons=("volume_unavailable",)),
        "OLD.NS": _unscored(STATUS_STALE, "latest_completed_bar_is_900s_old"),
        "FEW.BO": _unscored(STATUS_INSUFFICIENT, "only_1_of_4_windows"),
    }

    ranking = rank_momentum(results)
    skipped = unranked_table(results)

    assert set(ranking["Symbol"]) == {"OKK", "PAR"}
    assert ranking["Momentum strength"].notna().all()
    assert set(skipped["Symbol"]) == {"OLD", "FEW"}
    assert tuple(skipped.columns) == UNRANKED_COLUMNS
    reasons = dict(zip(skipped["Symbol"], skipped["Reasons"], strict=True))
    assert "900s_old" in reasons["OLD"]
    assert "only_1_of_4" in reasons["FEW"]


def test_same_company_on_both_exchanges_stays_two_rows_with_exchange_ranks() -> None:
    results = {
        "AAA.NS": _result(80.0),
        "AAA.BO": _result(75.0),
        "BBB.NS": _result(60.0),
        "CCC.BO": _result(90.0),
    }

    ranking = rank_momentum(results)

    assert list(zip(ranking["Symbol"], ranking["Exchange"], strict=True)) == [
        ("CCC", "BSE"),
        ("AAA", "NSE"),
        ("AAA", "BSE"),
        ("BBB", "NSE"),
    ]
    assert list(ranking["Exchange rank"]) == [1, 1, 2, 2]


def test_top_n_limits_rows_but_not_exchange_rank_basis() -> None:
    results = {f"S{i:02d}.NS": _result(float(i)) for i in range(15)}
    results["LOW.BO"] = _result(0.5)

    top3 = rank_momentum(results, top_n=3)
    everything = rank_momentum(results, top_n=None)

    assert len(top3) == 3
    assert len(everything) == 16
    assert len(rank_momentum(results)) == 10  # default
    assert rank_momentum(results, top_n=0).empty
    assert everything.loc[everything["Symbol"].eq("LOW"), "Exchange rank"].item() == 1


def test_empty_and_all_unscored_inputs_give_an_empty_ranking_with_columns() -> None:
    assert rank_momentum({}).empty
    only_bad = {"OLD.NS": _unscored(STATUS_STALE, "stale")}
    ranking = rank_momentum(only_bad)
    assert ranking.empty
    assert tuple(ranking.columns) == RANKING_COLUMNS


def test_view_ranking_filters_exchange_and_renumbers_without_touching_scores() -> None:
    results = {
        "AAA.NS": _result(90.0),
        "BBB.BO": _result(80.0),
        "CCC.NS": _result(70.0),
        "DDD.BO": _result(60.0),
    }
    full = rank_momentum(results, top_n=None)
    snapshot = full.copy(deep=True)

    bse = view_ranking(full, exchange="BSE")

    assert list(bse["Symbol"]) == ["BBB", "DDD"]
    assert list(bse["Rank"]) == [1, 2]
    assert list(bse["Exchange rank"]) == [1, 2]
    assert list(bse["Momentum strength"]) == [80.0, 60.0]
    assert list(view_ranking(full, exchange="NSE + BSE")["Symbol"]) == list(full["Symbol"])
    assert len(view_ranking(full, top_n=1)) == 1
    pd.testing.assert_frame_equal(full, snapshot)  # input not mutated


def test_view_ranking_handles_empty_input() -> None:
    assert view_ranking(pd.DataFrame()).empty
    assert tuple(view_ranking(pd.DataFrame()).columns) == RANKING_COLUMNS


def test_summary_counts_every_outcome_including_symbols_the_provider_never_returned() -> None:
    results = {
        "OKK.NS": _result(50.0),
        "PAR.BO": _result(30.0, status=STATUS_PARTIAL),
        "OLD.NS": _unscored(STATUS_STALE, "stale"),
    }

    summary = summarize_momentum(results, requested=5)

    assert summary["requested"] == 5
    assert summary["scored"] == 2
    assert summary["unscored"] == 1
    assert summary["missing_from_provider"] == 2
    assert summary["status_OK"] == 1
    assert summary["status_PARTIAL"] == 1
    assert summary["status_STALE"] == 1
    assert summarize_momentum(results)["missing_from_provider"] == 0


@pytest.mark.parametrize(
    ("ticker", "exchange", "symbol"),
    [
        ("RELIANCE.NS", "NSE", "RELIANCE"),
        ("reliance.bo", "BSE", "RELIANCE"),
        ("M&M.NS", "NSE", "M&M"),
        ("NIFTY", None, "NIFTY"),
    ],
)
def test_exchange_and_symbol_parsing(ticker: str, exchange: str | None, symbol: str) -> None:
    assert exchange_of(ticker) == exchange
    assert bare_symbol(ticker) == symbol


# --- end to end with the real engine on synthetic bars ----------------------------------


def _bars(drift_per_minute: float, *, end: datetime, volume_boost: float = 1.0) -> pd.DataFrame:
    """60 completed one-minute bars ending at ``end`` (bar start time)."""
    index = pd.date_range(end=end, periods=60, freq="1min")
    close = [100.0 * (1.0 + drift_per_minute) ** i for i in range(60)]
    volume = [1000.0] * 55 + [1000.0 * volume_boost] * 5
    return pd.DataFrame({"Close": close, "Volume": volume}, index=index)


def test_end_to_end_with_real_engine_results() -> None:
    last_bar = datetime(2026, 11, 4, 11, 29, tzinfo=IST)
    frames = {
        "FAST.NS": _bars(0.0010, end=last_bar, volume_boost=3.0),
        "SLOW.BO": _bars(0.0002, end=last_bar),
        "FLAT.NS": _bars(0.0, end=last_bar),
        "OLDD.NS": _bars(0.0010, end=last_bar - timedelta(hours=1)),
        "NONE.BO": None,
    }

    results = compute_momentum_batch(frames, as_of=AS_OF)
    ranking = rank_momentum(results)
    skipped = unranked_table(results)

    assert results["OLDD.NS"].status == STATUS_STALE
    assert results["NONE.BO"].status == STATUS_INSUFFICIENT
    assert list(ranking["Symbol"])[:2] == ["FAST", "SLOW"]
    assert ranking.loc[0, "Momentum strength"] > ranking.loc[1, "Momentum strength"]
    assert set(skipped["Symbol"]) == {"OLDD", "NONE"}
    assert not set(ranking["Symbol"]) & set(skipped["Symbol"])
    for ticker, result in results.items():
        if result.is_scored:
            shown = ranking.loc[ranking["Symbol"].eq(bare_symbol(ticker)), "Momentum strength"]
            assert shown.item() == round(result.score, 1)


def test_ranking_uses_only_information_known_at_as_of() -> None:
    last_bar = datetime(2026, 11, 4, 11, 29, tzinfo=IST)
    clean = _bars(0.0005, end=last_bar)
    poisoned = pd.concat(
        [
            clean,
            pd.DataFrame(
                {"Close": [500.0, 900.0], "Volume": [9e9, 9e9]},
                index=pd.date_range(last_bar + timedelta(minutes=1), periods=2, freq="1min"),
            ),
        ]
    )

    a = rank_momentum(compute_momentum_batch({"AAA.NS": clean}, as_of=AS_OF))
    b = rank_momentum(compute_momentum_batch({"AAA.NS": poisoned}, as_of=AS_OF))

    pd.testing.assert_frame_equal(a, b)
    assert (
        compute_momentum(poisoned, as_of=AS_OF).score == compute_momentum(clean, as_of=AS_OF).score
    )
