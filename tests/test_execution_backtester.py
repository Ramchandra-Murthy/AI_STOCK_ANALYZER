import pandas as pd
import pytest

from algorithmic_trading.execution_backtester import run_execution_aware_backtest


def _inputs(volumes: list[float] | None = None):
    index = pd.date_range("2026-01-01", periods=4, freq="D")
    prices = pd.Series([100.0, 100.0, 110.0, 110.0], index=index)
    signals = pd.Series([1.0, 1.0, 1.0, 0.0], index=index)
    volume = pd.Series(volumes or [100.0] * 4, index=index)
    volatility = pd.Series([0.01] * 4, index=index)
    return prices, signals, volume, volatility


def test_execution_backtest_lags_signals_and_respects_volume_cap() -> None:
    prices, signals, volumes, volatility = _inputs([100.0] * 4)
    result, _ = run_execution_aware_backtest(
        prices, signals, volumes, volatility, max_participation=0.10
    )

    assert result["position"].tolist() == [0.0, 1.0, 1.0, 1.0]
    assert result["filled_quantity"].iloc[0] == 0.0
    assert result["participation_rate"].max() <= 0.10
    assert result["remaining_quantity"].iloc[1] > 0.0


def test_execution_impact_increases_buy_fill_price_and_reduces_return() -> None:
    prices, signals, volumes, volatility = _inputs([10_000.0] * 4)
    no_impact, no_impact_metrics = run_execution_aware_backtest(
        prices, signals, volumes, volatility, impact_coefficient=0.0
    )
    with_impact, metrics = run_execution_aware_backtest(
        prices, signals, volumes, volatility, impact_coefficient=1.0
    )

    assert with_impact.loc[prices.index[1], "execution_price"] > prices.iloc[1]
    assert metrics.total_return < no_impact_metrics.total_return


def test_zero_volume_leaves_order_unfilled() -> None:
    prices, signals, volumes, volatility = _inputs([0.0] * 4)
    result, _ = run_execution_aware_backtest(prices, signals, volumes, volatility)

    assert result["filled_quantity"].sum() == 0.0
    assert result["shares"].eq(0.0).all()


def test_sell_fill_is_below_reference_and_short_position_is_supported() -> None:
    index = pd.date_range("2026-01-01", periods=3, freq="D")
    prices = pd.Series([100.0, 100.0, 100.0], index=index)
    signals = pd.Series([-1.0, -1.0, 0.0], index=index)
    volumes = pd.Series([10_000.0] * 3, index=index)
    volatility = pd.Series([0.02] * 3, index=index)
    result, _ = run_execution_aware_backtest(prices, signals, volumes, volatility)

    assert result.loc[index[1], "shares"] < 0
    assert result.loc[index[1], "execution_price"] < 100.0


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1.0])
def test_execution_backtest_rejects_invalid_market_impact_parameters(bad: float) -> None:
    prices, signals, volumes, volatility = _inputs()
    with pytest.raises(ValueError):
        run_execution_aware_backtest(
            prices, signals, volumes, volatility, impact_coefficient=bad
        )


def test_execution_backtest_rejects_misaligned_market_data() -> None:
    prices, signals, volumes, volatility = _inputs()
    with pytest.raises(ValueError, match="identical timestamps"):
        run_execution_aware_backtest(prices, signals, volumes, volatility.iloc[:-1])
