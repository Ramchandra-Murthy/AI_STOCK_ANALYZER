"""EROS DCF valuation boundary."""

from typing import Any

from services.valuation.dcf_engine import DCFValuationEngine


def evaluate_dcf(data: dict[str, Any]):
    """
    Execute the canonical DCF engine.

    EROS owns the boundary only.
    DCF mathematics remains in services.valuation.dcf_engine.
    """
    engine = DCFValuationEngine()
    return engine.evaluate(data)


__all__ = ["evaluate_dcf", "DCFValuationEngine"]
