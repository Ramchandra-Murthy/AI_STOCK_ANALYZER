"""Integration tests for the Next-Day Upside Scanner Streamlit page."""

# Ruff cannot reliably classify the Streamlit testing import with this module alias.
# ruff: noqa: I001

from __future__ import annotations

import pathlib
from datetime import date, datetime

import streamlit.testing.v1 as streamlit_testing

import scanner.next_day_movers as movers
import scanner.next_day_movers_eval as movers_eval
from scanner.next_day_movers import (
    DATA_SOURCE,
    IST,
    UNSUPPORTED_DATA,
    Candidate,
    ExclusionRecord,
    ScanResult,
)

PAGE = pathlib.Path(__file__).resolve().parents[1] / "pages" / "Next_Day_Upside_Scanner.py"
CUTOFF = datetime(2026, 11, 3, 15, 30, tzinfo=IST)
TARGET = date(2026, 11, 4)


def _candidate() -> Candidate:
    return Candidate(
        rank=1,
        symbol="RELIANCE",
        exchange="NSE",
        ticker="RELIANCE.NS",
        score=71.2,
        positive_score=80.0,
        penalty=8.8,
        factor_coverage=1.0,
        supporting_factors=("5-day return: +3.0% (percentile 90)",),
        risk_flags=("high_volatility",),
        last_close=1500.0,
        data_timestamp=date(2026, 11, 3),
        data_source=DATA_SOURCE,
        prediction_cutoff=CUTOFF,
        target_business_date=TARGET,
    )


def _result(status: str, candidates: tuple[Candidate, ...]) -> ScanResult:
    return ScanResult(
        status=status,
        candidates=candidates,
        excluded=(ExclusionRecord("XYZ", "NSE", "XYZ.NS", ("low_liquidity",)),),
        prediction_cutoff=CUTOFF,
        target_business_date=TARGET,
        generated_at=CUTOFF,
        data_quality={"universe_requested": 10, "eligible": 9, "coverage_pct": 90.0},
        unavailable_data=UNSUPPORTED_DATA,
        warnings=("a data warning",) if status != "OK" else (),
    )


def test_page_shows_disclaimer_and_waits_for_the_user_before_fetching(monkeypatch) -> None:
    def fail(*args, **kwargs):
        raise AssertionError("the page must not fetch data on load")

    monkeypatch.setattr(movers, "scan_next_day_movers", fail)

    app = streamlit_testing.AppTest.from_file(PAGE).run()

    assert not app.exception
    assert any("NOT probabilities" in warning.value for warning in app.warning)
    assert any("Run the scan after the market close" in info.value for info in app.info)


def test_page_renders_ranked_shortlist_with_cutoff_and_target(monkeypatch) -> None:
    monkeypatch.setattr(
        movers, "scan_next_day_movers", lambda *a, **k: _result("OK", (_candidate(),))
    )

    app = streamlit_testing.AppTest.from_file(PAGE).run()
    app.button[0].click().run()

    assert not app.exception
    assert any("Ranking produced" in success.value for success in app.success)
    metric_labels = {metric.label for metric in app.metric}
    assert {"Prediction cutoff (IST)", "Target business date"} <= metric_labels
    shortlist = app.dataframe[0].value
    assert list(shortlist["Symbol"]) == ["RELIANCE"]
    assert "Score (0-100, not a probability)" in shortlist.columns


def test_page_reports_unavailable_scan_without_a_shortlist(monkeypatch) -> None:
    monkeypatch.setattr(movers, "scan_next_day_movers", lambda *a, **k: _result("UNAVAILABLE", ()))

    app = streamlit_testing.AppTest.from_file(PAGE).run()
    app.button[0].click().run()

    assert not app.exception
    assert any("No ranking was produced" in error.value for error in app.error)
    assert any("a data warning" in warning.value for warning in app.warning)


def test_evaluation_failure_is_shown_as_an_error_not_hidden(monkeypatch) -> None:
    def failing(*args, **kwargs):
        raise movers_eval.EvaluationDataError("market-data provider failed: boom")

    monkeypatch.setattr(movers_eval, "evaluate_from_provider", failing)

    app = streamlit_testing.AppTest.from_file(PAGE).run()
    app.button[1].click().run()

    assert not app.exception
    assert any("Evaluation unavailable" in error.value for error in app.error)
