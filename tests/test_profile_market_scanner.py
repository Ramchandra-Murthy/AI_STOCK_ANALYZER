from __future__ import annotations

import pandas as pd

from scripts.profile_market_scanner import _runtime_delta, build_report


def test_profile_report_includes_stage_percentages_and_coverage_totals() -> None:
    result = pd.DataFrame([{"Symbol": "RELIANCE", "Exchange": "NSE"}])
    result.attrs["scanner_timings"] = {
        "universe_build_seconds": 0.2,
        "screen_seconds": 1.5,
        "analysis_download_seconds": 0.8,
        "analysis_seconds": 0.5,
        "total_seconds": 3.0,
    }
    result.attrs["scanner_coverage"] = {
        "NSE": {
            "candidates": 100,
            "tickers_requested": 80,
            "histories_returned": 72,
            "screen_chunks_requested": 2,
            "screen_chunks_empty": 1,
            "analyses_completed": 1,
            "final_rows": 1,
            "stale_data_rejected": 2,
            "unknown_timestamp_rejected": 1,
            "future_timestamp_rejected": 0,
            "cached_failures_skipped": 3,
        },
        "BSE": {
            "candidates": 50,
            "tickers_requested": 40,
            "histories_returned": 40,
            "screen_chunks_requested": 1,
            "screen_chunks_empty": 0,
            "analyses_completed": 0,
            "final_rows": 0,
            "stale_data_rejected": 0,
            "unknown_timestamp_rejected": 0,
            "future_timestamp_rejected": 0,
            "cached_failures_skipped": 0,
        },
    }

    report = build_report(
        result,
        3.2,
        cpu_seconds=1.6,
        runtime_delta={"batch_requests": 3, "cache_hits": 5},
    )

    assert report["status"] == "RESULTS"
    assert report["slowest_stage"] == "screen_seconds"
    assert report["stage_wall_time_pct"]["screen_seconds"] == 46.9
    assert report["coverage_totals"]["tickers_requested"] == 120
    assert report["coverage_totals"]["histories_returned"] == 112
    assert report["coverage_totals"]["history_coverage_pct"] == 93.3
    assert report["data_quality"]["rejected_stale_or_unknown_histories"] == 3
    assert report["data_quality"]["has_partial_history_coverage"] is True
    assert report["market_data_runtime_delta"]["batch_requests"] == 3


def test_profile_report_handles_no_results_and_missing_diagnostics() -> None:
    result = pd.DataFrame()
    report = build_report(result, 0.25)

    assert report["status"] == "NO_RESULTS"
    assert report["rows_returned"] == 0
    assert report["diagnostics_available"] is False
    assert report["slowest_stage"] is None
    assert report["coverage_totals"]["history_coverage_pct"] == 0.0


def test_runtime_delta_never_reports_negative_counter_values() -> None:
    delta = _runtime_delta(
        {"scan_calls": 4, "batch_requests": 8, "total_scan_seconds": 3.5},
        {"scan_calls": 2, "batch_requests": 10, "total_scan_seconds": 4.0},
    )

    assert delta == {
        "scan_calls": 0,
        "batch_requests": 2,
        "single_symbol_requests": 0,
        "provider_errors": 0,
        "cache_hits": 0,
        "cache_misses": 0,
        "total_scan_seconds": 0.5,
    }
