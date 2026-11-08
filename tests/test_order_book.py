from datetime import UTC, datetime, timedelta

import pytest

from ai_trading.order_book import LevelUpdate, OrderBookLevel, OrderBookSnapshot

NOW = datetime(2026, 11, 9, 4, 0, tzinfo=UTC)


def _book():
    return OrderBookSnapshot.from_levels(
        "reliance",
        NOW,
        bids=[(100.0, 10.0), (99.0, 20.0), (98.0, 30.0)],
        asks=[(101.0, 12.0), (102.0, 18.0), (103.0, 24.0)],
        sequence=10,
    )


def test_snapshot_normalizes_symbol_and_sorts_levels_best_first():
    book = OrderBookSnapshot.from_levels(
        " reliance ",
        NOW,
        bids=[(99.0, 20.0), (100.0, 10.0)],
        asks=[(102.0, 15.0), (101.0, 12.0)],
    )
    assert book.symbol == "RELIANCE"
    assert [level.price for level in book.bids] == [100.0, 99.0]
    assert [level.price for level in book.asks] == [101.0, 102.0]


def test_metrics_calculate_spread_depth_imbalance_and_microprice():
    metrics = _book().metrics(levels=2)
    assert metrics.best_bid == 100.0
    assert metrics.best_ask == 101.0
    assert metrics.mid_price == pytest.approx(100.5)
    assert metrics.spread == pytest.approx(1.0)
    assert metrics.spread_bps == pytest.approx(1.0 / 100.5 * 10_000)
    assert metrics.bid_depth == 30.0
    assert metrics.ask_depth == 30.0
    assert metrics.depth_imbalance == pytest.approx(0.0)
    assert metrics.microprice == pytest.approx((101.0 * 10.0 + 100.0 * 12.0) / 22.0)
    assert metrics.bid_top_level_concentration == pytest.approx(10.0 / 30.0)
    assert metrics.ask_top_level_concentration == pytest.approx(12.0 / 30.0)


def test_depth_imbalance_is_bounded_and_reflects_bid_pressure():
    book = OrderBookSnapshot.from_levels("ABC", NOW, bids=[(10, 90)], asks=[(11, 10)])
    assert book.metrics().depth_imbalance == pytest.approx(0.8)


def test_update_sets_absolute_quantity_and_returns_new_snapshot():
    book = _book()
    updated = book.apply_update(
        LevelUpdate(NOW + timedelta(milliseconds=1), "bid", 100.0, 25.0, sequence=11)
    )
    assert book.bids[0].quantity == 10.0
    assert updated.bids[0].quantity == 25.0
    assert updated.sequence == 11


def test_update_adds_new_level_and_resorts():
    updated = _book().apply_update(
        LevelUpdate(NOW + timedelta(milliseconds=1), "bid", 100.5, 5.0, sequence=11)
    )
    assert updated.bids[0] == OrderBookLevel(100.5, 5.0)


def test_zero_quantity_deletes_level():
    updated = _book().apply_update(
        LevelUpdate(NOW + timedelta(milliseconds=1), "ask", 101.0, 0.0, sequence=11)
    )
    assert [level.price for level in updated.asks] == [102.0, 103.0]


def test_update_rejects_crossed_book_without_mutating_original():
    book = _book()
    with pytest.raises(ValueError, match="crossed"):
        book.apply_update(
            LevelUpdate(NOW + timedelta(milliseconds=1), "bid", 101.0, 50.0, sequence=11)
        )
    assert book.bids[0].price == 100.0


@pytest.mark.parametrize(
    "bids,asks",
    [
        ([(100, 1)], [(100, 2)]),
        ([(101, 1)], [(100, 2)]),
        ([(100, 1), (100, 2)], [(101, 1)]),
        ([(100, 1)], [(101, 1), (101, 2)]),
        ([], [(101, 1)]),
        ([(100, 1)], []),
    ],
)
def test_invalid_book_shapes_are_rejected(bids, asks):
    with pytest.raises(ValueError):
        OrderBookSnapshot.from_levels("ABC", NOW, bids=bids, asks=asks)


@pytest.mark.parametrize(
    "price,quantity",
    [(0, 1), (1, 0), (-1, 1), (1, -1), (float("inf"), 1), (1, float("nan"))],
)
def test_invalid_level_values_are_rejected(price, quantity):
    with pytest.raises(ValueError):
        OrderBookLevel(price, quantity)


def test_naive_timestamp_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        OrderBookSnapshot.from_levels(
            "ABC",
            "2026-11-09T09:30:00",
            bids=[(100, 1)],
            asks=[(101, 1)],
        )


def test_stale_timestamp_and_non_increasing_sequence_are_rejected():
    book = _book()
    with pytest.raises(ValueError, match="timestamp"):
        book.apply_update(LevelUpdate(NOW - timedelta(seconds=1), "bid", 100, 12))
    with pytest.raises(ValueError, match="sequence"):
        book.apply_update(LevelUpdate(NOW, "bid", 100, 12, sequence=10))


@pytest.mark.parametrize("levels", [0, -1, 1.5, True])
def test_invalid_metrics_depth_is_rejected(levels):
    with pytest.raises(ValueError, match="levels"):
        _book().metrics(levels=levels)
