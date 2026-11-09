from datetime import datetime, timezone

import pytest

from ai_trading.order_book import OrderBookSnapshot
from algorithmic_trading.order_book_execution import estimate_order_book_execution


@pytest.fixture
def snapshot() -> OrderBookSnapshot:
    return OrderBookSnapshot.from_levels(
        "RELIANCE",
        datetime(2026, 1, 5, 4, 0, tzinfo=timezone.utc),
        bids=[(99.0, 100.0), (98.0, 200.0), (97.0, 300.0)],
        asks=[(101.0, 50.0), (102.0, 100.0), (103.0, 200.0)],
        sequence=10,
    )


def test_buy_sweeps_asks_and_reports_vwap_and_shortfall(snapshot) -> None:
    result = estimate_order_book_execution(snapshot, side="buy", quantity=100.0, synchronized=True)
    assert result.symbol == "RELIANCE"
    assert result.filled_quantity == pytest.approx(100.0)
    assert result.remaining_quantity == pytest.approx(0.0)
    assert result.levels_touched == 2
    assert result.volume_weighted_price == pytest.approx(101.5)
    assert result.implementation_shortfall_bps == pytest.approx(150.0)
    assert result.book_walk_bps == pytest.approx(49.504950495)


def test_sell_sweeps_bids_and_shortfall_is_positive(snapshot) -> None:
    result = estimate_order_book_execution(snapshot, side="sell", quantity=150.0, synchronized=True)
    assert result.volume_weighted_price == pytest.approx((99 * 100 + 98 * 50) / 150)
    assert result.implementation_shortfall_bps > 0
    assert result.book_walk_bps > 0


def test_insufficient_depth_reports_partial_fill(snapshot) -> None:
    result = estimate_order_book_execution(snapshot, side="buy", quantity=500.0, synchronized=True)
    assert result.filled_quantity == pytest.approx(350.0)
    assert result.remaining_quantity == pytest.approx(150.0)
    assert result.fill_ratio == pytest.approx(0.7)


def test_max_levels_limits_visible_liquidity(snapshot) -> None:
    result = estimate_order_book_execution(
        snapshot, side="buy", quantity=100.0, synchronized=True, max_levels=1
    )
    assert result.filled_quantity == pytest.approx(50.0)
    assert result.remaining_quantity == pytest.approx(50.0)
    assert result.levels_touched == 1


def test_unsynchronized_book_is_never_used(snapshot) -> None:
    with pytest.raises(ValueError, match="synchronized"):
        estimate_order_book_execution(snapshot, side="buy", quantity=10.0, synchronized=False)


@pytest.mark.parametrize("quantity", [0.0, -1.0, float("nan"), float("inf"), True])
def test_invalid_quantity_is_rejected(snapshot, quantity) -> None:
    with pytest.raises(ValueError, match="quantity"):
        estimate_order_book_execution(snapshot, side="buy", quantity=quantity, synchronized=True)


def test_invalid_side_and_level_limit_are_rejected(snapshot) -> None:
    with pytest.raises(ValueError, match="side"):
        estimate_order_book_execution(snapshot, side="hold", quantity=10.0, synchronized=True)
    with pytest.raises(ValueError, match="max_levels"):
        estimate_order_book_execution(
            snapshot, side="buy", quantity=10.0, synchronized=True, max_levels=0
        )
