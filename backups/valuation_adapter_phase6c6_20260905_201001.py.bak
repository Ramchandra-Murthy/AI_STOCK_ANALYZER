"""EROS valuation execution adapter."""

from typing import Any

from eros.valuation.bridge import ValuationBoundary


def valuation_available(data: Any) -> bool:
    """Return whether enough data exists to attempt valuation."""

    if not isinstance(data, dict):
        return False

    if not data:
        return False

    valuation_keys = {
        "company_name",
        "shares_outstanding",
        "dcf_segments",
        "other_segments",
        "holdco_discount",
        "revenue",
        "ebitda",
        "ebit",
        "pat",
        "free_cash_flow",
    }

    return any(
        key in data and data.get(key) is not None
        for key in valuation_keys
    )


def evaluate_valuation(
    data: dict[str, Any],
    provenance: dict[str, Any] | None = None,
) -> ValuationBoundary:
    """Execute the EROS valuation boundary."""

    boundary = ValuationBoundary()

    if not valuation_available(data):
        return boundary.evaluate(
            {},
            provenance=provenance,
        )

    return boundary.evaluate(
        data,
        provenance=provenance,
    )


__all__ = [
    "evaluate_valuation",
    "valuation_available",
]
