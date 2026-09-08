"""
EROS 3.0 - SOTP / DCF Bridge

The bridge combines already-computed valuations.

It does not recalculate SOTP or DCF.
"""

from typing import Optional

from eros.contracts import ValuationResult


def build_bridge(
    sotp: Optional[ValuationResult],
    dcf: Optional[ValuationResult],
) -> ValuationResult:

    warnings = []

    if sotp is None:
        warnings.append("SOTP valuation unavailable.")

    if dcf is None:
        warnings.append("DCF valuation unavailable.")

    values = []

    if sotp is not None and sotp.value is not None:
        values.append(float(sotp.value))

    if dcf is not None and dcf.value is not None:
        values.append(float(dcf.value))

    if not values:
        return ValuationResult(
            method="SOTP_DCF_BRIDGE",
            warnings=warnings + ["No valuation values available."],
        )

    bridge_value = sum(values) / len(values)

    low_values = [
        float(x.low)
        for x in (sotp, dcf)
        if x is not None and x.low is not None
    ]

    high_values = [
        float(x.high)
        for x in (sotp, dcf)
        if x is not None and x.high is not None
    ]

    return ValuationResult(
        value=bridge_value,
        low=min(low_values) if low_values else None,
        high=max(high_values) if high_values else None,
        method="SOTP_DCF_BRIDGE",
        assumptions={
            "components": [
                x.method
                for x in (sotp, dcf)
                if x is not None
            ],
            "combination": "simple_mean",
        },
        warnings=warnings,
    )


__all__ = ["build_bridge"]
