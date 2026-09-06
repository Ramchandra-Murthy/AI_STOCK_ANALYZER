"""
EROS quality boundary.

Delegates quality calculations to the existing quality engines.
"""

from typing import Any

from services.data_platform.quality import DataQualityEngine
from services.ratios.quality_engine import AdvancedQualityEngine


def inspect_metric(
    metric_name: str,
    value: float,
    min_val: float = -1e12,
    max_val: float = 1e12,
):
    return DataQualityEngine.inspect_metric(
        metric_name,
        value,
        min_val,
        max_val,
    )


def quality_engine():
    return AdvancedQualityEngine()


__all__ = [
    "inspect_metric",
    "quality_engine",
    "DataQualityEngine",
    "AdvancedQualityEngine",
]
