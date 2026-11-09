# Intraday momentum engine

`scanner/momentum_engine.py` turns one-minute bars into a transparent 0-100 **momentum
strength** score per stock. It is pure computation: no network, no Streamlit, no global
state. Fetching, ranking and history live in later layers; the existing
`components/top10_live.py` is unchanged.

The score describes how strong and how well confirmed the *recent* move is. It is **not** a
probability, a forecast, or a buy/sell signal. Every result carries
`score_type = "momentum_strength_0_100_not_a_probability"`.

## Inputs

`compute_momentum(frame, as_of=..., config=..., symbol=...)` takes a DataFrame with a
datetime index and a `Close` column (`Volume` optional). Naive timestamps are taken as IST;
timezone-aware ones are converted. `as_of` defaults to now (IST); pass it explicitly to replay
or test. `compute_momentum_batch(frames, as_of=...)` scores many symbols against one shared
`as_of`, each independently.

## Score

| Component | Max | What it measures |
| --- | --- | --- |
| Magnitude 1m / 5m / 10m / 15m | 10 / 20 / 15 / 15 | Window return vs a fixed full-credit scale (0.5% / 1.0% / 1.5% / 2.0%), dominant side only |
| Confirmation | 20 | Share of window weight agreeing with the direction (UP or DOWN only) |
| Volume | 20 | Mean volume of the last 5 completed bars vs the median of the 30 bars before them: 1x earns 0, 2x or more earns full (UP or DOWN only) |

Windows opposing the dominant side earn no magnitude points. Volume and confirmation earn
nothing when the direction is MIXED or NEUTRAL: a volume surge in a conflicted move is
reported (`volume_state`) but is not a confirmation.

If a component cannot be computed (no volume for an index, a window with no bar) its points
are removed and the score is rescaled over what remains. `score_coverage` is the share of
the 100 points that were computable (1.0 = everything), and the status becomes `PARTIAL`.
Nothing is ever filled in. `components` lists every piece with its points and a one-line
explanation.

## Direction

Each available window votes UP, DOWN, or flat (|return| within 0.02%, inclusive), weighted by
its magnitude weight (10 / 20 / 15 / 15).

- **NEUTRAL**: every available window is flat (or none is available).
- **UP / DOWN**: one side holds at least 75% of the non-flat weight.
- **MIXED**: both sides are present and neither reaches 75%.

`timeframe_confirmation` is `FULL` (direction UP/DOWN, all available windows agree, at least
3 available), `PARTIAL` (direction UP/DOWN, some windows disagree or fewer than 3 exist) or
`NONE` (MIXED/NEUTRAL).

## Status values

| Status | Meaning | Score |
| --- | --- | --- |
| `OK` | All four windows and volume available | yes |
| `PARTIAL` | At least 2 windows but a window or volume is missing | yes, with `score_coverage` < 1 |
| `STALE` | Latest completed bar older than 180 s | none |
| `INSUFFICIENT` | No data, no valid bars, or fewer than 2 usable windows | none |
| `INVALID` | No `Close` column | none |

## No look-ahead and data hygiene

- A bar stamped `t` is *complete* once `t + 1 minute <= as_of`. The forming bar and any later
  bar are dropped before any calculation, so a result never depends on information after
  `as_of` (tested by poisoning later bars and by replaying earlier moments).
- Only bars from the latest bar's IST calendar date are used, so an overnight gap is never read
  as intraday momentum and yesterday's volume never forms today's baseline.
- Window starts are found by *time* (the bar `w` minutes earlier, allowing a 1-minute gap), not
  by position, so missing minutes cannot stretch a window.
- Non-positive, non-finite and non-numeric prices are dropped, never repaired. A window
  return above 20% in absolute value is treated as an unverified bad tick and left unavailable.
- Duplicate timestamps keep the last row; unsorted input is sorted. The input frame is not
  modified.

## Assumptions and limitations

- All scales, weights and thresholds are fixed a priori and **not fitted** to outcomes. They
  are documented assumptions, and the score has **no demonstrated predictive value**; do not
  tune them to make results look better.
- The magnitude scales are the same for every stock. A 1% move is far more unusual for a large
  low-volatility stock than for a volatile small cap, so scores are not volatility-adjusted.
- Volume is provider-reported and can lag, be revised, or be missing for some tickers; yfinance
  one-minute volume is not an exchange-grade feed. Indices have no volume.
- Delayed or revised provider data affects every output; the engine can only detect staleness
  by bar timestamp. It does not know exchange holidays or session hours, so before the open or
  after the close results are `STALE` rather than "market closed".
- One-minute bars are noisy; the 1m window in particular reflects a single minute.
- Verified here on synthetic bars only. No live-data accuracy has been checked.

## Reproducing the tests

```bash
PYTHONPATH=. python -m pytest --import-mode=importlib -q tests/test_momentum_engine.py tests/test_momentum_ranking.py
ruff check scanner/momentum_engine.py scanner/momentum_ranking.py
black --check scanner/momentum_engine.py scanner/momentum_ranking.py
```

## Ranking and scanner integration

`scanner/momentum_ranking.py` orders engine results; it never scores anything itself.

- **Who is ranked.** Only results with a real score (`OK` or `PARTIAL`). `STALE`,
  `INSUFFICIENT`, `INVALID` and symbols the provider never returned are excluded and reported
  (`summarize_momentum`, `unranked_table`), so a coverage gap is visible.
- **Order.** Momentum strength (descending, ties at 6 decimals), then timeframe confirmation
  (`FULL` before `PARTIAL` before `NONE`), then volume ratio (higher first, missing last), then
  ticker. The result does not depend on input order.
- **Exchanges.** Keyed by Yahoo ticker, so the same company on NSE and BSE is two rows.
  `Exchange rank` is the position among all scored symbols of that exchange; the exchange
  filter in the scanner only hides rows and renumbers `Rank` for what is shown.
- **Scanner.** `components/top10_live.py` scores every downloaded symbol at the scan time and
  stores the ranking on the scan result. The movers table is still ordered by absolute 1-minute
  move and keeps its own simpler "Momentum score"; the new panel is labelled "Momentum
  strength" so the two are not confused. A failure in this step is reported in the panel and the
  provider diagnostics and never fails the scan.
- The same limitations as above apply: fixed, unfitted weights; no demonstrated predictive
  value; not volatility adjusted; verified on synthetic bars only.
