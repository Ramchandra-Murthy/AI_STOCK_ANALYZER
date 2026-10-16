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
- The integration test validates OHLC bars, detects confirmed pivots, then passes a confirmed low/high pair into confluence analysis. This is a test workflow only; no live-data connection is added.
- Position sizing floors quantity to whole units and takes the tighter of the available-capital limit and estimated-loss limit. Estimated per-unit risk includes the entry-to-stop distance plus a caller-supplied estimate for round-trip fees and slippage. It rejects invalid inputs and refuses a size when one unit breaches the loss ceiling.

The 50% retracement is a commonly used market convention, not a Fibonacci ratio. Extension conventions differ between charting tools; this module explicitly uses the beyond-high formula documented above. Swing detection expects callers to validate their OHLC bars first. Confluence is descriptive geometry, not statistical evidence that a level will hold.

## Examples

```python
from modules.fibonacci_gann import calculate_position_size, find_confluence_zones

zones = find_confluence_zones(800, 1000, tolerance="2")
for zone in zones:
    print(zone.low, zone.high, zone.center)

# Illustrative long-position sizing; costs are estimated, not broker-verified.
size = calculate_position_size(
    entry_price="100",
    stop_price="95",
    capital="10000",
    max_loss="500",
    cost_per_unit="1",
)
print(size.quantity, size.estimated_loss, size.capital_required)
```

The confluence tolerance uses the same price units as the swing. The risk helper models long positions in whole units only; it does not calculate exchange-specific charges, options lot sizes, variable turnover taxes, gap risk, or guaranteed stop execution. Supply a conservative round-trip cost estimate and verify instrument-specific costs separately.

## Planned next phases

1. Historical tests with realistic transaction costs, walk-forward/out-of-sample evaluation, and paper-trading only.
2. An optional, separate Streamlit page only after calculation, data-quality, and risk tests pass.

## Risk note

A plotted level or confluence zone is not a buy/sell signal and does not demonstrate a profitable edge. For options, analyse the underlying first; option premium, implied volatility, time decay, spread, and lot size can make a technically plausible underlying setup unsuitable. Never trade when the estimated maximum loss exceeds the configured limit. The conservative example budget is ₹10,000 trading capital and ₹500 maximum acceptable loss per trade including costs.
