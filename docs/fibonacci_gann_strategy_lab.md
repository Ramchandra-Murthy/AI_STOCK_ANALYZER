# Fibonacci & Gann Strategy Lab

## Status

This is an isolated, calculation-only foundation. It is not connected to Streamlit pages, market-data providers, scanners, portfolio services, or broker APIs. No orders are submitted.

## Current calculations

- Fibonacci retracements for an upward swing: `H - ratio * (H - L)` at 23.6%, 38.2%, 50%, 61.8%, and 78.6%.
- Fibonacci upside extensions beyond the swing high: `H + ratio * (H - L)` at 1.000x, 1.272x, 1.618x, 2.000x, and 2.618x.
- Gann eighths: nine levels from 0/8 through 8/8, inclusive.
- `Decimal` arithmetic and validation reject non-finite, non-positive, or incorrectly ordered swing prices.

The 50% retracement is a commonly used market convention, not a Fibonacci ratio. Extension conventions differ between charting tools; this module explicitly uses the beyond-high formula documented above.

## Planned next phases

1. Confirmed swing-point detection that avoids look-ahead bias.
2. Market-data freshness and OHLC integrity checks; no signal when data is unavailable or stale.
3. Confluence and price-action confirmation as candidate conditions, not guarantees.
4. Stop/target and position-risk calculation, including fees and slippage; enforce the configured risk ceiling.
5. Historical tests with realistic transaction costs, walk-forward/out-of-sample evaluation, and paper-trading only.
6. An optional, separate Streamlit page after the calculation and data tests pass.

## Risk note

A plotted level is not a buy/sell signal and does not demonstrate a profitable edge. For options, analyse the underlying first; option premium, implied volatility, time decay, spread, and lot size can make a technically plausible underlying setup unsuitable. Never trade when the estimated maximum loss exceeds the configured limit.
