"""EROS SOTP valuation boundary."""

from typing import Any

from services.valuation.sotp_engine import SOTPValuationEngine


def evaluate_sotp(data: dict[str, Any]):
    """
    Execute the canonical SOTP engine.

    EROS owns the boundary only.
    SOTP mathematics remains in services.valuation.sotp_engine.
    """
    engine = SOTPValuationEngine()
    return engine.evaluate(data)


__all__ = ["evaluate_sotp", "SOTPValuationEngine"]
