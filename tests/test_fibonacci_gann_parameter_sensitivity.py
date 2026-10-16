from __future__ import annotations

import pytest

from modules.fibonacci_gann.backtest import BacktestConfig, Candle
from modules.fibonacci_gann.parameter_sensitivity import evaluate_parameter_sensitivity


def sample_candles() -> list[Candle]:
    closes = [100, 101, 102, 103, 102, 104, 105, 103]
    return [
        Candle(f"2026-01-01T09:{15 + index * 5:02d}", close, close + 2, close - 2, close)
        for index, close in enumerate(closes)
    ]


def test_compares_named_parameter_variants_independently() -> None:
    variants = {
        "baseline": BacktestConfig(capital=10_000, max_loss_per_trade=50, stop_distance=1),
        "wider_stop": BacktestConfig(
            capital=10_000, max_loss_per_trade=50, stop_distance=2, reward_risk_ratio=2
        ),
    }
    results = evaluate_parameter_sensitivity(
        sample_candles(), [True, False, True, False, True, False, True, False], variants
    )
    assert [item.variant for item in results] == ["baseline", "wider_stop"]
    assert all(item.result.starting_capital == 10_000 for item in results)
    assert all(item.config == variants[item.variant] for item in results)


def test_rejects_empty_variants() -> None:
    with pytest.raises(ValueError, match="at least one"):
        evaluate_parameter_sensitivity(sample_candles(), [False] * 8, {})


def test_rejects_signal_length_mismatch() -> None:
    with pytest.raises(ValueError, match="signals length"):
        evaluate_parameter_sensitivity(sample_candles(), [False], {"baseline": BacktestConfig()})


def test_rejects_non_boolean_signals() -> None:
    with pytest.raises(ValueError, match="only booleans"):
        evaluate_parameter_sensitivity(sample_candles(), [0] * 8, {"baseline": BacktestConfig()})


def test_rejects_invalid_variant_values() -> None:
    with pytest.raises(ValueError, match="must use a BacktestConfig"):
        evaluate_parameter_sensitivity(
            sample_candles(), [False] * 8, {"bad": "not a config"}  # type: ignore[dict-item]
        )
