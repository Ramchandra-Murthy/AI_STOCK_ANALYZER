# Fibonacci & Gann Strategy Lab

## Status

This remains an isolated analysis-only module. It is not connected to Streamlit pages, market-data providers, scanners, portfolio services, or broker APIs. No orders are submitted.

## Current calculations and safeguards

- Fibonacci retracements for an upward swing: `H - ratio * (H - L)` at 23.6%, 38.2%, 50%, 61.8%, and 78.6%.
- Fibonacci upside extensions beyond the swing high: `H + ratio * (H - L)` at 1.000x, 1.272x, 1.618x, 2.000x, and 2.618x.
- Gann eighths: nine levels from 0/8 through 8/8, inclusive.
- `Decimal` arithmetic and validation reject non-finite, non-positive, or incorrectly ordered swing prices.
- OHLC integrity and freshness checks reject empty, stale, future-dated, unordered, timezone-naive, or internally inconsistent candle data.
- Confirmed swing detection requires both left- and right-side candles; the latest right-side window is not emitted as confirmed, reducing look-ahead bias. Equal highs/lows are excluded rather than arbitrarily selecting a plateau.
- The confluence engine groups nearby calculated levels using an explicit absolute price tolerance. It reports the zone's low, high, midpoint, and contributing level family/labels. Single levels are not reported as confluence; exact overlaps can be found with zero tolerance.
- An integration test validates a recent OHLC series, detects only confirmed pivots, then passes a confirmed low/high pair into confluence analysis. This is a test workflow only; no runtime pipeline or live-data connection is added.

The 50% retracement is a commonly used market convention, not a Fibonacci ratio. Extension conventions differ between charting tools; this module explicitly uses the beyond-high formula documented above. Swing detection expects callers to validate their OHLC bars first. Confluence is descriptive geometry, not statistical evidence that a level will hold.

## Example

```python
from modules.fibonacci_gann import find_confluence_zones

zones = find_confluence_zones(800, 1000, tolerance="2")
for zone in zones:
    print(zone.low, zone.high, zone.center)
    print([(level.family, level.label, level.price) for level in zone.levels])
```

The tolerance is measured in the same price units as the swing. Choose it deliberately for the instrument and price scale; the library does not infer tick size or market context.

## Planned next phases

1. Stop/target and position-risk calculation, including fees and slippage; enforce the configured risk ceiling.
2. Historical tests with realistic transaction costs, walk-forward/out-of-sample evaluation, and paper-trading only.
3. An optional, separate Streamlit page only after calculation, data-quality, and risk tests pass.

## Risk note

A plotted level or confluence zone is not a buy/sell signal and does not demonstrate a profitable edge. For options, analyse the underlying first; option premium, implied volatility, time decay, spread, and lot size can make a technically plausible underlying setup unsuitable. Never trade when the estimated maximum loss exceeds the configured limit. For the conservative test budget, retain ₹10,000 trading capital and ₹500 maximum acceptable loss per trade including costs.
