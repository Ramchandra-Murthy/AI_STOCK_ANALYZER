import pandas as pd
import pytest

from algorithmic_trading.market_impact import (
    estimate_market_impact_bps,
    simulate_execution,
    summarize_execution_fills,
)


def test_square_root_impact_includes_half_spread() -> None:
    impact = estimate_market_impact_bps(
        filled_quantity=100,
        bar_volume=10_000,
        volatility=0.02,
        impact_coefficient=0.5,
        half_spread_bps=2,
    )
    assert impact == pytest.approx(12.0)


def test_execution_respects_participation_and_carries_unfilled_quantity() -> None:
    index = pd.date_range("2026-01-01", periods=3, freq="min")
    result = simulate_execution(
        order_quantity=250,
        side="buy",
        prices=pd.Series([100.0, 101.0, 102.0], index=index),
        volumes=pd.Series([1_000.0, 1_000.0, 1_000.0], index=index),
        volatility=pd.Series([0.01, 0.01, 0.01], index=index),
        max_participation=0.10,
    )

    assert result["filled_quantity"].tolist() == [100.0, 100.0, 50.0]
    assert result["remaining_quantity"].tolist() == [150.0, 50.0, 0.0]
    assert result["participation_rate"].max() <= 0.10
    assert (result["execution_price"] >= result["reference_price"]).all()


def test_sell_execution_is_below_reference_price() -> None:
    index = pd.date_range("2026-01-01", periods=1, freq="min")
    result = simulate_execution(
        order_quantity=50,
        side="sell",
        prices=pd.Series([100.0], index=index),
        volumes=pd.Series([1_000.0], index=index),
        volatility=pd.Series([0.02], index=index),
        half_spread_bps=1,
    )
    assert result.loc[index[0], "execution_price"] < 100.0


def test_zero_volume_bar_does_not_fill() -> None:
    index = pd.date_range("2026-01-01", periods=1, freq="min")
    result = simulate_execution(
        order_quantity=10,
        side="buy",
        prices=pd.Series([100.0], index=index),
        volumes=pd.Series([0.0], index=index),
        volatility=pd.Series([0.01], index=index),
    )
    assert result.loc[index[0], "filled_quantity"] == 0
    assert result.loc[index[0], "remaining_quantity"] == 10


@pytest.mark.parametrize(
    ("quantity", "volume", "volatility"),
    [(float("nan"), 100, 0.01), (10, 0, 0.01), (10, 100, -0.01), (101, 100, 0.01)],
)
def test_impact_rejects_invalid_inputs(quantity: float, volume: float, volatility: float) -> None:
    with pytest.raises(ValueError):
        estimate_market_impact_bps(
            filled_quantity=quantity,
            bar_volume=volume,
            volatility=volatility,
        )


def test_execution_rejects_misaligned_indexes() -> None:
    index = pd.date_range("2026-01-01", periods=2, freq="min")
    with pytest.raises(ValueError, match="identical indexes"):
        simulate_execution(
            order_quantity=10,
            side="buy",
            prices=pd.Series([100.0, 101.0], index=index),
            volumes=pd.Series([1_000.0, 1_000.0], index=index),
            volatility=pd.Series([0.01], index=index[:1]),
        )


def test_fill_diagnostics_report_completion_and_buy_slippage() -> None:
    index = pd.date_range("2026-01-01", periods=3, freq="min")
    fills = simulate_execution(
        order_quantity=250,
        side="buy",
        prices=pd.Series([100.0, 101.0, 102.0], index=index),
        volumes=pd.Series([1_000.0] * 3, index=index),
        volatility=pd.Series([0.01] * 3, index=index),
        max_participation=0.10,
    )
    diagnostics = summarize_execution_fills(
        fills, order_quantity=250, side="buy", arrival_price=100.0
    )

    assert diagnostics.completed is True
    assert diagnostics.fill_ratio == pytest.approx(1.0)
    assert diagnostics.bars_to_complete == 3
    assert diagnostics.remaining_quantity == pytest.approx(0.0)
    assert diagnostics.slippage_bps > 0
    assert diagnostics.implementation_shortfall > 0
    assert diagnostics.maximum_participation_rate == pytest.approx(0.10)


def test_fill_diagnostics_report_partial_sell_and_positive_slippage() -> None:
    from algorithmic_trading.market_impact import summarize_execution_fills

    index = pd.date_range("2026-01-01", periods=2, freq="min")
    fills = simulate_execution(
        order_quantity=300,
        side="sell",
        prices=pd.Series([100.0, 99.0], index=index),
        volumes=pd.Series([1_000.0, 1_000.0], index=index),
        volatility=pd.Series([0.01, 0.01], index=index),
        max_participation=0.10,
    )
    diagnostics = summarize_execution_fills(
        fills, order_quantity=300, side="sell", arrival_price=100.0
    )

    assert diagnostics.completed is False
    assert diagnostics.fill_ratio == pytest.approx(2 / 3)
    assert diagnostics.remaining_quantity == pytest.approx(100.0)
    assert diagnostics.bars_to_complete is None
    assert diagnostics.slippage_bps > 0


def test_fill_diagnostics_reject_inconsistent_remaining_quantity() -> None:
    from algorithmic_trading.market_impact import summarize_execution_fills

    index = pd.date_range("2026-01-01", periods=1, freq="min")
    fills = simulate_execution(
        order_quantity=100,
        side="buy",
        prices=pd.Series([100.0], index=index),
        volumes=pd.Series([1_000.0], index=index),
        volatility=pd.Series([0.01], index=index),
    )
    fills.loc[index[0], "remaining_quantity"] = 0.0
    with pytest.raises(ValueError, match="does not reconcile"):
        summarize_execution_fills(fills, order_quantity=100, side="buy", arrival_price=100.0)
