import pandas as pd

from scripts import profile_market_scanner


def test_build_report_includes_timings_and_exchange_coverage() -> None:
    result = pd.DataFrame([{"Symbol": "RELIANCE"}])
    result.attrs["scanner_timings"] = {
        "universe_build_seconds": 0.1,
        "screen_seconds": 2.5,
        "analysis_download_seconds": 0.4,
        "analysis_seconds": 0.2,
        "total_seconds": 3.3,
    }
    result.attrs["scanner_coverage"] = {
        "NSE": {
            "candidates": 100,
            "tickers_requested": 90,
            "histories_returned": 72,
            "screen_chunks_requested": 2,
            "screen_chunks_empty": 1,
            "cached_failures_skipped": 3,
            "stale_data_rejected": 2,
            "unknown_timestamp_rejected": 1,
            "future_timestamp_rejected": 0,
            "analyses_completed": 5,
            "final_rows": 1,
        }
    }

    report = profile_market_scanner.build_report(result, 3.4)

    assert report["status"] == "RESULTS"
    assert report["rows_returned"] == 1
    assert report["slowest_stage"] == "screen_seconds"
    assert report["scanner_coverage"]["NSE"]["history_coverage_pct"] == 80.0
    assert report["scanner_coverage"]["NSE"]["cached_failures_skipped"] == 3
    assert report["diagnostics_available"] is True


def test_build_report_handles_empty_scan_without_analysis_timings() -> None:
    result = pd.DataFrame()
    result.attrs["scanner_timings"] = {
        "universe_build_seconds": 0.01,
        "screen_seconds": 0.2,
        "total_seconds": 0.21,
    }
    result.attrs["scanner_coverage"] = {}

    report = profile_market_scanner.build_report(result, 0.22)

    assert report["status"] == "NO_RESULTS"
    assert report["rows_returned"] == 0
    assert report["slowest_stage"] == "screen_seconds"
    assert "analysis_download_seconds" not in report["scanner_timings"]


def test_build_report_fails_soft_when_diagnostics_are_missing() -> None:
    result = pd.DataFrame()

    report = profile_market_scanner.build_report(result, 0.05)

    assert report["status"] == "NO_RESULTS"
    assert report["diagnostics_available"] is False
    assert report["slowest_stage"] is None
    assert report["scanner_coverage"] == {}
