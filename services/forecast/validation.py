"""
==========================================================
FORECAST VALIDATION RULES & BOUNDARY CHECKS
Module  : services.forecast.validation
Layer   : Domain / Forecast
==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Container for validation outcomes, errors, and warnings."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
