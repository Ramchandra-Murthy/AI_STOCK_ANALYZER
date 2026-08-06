from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, runtime_checkable


@runtime_checkable
class IResearchSynthesizer(ABC):
    """Interface for AI agents and recommendation engines synthesizing research."""

    @abstractmethod
    async def generate_thesis(
        self, valuation_results: Dict[str, Any], risk_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize quantitative outputs and risk assessments asynchronously into an investment thesis."""
        pass
