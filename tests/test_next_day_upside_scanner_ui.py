"""Integration tests for the Next-Day Upside Scanner Streamlit page."""

# Ruff cannot reliably classify the Streamlit testing import with this module alias.
# ruff: noqa: I001

from __future__ import annotations

import json
import pathlib
from datetime import date, datetime

import pandas as pd
import streamlit.testing.v1 as streamlit_testing

import scanner.next_day_movers as movers
import scanner.next_day_movers_eval as movers_eval
import scanner.next_day_paper_log as paper_log
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


# --------------------------------------------------------------------------- scope and state


def test_scope_assumptions_and_limitations_are_visible_before_any_run() -> None:
    app = streamlit_testing.AppTest.from_file(PAGE).run()

    assert not app.exception
    assert any("Scope, assumptions" in expander.label for expander in app.expander)
    text = " ".join(markdown.value for markdown in app.markdown)
    for expected in ("Universe:", "Cutoff:", "Not scored:", "Survivorship"):
        assert expected in text


def test_changing_the_selection_after_a_run_warns_that_the_result_is_stale(monkeypatch) -> None:
    monkeypatch.setattr(
        movers, "scan_next_day_movers", lambda *a, **k: _result("OK", (_candidate(),))
    )

    app = streamlit_testing.AppTest.from_file(PAGE).run()
    app.button[0].click().run()
    assert not any("Run it again to refresh" in warning.value for warning in app.warning)

    app.radio[0].set_value("NSE").run()

    assert not app.exception
    assert any("Run it again to refresh" in warning.value for warning in app.warning)


def test_each_exchange_mode_is_passed_to_the_scanner(monkeypatch) -> None:
    seen: list[tuple[str, ...]] = []

    def fake_scan(config, *args, **kwargs):
        seen.append(config.exchanges)
        return _result("OK", (_candidate(),))

    monkeypatch.setattr(movers, "scan_next_day_movers", fake_scan)
    app = streamlit_testing.AppTest.from_file(PAGE).run()
    for choice in ("NSE", "BSE", "NSE + BSE"):
        app.radio[0].set_value(choice).run()
        app.button[0].click().run()
        assert not app.exception

    assert seen == [("NSE",), ("BSE",), ("NSE", "BSE")]


def test_shortlist_size_is_passed_to_the_scanner(monkeypatch) -> None:
    sizes: list[int] = []

    def fake_scan(config, *args, **kwargs):
        sizes.append(config.top_n)
        return _result("OK", (_candidate(),))

    monkeypatch.setattr(movers, "scan_next_day_movers", fake_scan)
    app = streamlit_testing.AppTest.from_file(PAGE).run()
    app.slider[0].set_value(35).run()
    app.button[0].click().run()

    assert sizes == [35]


def _evaluation_result() -> movers_eval.WalkForwardResult:
    return movers_eval.WalkForwardResult(
        summary=pd.DataFrame({"mean_bps": [1.0]}, index=["Score top-k, net of costs"]),
        folds=pd.DataFrame({"fold": [1], "days": [10]}),
        quintiles=pd.DataFrame({"mean_o2c_bps": [0.5]}),
        daily=pd.DataFrame(),
        coverage={
            "symbols_requested": 40,
            "symbols_used": 38,
            "history_start": "2021-11-01",
            "history_end": "2026-11-03",
            "dates_evaluated": 1200,
        },
        assessment={
            "edge_supported": False,
            "verdict": "No evidence of a predictive edge under the pre-registered rule.",
            "rule": "fixed rule",
            "checks": {"enough_days": True},
        },
        round_trip_cost_bps=14.5,
    )


def test_evaluation_shows_period_universe_cost_and_the_negative_verdict(monkeypatch) -> None:
    monkeypatch.setattr(movers_eval, "evaluate_from_provider", lambda *a, **k: _evaluation_result())

    app = streamlit_testing.AppTest.from_file(PAGE).run()
    app.button[1].click().run()

    assert not app.exception
    assert any("No evidence of a predictive edge" in error.value for error in app.error)
    text = " ".join(markdown.value for markdown in app.markdown)
    assert "2021-11-01 to 2026-11-03" in text
    assert "38 of 40" in text
    assert "14.5 bps" in text


# --------------------------------------------------------------------------- paper log tab


def _future_result() -> ScanResult:
    """A shortlist for a far-future session so recording never depends on the wall clock."""
    cutoff = datetime(2099, 1, 4, 15, 30, tzinfo=IST)
    base = _result("OK", (_candidate(),))
    candidate = Candidate(
        **{
            **base.candidates[0].__dict__,
            "prediction_cutoff": cutoff,
            "target_business_date": date(2099, 1, 5),
            "data_timestamp": date(2099, 1, 4),
        }
    )
    return ScanResult(
        **{
            **base.__dict__,
            "candidates": (candidate,),
            "prediction_cutoff": cutoff,
            "target_business_date": date(2099, 1, 5),
        }
    )


def test_paper_tab_saves_once_and_never_overwrites(monkeypatch, tmp_path) -> None:
    log = tmp_path / "log.jsonl"
    monkeypatch.setattr(paper_log, "DEFAULT_LOG_PATH", log)
    monkeypatch.setattr(movers, "scan_next_day_movers", lambda *a, **k: _future_result())

    app = streamlit_testing.AppTest.from_file(PAGE).run()
    assert any("not live-trading performance" in info.value for info in app.info)

    app.button[2].click().run()  # nothing scanned yet
    assert any("Run a scan first" in warning.value for warning in app.warning)
    assert not log.exists()

    app.button[0].click().run()
    app.button[2].click().run()
    assert any("Saved the shortlist" in success.value for success in app.success)
    records = [json.loads(line) for line in log.read_text().splitlines()]
    assert len(records) == 1 and records[0]["label"] == paper_log.PAPER_LABEL

    app.button[2].click().run()
    assert any("already_recorded" in warning.value for warning in app.warning)
    assert len(log.read_text().splitlines()) == 1


def test_paper_tab_reports_settlement_provider_errors_without_recording(monkeypatch, tmp_path):
    monkeypatch.setattr(paper_log, "DEFAULT_LOG_PATH", tmp_path / "log.jsonl")
    monkeypatch.setattr(
        paper_log,
        "settle_outcomes",
        lambda *a, **k: paper_log.SettleReport(errors=("ConnectionError: provider down",)),
    )

    app = streamlit_testing.AppTest.from_file(PAGE).run()
    app.button[3].click().run()

    assert not app.exception
    assert any("Provider error, nothing recorded" in error.value for error in app.error)
    assert not (tmp_path / "log.jsonl").exists()
