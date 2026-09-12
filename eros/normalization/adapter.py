"""
EROS normalization boundary.

Delegates normalization to the existing FinancialNormalizer.
No normalization mathematics is duplicated here.
"""

from collections.abc import Mapping
from typing import Any

from services.fundamentals.normalizer import FinancialNormalizer


def normalize(raw_data: Mapping[str, Any]):
    if not isinstance(raw_data, Mapping):
        raise TypeError("raw_data must be a mapping")

    normalizer = FinancialNormalizer()
    return normalizer.normalize(dict(raw_data))


__all__ = ["normalize"]
