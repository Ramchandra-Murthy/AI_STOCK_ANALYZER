"""
EROS 3.0 - Stage 13C Facade

Stage 13C is deliberately separated into:

13C.1 - Evidence ingestion
13C.2 - Classification
13C.3 - Valuation authorization / gate

This facade provides one controlled entry point while
preserving the existing classification implementation.
"""

from typing import Any

from eros.decision.stage13c.classification import classify_record

STAGE_ID = "13C"


def evaluate_stage13c(record: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluate one Stage 13C record.

    The underlying classification rules remain in the
    migrated existing implementation.
    """

    result = classify_record(record)

    return {
        "stage": STAGE_ID,
        "classification": result,
    }


__all__ = [
    "STAGE_ID",
    "evaluate_stage13c",
]
