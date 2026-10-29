"""Create deterministic manifests for reproducible strategy experiments.

The manifest records caller-supplied experiment inputs and a stable fingerprint.
It does not fetch data, execute backtests, or certify that inputs are truthful.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import date


def build_experiment_manifest(
    *,
    strategy_name: str,
    parameters: Mapping[str, object],
    data_source: str,
    data_start: str,
    data_end: str,
    timeframe: str,
    benchmark: str | None = None,
    random_seed: int | None = None,
    code_version: str | None = None,
    transaction_cost_bps: float = 0.0,
    slippage_bps: float = 0.0,
) -> dict[str, object]:
    """Return a JSON-safe experiment manifest with a deterministic SHA-256 ID."""
    if not isinstance(strategy_name, str) or not strategy_name.strip():
        raise ValueError("strategy_name must be a non-empty string")
    if not isinstance(data_source, str) or not data_source.strip():
        raise ValueError("data_source must be a non-empty string")
    if not isinstance(timeframe, str) or not timeframe.strip():
        raise ValueError("timeframe must be a non-empty string")
    start = _parse_date(data_start, "data_start")
    end = _parse_date(data_end, "data_end")
    if start > end:
        raise ValueError("data_start must be on or before data_end")
    if random_seed is not None and (
        isinstance(random_seed, bool) or not isinstance(random_seed, int) or random_seed < 0
    ):
        raise ValueError("random_seed must be a non-negative integer or None")
    costs = {
        "transaction_cost_bps": _nonnegative_finite(transaction_cost_bps, "transaction_cost_bps"),
        "slippage_bps": _nonnegative_finite(slippage_bps, "slippage_bps"),
    }
    if not isinstance(parameters, Mapping):
        raise TypeError("parameters must be a mapping")
    if any(not isinstance(key, str) or not key for key in parameters):
        raise ValueError("parameter keys must be non-empty strings")

    payload: dict[str, object] = {
        "schema_version": 1,
        "strategy_name": strategy_name.strip(),
        "parameters": dict(parameters),
        "data": {
            "source": data_source.strip(),
            "start": start.isoformat(),
            "end": end.isoformat(),
            "timeframe": timeframe.strip(),
            "benchmark": benchmark.strip() if isinstance(benchmark, str) and benchmark.strip() else None,
        },
        "execution_assumptions": costs,
        "random_seed": random_seed,
        "code_version": code_version.strip() if isinstance(code_version, str) and code_version.strip() else None,
    }
    try:
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("manifest fields must be JSON-serializable and finite") from exc
    payload["experiment_id"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload


def _parse_date(value: str, field: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO date string (YYYY-MM-DD)")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO date string (YYYY-MM-DD)") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{field} must use YYYY-MM-DD format")
    return parsed


def _nonnegative_finite(value: float, field: str) -> float:
    import math

    if isinstance(value, bool):
        raise ValueError(f"{field} must be finite and non-negative")
    try:
        parsed = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} must be finite and non-negative") from exc
    if not math.isfinite(parsed) or parsed < 0:
        raise ValueError(f"{field} must be finite and non-negative")
    return parsed
