# Level-2 Order Book Data Engine

## Purpose

This module introduces a deterministic, validated in-memory model for aggregated
Level-2 (price-level) order-book snapshots. It is the first stage of the order-book
research pipeline described in *Quantitative Trading: Algorithms, Analytics,
Data Models, Optimization*, Chapter 5, especially Sections 5.1–5.2 on feed
messages and book construction.

It also operationalizes the liquidity concepts in *The Automated Trader*,
Chapter 4: quoted spread, displayed depth, immediate liquidity and the risk
that visible liquidity can disappear.

## Scope

Implemented in `ai_trading/order_book.py`:

- Immutable bid/ask snapshots with normalized symbols and best-first sorting.
- Timezone-aware timestamps and optional monotonic sequence checks.
- Validation for positive finite prices/quantities, duplicate price levels,
  missing sides, and locked/crossed books.
- Absolute level SET updates and zero-quantity DELETE updates.
- Top-N displayed depth, depth imbalance, quoted spread in basis points,
  microprice and top-level depth concentration.

## Feed adapter contract

The engine accepts already-decoded aggregate price levels as
`(price, absolute_quantity)` pairs. A provider adapter must translate its
snapshot/update protocol into this normalized contract.

A `LevelUpdate` is explicitly an absolute quantity at one price. It is not a
quantity delta. Provider-specific ADD, CANCEL, CANCEL-REPLACE and EXECUTION
messages must be decoded according to that provider's protocol before calling
`apply_update`. Sequence continuity, reconnect recovery and snapshot replay
must be enforced by the feed adapter; this module only rejects non-increasing
sequence values when both sequence numbers are supplied.

## Important limitations

- This is an aggregated price-level book, not an order-by-order book.
- It cannot reveal individual order identity or exact queue position.
- Displayed depth is not guaranteed executable liquidity; cancellations and
  hidden/iceberg liquidity can make visible depth misleading.
- It does not infer aggressor side, trade flow, cancellations, or Hawkes
  intensities without the corresponding event feed.
- It does not connect to a broker or exchange and does not generate trade
  recommendations or submit orders.
- Yahoo Finance OHLCV candles are not a Level-2 feed and must not be used to
  fabricate snapshots.

## Metrics

For the selected top N levels on each side:

- `bid_depth` and `ask_depth`: sum of displayed quantities.
- `depth_imbalance`: `(bid_depth - ask_depth) / (bid_depth + ask_depth)`.
- `spread_bps`: `(best_ask - best_bid) / mid_price * 10,000`.
- `microprice`: opposite-side-quantity-weighted best price:
  `(best_ask * best_bid_qty + best_bid * best_ask_qty) /`
  `(best_bid_qty + best_ask_qty)`.
- Top-level concentration: best-level quantity divided by displayed depth
  on that side.

These are descriptive book-state features, not standalone directional signals.
They should be evaluated against timestamp-aligned trades and out-of-sample
price changes before any strategy integration.

## Validation

Run:

```bash
pytest tests/test_order_book.py
ruff check ai_trading/order_book.py tests/test_order_book.py
black --check ai_trading/order_book.py tests/test_order_book.py
```


## Sequenced event replay and recovery

`ai_trading/order_book_replay.py` adds a deterministic replay coordinator for
normalized `LevelUpdate` events:

- Replay requires a sequence number on the initial snapshot and every update.
- Only the exact next sequence is applied. Future events are buffered and the
  book is marked unsynchronized; the last valid snapshot remains unchanged.
- If the missing event arrives before the buffer limit is reached, buffered
  events are applied in ascending contiguous sequence order.
- If the gap remains, the caller must request and provide a fresh authoritative
  snapshot. The replay coordinator drops buffered events covered by that
  snapshot and applies only the contiguous buffered suffix after it.
- Duplicate events are ignored. Conflicting events with the same buffered
  sequence, invalid book transitions and buffer overflow are reported rather
  than silently accepted.
- A buffer overflow clears the bounded buffer and requires authoritative
  snapshot recovery. No event is synthesized and no gap is skipped.

The replay coordinator is transport-agnostic. The upstream adapter remains
responsible for detecting disconnects, requesting provider snapshots, mapping
provider event semantics to absolute SET/DELETE updates, and deciding when a
feed is safe to resume. A `gap` or `invalid` result must not be treated as a
tradable live book.

Run the focused tests with:

```bash
pytest tests/test_order_book.py tests/test_order_book_replay.py
```
