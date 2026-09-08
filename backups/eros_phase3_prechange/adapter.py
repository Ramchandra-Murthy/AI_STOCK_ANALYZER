"""
EROS 3.0 - Valuation Adapter

The existing valuation engines remain the calculation authority.
This layer normalizes their output into the EROS ValuationResult
contract.
"""

from typing import Any

from eros.contracts import ValuationResult


def normalize_valuation(
    result: Any,
    method: str,
    currency: str = "INR",
) -> ValuationResult:
    """
    Convert an existing SOTP/DCF result into the canonical EROS
    ValuationResult.

    No valuation mathematics is performed here.
    """

    if result is None:
        return ValuationResult(
            method=method,
            currency=currency,
            warnings=["Underlying valuation returned None."],
        )

    if isinstance(result, ValuationResult):
        return result

    def read(name: str, default=None):
        if isinstance(result, dict):
            return result.get(name, default)

        return getattr(result, name, default)

    value = read("value")

    if value is None:
        value = read("fair_value")

    if value is None:
        value = read("intrinsic_value")

    low = read("low")

    if low is None:
        low = read("low_value")

    high = read("high")

    if high is None:
        high = read("high_value")

    assumptions = read("assumptions", {})

    if assumptions is None:
        assumptions = {}

    warnings = read("warnings", [])

    if warnings is None:
        warnings = []

    return ValuationResult(
        value=value,
        low=low,
        high=high,
        method=method,
        currency=currency,
        assumptions=assumptions,
        warnings=list(warnings),
    )


__all__ = ["normalize_valuation"]
