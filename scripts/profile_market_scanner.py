"""Run the market scanner once and emit a machine-readable performance report.

Usage:
    python scripts/profile_market_scanner.py --exchange "NSE + BSE"
"""

from __future__ import annotations

import argparse
import json
import time
from typing import Any

from scanner.market_scanner import market_scan

TIMING_KEYS = (
    "universe_build_seconds",
    "screen_seconds",
    "analysis_download_seconds",
    "analysis_seconds",
)


def build_report(result: Any, elapsed_seconds: float) -> dict[str, Any]:
    """Build a JSON-safe summary from a scanner result and its diagnostics."""
    attrs = getattr(result, "attrs", {}) or {}
    timings = attrs.get("scanner_timings", {})
    coverage = attrs.get("scanner_coverage", {})
    rows = len(result)

    stage_timings = {
        key: round(float(timings[key]), 6)
        for key in TIMING_KEYS
        if key in timings
    }
    slowest_stage = (
        max(stage_timings, key=stage_timings.get) if stage_timings else None
    )

    exchange_coverage = {}
    for exchange, values in coverage.items():
        values = values or {}
        requested = int(values.get("tickers_requested", 0) or 0)
        returned = int(values.get("histories_returned", 0) or 0)
        exchange_coverage[exchange] = {
            "candidates": int(values.get("candidates", 0) or 0),
            "tickers_requested": requested,
            "histories_returned": returned,
            "history_coverage_pct": round(100 * returned / max(1, requested), 1),
            "screen_chunks_requested": int(values.get("screen_chunks_requested", 0) or 0),
            "screen_chunks_empty": int(values.get("screen_chunks_empty", 0) or 0),
            "cached_failures_skipped": int(values.get("cached_failures_skipped", 0) or 0),
            "stale_data_rejected": int(values.get("stale_data_rejected", 0) or 0),
            "unknown_timestamp_rejected": int(
                values.get("unknown_timestamp_rejected", 0) or 0
            ),
            "future_timestamp_rejected": int(
                values.get("future_timestamp_rejected", 0) or 0
            ),
            "analyses_completed": int(values.get("analyses_completed", 0) or 0),
            "final_rows": int(values.get("final_rows", 0) or 0),
        }

    return {
        "status": "RESULTS" if rows else "NO_RESULTS",
        "rows_returned": rows,
        "elapsed_seconds": round(float(elapsed_seconds), 6),
        "scanner_timings": stage_timings,
        "slowest_stage": slowest_stage,
        "scanner_coverage": exchange_coverage,
        "diagnostics_available": bool(timings or coverage),
        "data_note": "Scanner history is daily Yahoo Finance data, not tick-live data.",
    }


def main() -> int:
    """Execute one scan and print its performance report as JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exchange",
        default="NSE + BSE",
        choices=("NSE", "BSE", "NSE + BSE"),
        help="Exchange universe to scan (default: NSE + BSE).",
    )
    args = parser.parse_args()

    started = time.perf_counter()
    result = market_scan(args.exchange)
    elapsed = time.perf_counter() - started
    print(json.dumps(build_report(result, elapsed), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
