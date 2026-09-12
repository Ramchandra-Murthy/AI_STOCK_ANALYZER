from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, runtime_checkable


@runtime_checkable
class IResearchSynthesizer(ABC):
    """Interface for AI agents and recommendation engines synthesizing research."""

    @abstractmethod
    async def generate_thesis(
        self, valuation_results: dict[str, Any], risk_metrics: dict[str, Any]
    ) -> dict[str, Any]:
        """Synthesize quantitative outputs and risk assessments asynchronously into an investment thesis."""
        pass
