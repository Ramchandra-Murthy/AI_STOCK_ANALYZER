"""Profile one end-to-end NSE/BSE market scan and emit a JSON diagnostics report.

Usage:
    python scripts/profile_market_scanner.py --exchange "NSE + BSE"
    python scripts/profile_market_scanner.py --exchange NSE --output scanner-profile.json

The command performs a real market-data scan. It is intended for controlled
manual diagnostics, not a high-frequency scheduler or a tick-data benchmark.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any

from scanner.market_scanner import market_scan
from services.resilient_market_data import market_data_runtime_stats

TIMING_KEYS = (
    "universe_build_seconds",
    "screen_seconds",
    "analysis_download_seconds",
    "analysis_seconds",
)
RUNTIME_COUNTERS = (
    "scan_calls",
    "batch_requests",
    "single_symbol_requests",
    "provider_errors",
    "cache_hits",
    "cache_misses",
    "total_scan_seconds",
)


def _safe_number(value: Any) -> float:
    """Convert a diagnostic value to a finite non-negative float."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) and number >= 0 else 0.0


def _runtime_delta(before: dict[str, Any], after: dict[str, Any]) -> dict[str, int | float]:
    """Return process-local market-data counter deltas for this scan invocation."""
    delta: dict[str, int | float] = {}
    for key in RUNTIME_COUNTERS:
        difference = _safe_number(after.get(key, 0)) - _safe_number(before.get(key, 0))
        delta[key] = (
            round(max(0.0, difference), 6)
            if key == "total_scan_seconds"
            else int(max(0.0, difference))
        )
    return delta


def build_report(
    result: Any,
    elapsed_seconds: float,
    *,
    cpu_seconds: float = 0.0,
    runtime_delta: dict[str, int | float] | None = None,
) -> dict[str, Any]:
    """Build a JSON-safe performance, coverage, and data-quality summary."""
    attrs = getattr(result, "attrs", {}) or {}
    timings = attrs.get("scanner_timings", {}) or {}
    coverage = attrs.get("scanner_coverage", {}) or {}
    rows = len(result)

    stage_timings = {
        key: round(_safe_number(timings[key]), 6) for key in TIMING_KEYS if key in timings
    }
    slowest_stage = max(stage_timings, key=stage_timings.get) if stage_timings else None
    stage_percentages = {
        key: round(100.0 * value / max(_safe_number(elapsed_seconds), 1e-9), 1)
        for key, value in stage_timings.items()
    }

    exchange_coverage: dict[str, dict[str, int | float]] = {}
    totals = {
        "candidates": 0,
        "tickers_requested": 0,
        "histories_returned": 0,
        "screen_chunks_requested": 0,
        "screen_chunks_empty": 0,
        "analyses_completed": 0,
        "final_rows": 0,
        "stale_data_rejected": 0,
        "unknown_timestamp_rejected": 0,
        "future_timestamp_rejected": 0,
        "cached_failures_skipped": 0,
    }
    for exchange, raw_values in coverage.items():
        values = raw_values or {}
        requested = int(values.get("tickers_requested", 0) or 0)
        returned = int(values.get("histories_returned", 0) or 0)
        summary = {key: int(values.get(key, 0) or 0) for key in totals}
        summary["history_coverage_pct"] = round(100.0 * returned / max(1, requested), 1)
        exchange_coverage[str(exchange)] = summary
        for key in totals:
            totals[key] += summary[key]

    totals["history_coverage_pct"] = round(
        100.0 * totals["histories_returned"] / max(1, totals["tickers_requested"]), 1
    )
    rejected = (
        totals["stale_data_rejected"]
        + totals["unknown_timestamp_rejected"]
        + totals["future_timestamp_rejected"]
    )
    return {
        "status": "RESULTS" if rows else "NO_RESULTS",
        "rows_returned": rows,
        "elapsed_seconds": round(_safe_number(elapsed_seconds), 6),
        "cpu_seconds": round(_safe_number(cpu_seconds), 6),
        "cpu_to_wall_ratio": round(
            _safe_number(cpu_seconds) / max(_safe_number(elapsed_seconds), 1e-9), 3
        ),
        "scanner_timings": stage_timings,
        "stage_wall_time_pct": stage_percentages,
        "slowest_stage": slowest_stage,
        "scanner_coverage": exchange_coverage,
        "coverage_totals": totals,
        "data_quality": {
            "history_coverage_pct": totals["history_coverage_pct"],
            "rejected_stale_or_unknown_histories": rejected,
            "empty_screen_chunks": totals["screen_chunks_empty"],
            "has_partial_history_coverage": totals["histories_returned"]
            < totals["tickers_requested"],
        },
        "market_data_runtime_delta": runtime_delta or {},
        "diagnostics_available": bool(timings or coverage),
        "data_note": (
            "Scanner history is daily Yahoo Finance data, not tick-live data. "
            "Process-local telemetry deltas are not shared across application tasks."
        ),
    }


def main() -> int:
    """Execute one scan and print or save its performance report as JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--exchange",
        default="NSE + BSE",
        choices=("NSE", "BSE", "NSE + BSE"),
        help="Exchange universe to scan (default: NSE + BSE).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the JSON report; stdout remains the default.",
    )
    args = parser.parse_args()

    runtime_before = market_data_runtime_stats()
    wall_started = time.perf_counter()
    cpu_started = time.process_time()
    try:
        result = market_scan(args.exchange)
    except Exception as exc:
        elapsed = time.perf_counter() - wall_started
        cpu_elapsed = time.process_time() - cpu_started
        report = {
            "status": "SCAN_ERROR",
            "elapsed_seconds": round(elapsed, 6),
            "cpu_seconds": round(cpu_elapsed, 6),
            "error_type": type(exc).__name__,
            "error": str(exc)[:500],
            "market_data_runtime_delta": _runtime_delta(
                runtime_before, market_data_runtime_stats()
            ),
        }
        rendered = json.dumps(report, indent=2, sort_keys=True)
        if args.output:
            args.output.write_text(rendered + "\\n", encoding="utf-8")
        print(rendered)
        return 1

    elapsed = time.perf_counter() - wall_started
    cpu_elapsed = time.process_time() - cpu_started
    report = build_report(
        result,
        elapsed,
        cpu_seconds=cpu_elapsed,
        runtime_delta=_runtime_delta(runtime_before, market_data_runtime_stats()),
    )
    rendered = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(rendered + "\\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
