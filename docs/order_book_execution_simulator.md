# Order-book-aware execution simulator

The algorithmic_trading.order_book_execution module estimates the cost of
sweeping a validated aggregated Level-2 snapshot. It complements, rather than
replaces, the OHLCV square-root impact approximation.

## Method

- A buy consumes ask levels from best to worst; a sell consumes bid levels.
- Each level fills up to its displayed quantity until the requested quantity
  is filled or selected depth is exhausted.
- Results include per-level fills, executed notional, VWAP, remaining quantity,
  fill ratio, and levels touched.
- Implementation shortfall is measured against snapshot mid-price.
  Book-walk cost is measured against the best executable touch price.
- max_levels makes the visible-depth horizon explicit.

The caller must pass synchronized=True only when the feed/replay layer confirms
the snapshot is synchronized. A gap, invalid update, or replay buffer overflow
must keep the book unavailable for this estimate.

## Example

    estimate = estimate_order_book_execution(
        snapshot,
        side="buy",
        quantity=1_000,
        synchronized=replay.synchronized,
        max_levels=5,
    )

## Limitations

This is a static displayed-depth sweep, not a dynamic matching engine. It
assumes displayed quantities remain available and does not model queue priority,
hidden/iceberg liquidity, replenishment, cancellations, latency, market response,
fees, taxes, or adverse selection. It is not a guaranteed fill or live broker
estimate. Yahoo Finance OHLCV is not Level-2 data and must never be converted
into a fabricated order book.

## Validation

    pytest tests/test_order_book_execution.py
    ruff check algorithmic_trading/order_book_execution.py tests/test_order_book_execution.py
    black --check algorithmic_trading/order_book_execution.py tests/test_order_book_execution.py
