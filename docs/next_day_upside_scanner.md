# Next-business-day upside candidate scanner

Research and paper-trading use only. This tool ranks liquid NSE/BSE stocks against each
other using information available at the last completed session's close. It does not
predict returns, does not output probabilities, places no orders and gives no buy or sell
recommendations.

- Scanner: `scanner/next_day_movers.py`
- Walk-forward evaluation: `scanner/next_day_movers_eval.py`
- Page: `pages/Next_Day_Upside_Scanner.py`
- Calendar helpers added to the existing `services/market_calendar.py`

## What the score means

`score` is a 0-100 **ranking score**. It orders stocks within a single run only.

- It is **not** a probability that a stock rises. It has not been calibrated against
  realised outcomes, so "score 80" does not mean "80% chance".
- Scores from different dates are not comparable, because each factor is a cross-sectional
  percentile rank on that date.
- A high score is a reason to look at a stock, not a recommendation to trade it.
- Every result carries `score_type = "ranking_score_0_100_not_a_probability"`.

### How it is built

Each factor is converted to a percentile rank across the eligible stocks, then combined
with fixed a-priori weights (they are not fitted to data and sum to 1.0):

| Factor | Weight |
| --- | --- |
| 1-day / 5-day / 20-day return | 0.05 / 0.10 / 0.15 |
| Close location in the day's range | 0.07 |
| Close vs prior 20-day high (breakout proximity) | 0.08 |
| Up-day volume surge / turnover surge vs 20-day average | 0.07 / 0.08 |
| Close vs 20-day SMA; 20-day vs 50-day SMA | 0.05 / 0.05 |
| RSI(14) closeness to 60 | 0.05 |
| MACD histogram / close | 0.05 |
| 5-day and 20-day return vs the exchange index | 0.06 / 0.06 |
| 5-day return vs same-sector peers in the scanned universe | 0.08 |

Penalties are then subtracted: volatility (ATR % of price, up to 15 points), overnight
gap risk (60-day gap standard deviation, up to 10 points) and over-extension (RSI above 80
or a 1-day gain above 8%, 5 points each). A stock needs at least 80% of the factor weight
available to be ranked; missing factors are never filled in.

## Inputs, calendar and the prediction cutoff

- **Calendar:** `resolve_prediction_cutoff` uses the repository calendar in
  `services/market_calendar.py` (`is_equity_trading_day`, `next_equity_trading_day`,
  `previous_equity_trading_day`). A run on a weekend, holiday or before the settled close
  (session close + 15 minutes) uses the previous session as the cutoff. A year without a
  configured holiday list raises `CalendarUnavailableError` and the scan reports
  `UNAVAILABLE` instead of guessing a target date.
- **Cutoff:** the regular-session close (15:30 IST) of the last completed session. Bars
  dated after it are dropped before any feature is computed.
- **Universe:** the curated NSE and BSE lists in `scanner/universe.py`, validated and
  de-duplicated. BSE symbols are six-digit scrip codes, mapped through the existing
  `scanner/dynamic_universe.py` helpers. By default a BSE listing that pairs with an NSE
  listing of the same company is dropped to avoid double counting.
- **Data:** daily OHLCV from Yahoo Finance via `services/resilient_market_data.py`. It is
  delayed, auto-adjusted and can contain gaps or revisions. It is not an exchange feed.
- **Reused indicators:** SMA, RSI, MACD and ATR come from the `indicators` package; liquidity
  floors come from `scanner/dynamic_universe.py`; sectors from `services/sector_mapping.py`.

### What is excluded, and why it is reported

Symbols are excluded with an explicit reason, never silently: no data, missing columns,
non-positive or internally inconsistent prices, negative volume, too many invalid recent
rows, stale bars, insufficient history, price below the minimum, low median turnover,
frequent zero-volume days, large data gaps, unverified extreme moves and, when the
surveillance lookup works, surveillance-flagged names. If the provider fails, the status is
`UNAVAILABLE` with the error shown. Stale data is never substituted. If too few symbols
remain or universe coverage is low, the result is `UNAVAILABLE` or `DEGRADED`.

### Not scored

These have no verified source in this repository, so they are **not** used and are listed
on every result: delivery percentage, news and corporate-action events, and sector index
series. Sector strength uses same-sector peers in the scanned universe only and needs at
least three peers.

## Walk-forward evaluation

For each historical date `t`, the evaluation rebuilds the cross-section as the live scanner
would at the close of `t`, using the same cleaning, `compute_feature_frame`, eligibility
filters and `score_panel`, then looks one market session ahead. Features use only bars
dated on or before `t`; outcomes are never used to build features or choose weights.

- **Primary outcome:** next-session open to close, net of round-trip costs and slippage
  (a scan finished after the close cannot buy at that close). Costs come from the
  repository's `IndiaEquityCostModel` with approximate, configurable defaults; verify them
  against your broker and the current statutory rates.
- **Secondary outcome:** next-session close to close, gross, shown as the descriptive
  "moved upward" measure because it is not obtainable after the cutoff.
- **Reported:** top-k hit rate and precision with the base rate, mean next-session return,
  benchmark-relative performance (index and equal-weight eligible universe), maximum
  drawdown, score-quintile table, sequential fold stability, and sample coverage.
- **Baselines:** the market index, the equal-weight eligible universe and a plain 5-day
  momentum ranking.
- **Edge rule (fixed before looking at results):** at least 120 evaluated days; the 95%
  block-bootstrap lower bound of mean daily net excess return vs the eligible universe is
  above zero; at least 60% of folds have positive net excess; mean net return is positive.
  Meeting the rule is necessary but not sufficient evidence of an edge. If it is not met the
  report says "No evidence of a predictive edge" and the score should not be relied on.

## Limitations

- **Survivorship bias:** the universe is today's curated list; delisted or dropped names
  are absent, which flatters results.
- **Data quality:** delayed, adjusted Yahoo data with possible gaps and bad ticks, not a
  point-in-time exchange database.
- **Idealised fills:** no auction impact, partial fills, circuit-limit lock-ins or rejected
  orders; costs are approximate.
- **Tested once:** one fixed configuration was evaluated; tuning weights on these results
  would be data snooping.
- **Live filters not backtested:** historical surveillance flags, delivery, news and
  corporate actions are unavailable point-in-time, so the backtest scores the ranking only.
- **Regime and capacity:** equal-weight daily rebalancing ignores capacity and impact, and
  the sample covers one market regime, so out-of-sample is not out-of-regime.
- A hit rate near the base rate (roughly half of stocks rise on a typical day) means no
  skill. Always compare precision with the base rate.

## Usage

```python
from scanner.next_day_movers import ScannerConfig, scan_next_day_movers

result = scan_next_day_movers(ScannerConfig(top_n=20))
print(result.status, result.target_business_date)
print(result.to_frame())
```

```python
from scanner.next_day_movers_eval import EvalConfig, evaluate_from_provider

report = evaluate_from_provider(EvalConfig(top_k=10))
print(report.assessment["verdict"])
print(report.summary)
```

Both functions accept an injected `fetcher` for offline use and tests. The Streamlit page
is registered in `app.py` under the scanners group and fetches data only when a button is
pressed.
