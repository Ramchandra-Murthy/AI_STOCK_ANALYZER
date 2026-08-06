# core/interfaces/research.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class IResearchSynthesizer(ABC):
    """Interface for AI agents and recommendation engines synthesizing research."""

    @abstractmethod
    def generate_thesis(
        self, valuation_results: Dict[str, Any], risk_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize quantitative outputs and risk assessments into an investment thesis."""
        pass
