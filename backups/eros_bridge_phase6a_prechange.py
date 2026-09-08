"""
EROS 3.0 SOTP / DCF Bridge.

Important:
This is NOT a valuation calculator.

It does not invent a weighting methodology.
It preserves the independently calculated SOTP and DCF
results and exposes their relationship for the decision layer.

Final investment decision authority remains downstream.
"""

from typing import Optional

from eros.contracts import ValuationResult


def build_bridge(
    sotp: Optional[ValuationResult],
    dcf: Optional[ValuationResult],
) -> dict:

    warnings = []

    if sotp is None:
        warnings.append(
            "SOTP valuation unavailable."
        )

    if dcf is None:
        warnings.append(
            "DCF valuation unavailable."
        )

    return {
        "method": "SOTP_DCF_BRIDGE",
        "sotp": sotp,
        "dcf": dcf,
        "sotp_value": (
            sotp.value
            if sotp is not None
            else None
        ),
        "dcf_value": (
            dcf.value
            if dcf is not None
            else None
        ),
        "spread": (
            abs(
                float(sotp.value)
                - float(dcf.value)
            )
            if (
                sotp is not None
                and dcf is not None
                and sotp.value is not None
                and dcf.value is not None
            )
            else None
        ),
        "warnings": warnings,
        "provenance": {
            "sotp": (
                sotp.method
                if sotp is not None
                else None
            ),
            "dcf": (
                dcf.method
                if dcf is not None
                else None
            ),
            "combination": None,
            "decision_authority": (
                "DOWNSTREAM_DECISION_LAYER"
            ),
        },
    }


__all__ = ["build_bridge"]
