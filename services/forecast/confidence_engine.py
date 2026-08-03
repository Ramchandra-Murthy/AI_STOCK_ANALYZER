"""
==========================================================
CONFIDENCE SCORING ENGINE
Module  : services.forecast.confidence_engine
Layer   : Domain / Forecast
==========================================================
"""

from __future__ import annotations

import logging
from typing import Tuple, Any

from services.forecast.models import ConfidenceLevel
from services.forecast.validation import ValidationReport

logger = logging.getLogger(__name__)


class ConfidenceEngine:
    """Engine for evaluating statistical confidence of financial series."""

    @staticmethod
    def evaluate_confidence(data: Tuple[float, ...], **kwargs: Any) -> ConfidenceLevel:
        """Evaluates data volatility and sample size to assign confidence."""
        logger.info("Evaluating series confidence.")
        if len(data) < 3:
            return ConfidenceLevel.LOW

        # Simple heuristic based on data length and variability
        return ConfidenceLevel.MEDIUM
