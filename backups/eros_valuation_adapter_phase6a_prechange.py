"""
EROS 3.0 canonical valuation normalization.

The legacy/modular valuation engines remain the calculation
authority. EROS owns the contract boundary only.
"""

from typing import Any

from eros.contracts import ValuationResult


def _read(obj: Any, name: str, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def normalize_valuation(
    result: Any,
    method: str,
    currency: str = "INR",
) -> ValuationResult:

    if isinstance(result, ValuationResult):
        return result

    if result is None:
        return ValuationResult(
            method=method,
            currency=currency,
            warnings=[f"{method} engine returned no valuation result."],
        )

    value = _read(result, "value")

    if value is None:
        value = _read(result, "fair_value")

    if value is None:
        value = _read(result, "intrinsic_value")

    if value is None:
        value = _read(result, "implied_share_price")

    enterprise_value = _read(
        result,
        "enterprise_value",
    )

    equity_value = _read(
        result,
        "equity_value",
    )

    low = _read(result, "low")

    if low is None:
        low = _read(result, "low_value")

    high = _read(result, "high")

    if high is None:
        high = _read(result, "high_value")

    assumptions = _read(
        result,
        "assumptions",
        {},
    )

    warnings = _read(
        result,
        "warnings",
        [],
    )

    if assumptions is None:
        assumptions = {}

    if warnings is None:
        warnings = []

    return ValuationResult(
        value=value,
        low=low,
        high=high,
        method=method,
        currency=currency,
        assumptions={
            **assumptions,
            "enterprise_value": enterprise_value,
            "equity_value": equity_value,
        },
        warnings=list(warnings),
    )


__all__ = ["normalize_valuation"]
