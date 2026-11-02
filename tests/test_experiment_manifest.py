from __future__ import annotations

import copy

import pytest

from ai_trading.experiment_manifest import build_experiment_manifest


def _manifest(**overrides):
    values = {
        "strategy_name": "moving_average_cross",
        "parameters": {"fast": 10, "slow": 30},
        "data_source": "NSE_daily_adjusted",
        "data_start": "2022-01-01",
        "data_end": "2025-12-31",
        "timeframe": "1d",
        "benchmark": "NIFTY50",
        "random_seed": 7,
        "code_version": "abc123",
        "transaction_cost_bps": 5,
        "slippage_bps": 10,
    }
    values.update(overrides)
    return build_experiment_manifest(**values)


def test_manifest_fingerprint_is_deterministic_and_json_safe():
    first = _manifest()
    second = _manifest(parameters={"slow": 30, "fast": 10})

    assert first["experiment_id"] == second["experiment_id"]
    assert first["schema_version"] == 1
    assert len(first["experiment_id"]) == 64
    assert first["data"]["start"] == "2022-01-01"


def test_fingerprint_changes_when_experiment_input_changes():
    baseline = _manifest()
    changed_parameters = _manifest(parameters={"fast": 12, "slow": 30})
    changed_costs = _manifest(slippage_bps=15)

    assert baseline["experiment_id"] != changed_parameters["experiment_id"]
    assert baseline["experiment_id"] != changed_costs["experiment_id"]


def test_manifest_does_not_mutate_input_parameters():
    parameters = {"fast": 10, "slow": 30}
    original = copy.deepcopy(parameters)

    _manifest(parameters=parameters)

    assert parameters == original


@pytest.mark.parametrize(
    "overrides",
    [
        {"strategy_name": ""},
        {"data_source": ""},
        {"timeframe": ""},
        {"data_start": "2025-01-01", "data_end": "2024-01-01"},
        {"data_start": "01-01-2024"},
        {"random_seed": -1},
        {"transaction_cost_bps": -1},
        {"slippage_bps": float("inf")},
        {"parameters": {"fast": float("nan")}},
        {"parameters": {1: "bad-key"}},
    ],
)
def test_invalid_manifest_inputs_are_rejected(overrides):
    with pytest.raises((ValueError, TypeError)):
        _manifest(**overrides)
