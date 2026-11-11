# Market Scanner Performance Diagnostics

The market scanner records stage timings and per-exchange data coverage on the
returned DataFrame. Use the profiling CLI to capture a reproducible JSON report:

```bash
python scripts/profile_market_scanner.py --exchange "NSE + BSE"
python scripts/profile_market_scanner.py --exchange NSE --output nse-profile.json
python scripts/profile_market_scanner.py --exchange BSE --output bse-profile.json
```

The report includes:

- End-to-end wall-clock and process CPU time, plus their ratio.
- Universe construction, screening, analysis download, and local analysis
  durations, with each stage's share of total wall-clock time.
- The slowest measured stage, excluding total duration.
- Per-exchange and aggregate candidate counts, requested tickers, returned
  histories, coverage percentage, empty download chunks, cached failures,
  rejected stale/unknown/future timestamps, completed analyses, and final rows.
- Market-data runtime counter deltas for the invocation, including batch and
  single-symbol requests, cache hits/misses, provider errors, and fetch time.
- Explicit `RESULTS`, `NO_RESULTS`, or `SCAN_ERROR` status. A scan with no
  rows is not automatically a scanner failure; inspect coverage and timings to
  distinguish unavailable provider data from candidates rejected by validation.

## Interpreting results

Compare repeated runs with the same exchange selection and similar market-data
conditions. Yahoo Finance response times vary with network conditions,
provider throttling, and symbol availability. Do not treat a single run as a
stable benchmark.

The scanner's broad-market screening and technical analysis use daily Yahoo
Finance candles. This report does not establish tick-level freshness or
intraday execution latency. Runtime telemetry deltas are process-local and do
not aggregate across multiple Streamlit/ECS tasks.

The CLI performs a real scan and therefore makes external market-data
requests. Run it deliberately; do not schedule it at a high frequency. Unit
tests exercise report generation with synthetic results and do not call Yahoo
Finance.
