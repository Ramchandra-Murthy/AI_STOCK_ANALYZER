# Market Scanner Performance Diagnostics

The market scanner records stage timings and per-exchange data coverage on the
returned DataFrame. Use the profiling CLI to capture those values in a
reproducible JSON report:

```bash
python scripts/profile_market_scanner.py --exchange "NSE + BSE"
python scripts/profile_market_scanner.py --exchange NSE
python scripts/profile_market_scanner.py --exchange BSE
```

The report includes:

- Total wall-clock time for the invocation.
- Universe construction, screening, analysis download, and local analysis
  durations when those stages ran.
- The slowest measured stage, excluding total duration.
- Per-exchange candidate counts, requested tickers, returned histories,
  coverage percentage, empty download chunks, cached failures, rejected stale
  or unknown timestamps, completed analyses, and final rows.
- An explicit `NO_RESULTS` status when a scan returns no ranked rows. A scan
  with no rows is not automatically a scanner failure; inspect coverage and
  timings to determine whether data was unavailable or candidates were
  rejected by validation.

## Interpreting results

Compare repeated runs with the same exchange selection and similar market-data
conditions. Yahoo Finance response times vary with network conditions,
provider throttling, and symbol availability. Do not treat a single run as a
stable benchmark.

The scanner's historical screening and technical analysis use daily Yahoo
Finance candles. This report does not establish tick-level freshness or
intraday execution latency.

The CLI performs a real scan and therefore makes external market-data
requests. Unit tests exercise report generation with synthetic results and do
not call Yahoo Finance.
