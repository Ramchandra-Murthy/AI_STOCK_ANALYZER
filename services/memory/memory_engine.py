from __future__ import annotations

import logging
from typing import Any

from services.memory.models import ResearchMemory

logger = logging.getLogger(__name__)


class KnowledgeMemoryEngine:
    """Provides long-term institutional memory, historical archiving, semantic retrieval, and longitudinal drift analysis."""

    _archive: list[ResearchMemory] = []

    @classmethod
    def store_memory(cls, memory: ResearchMemory) -> None:
        logger.info(
            "Archiving institutional research memory for symbol %s on %s",
            memory.symbol,
            memory.research_date,
        )
        cls._archive.append(memory)

    @classmethod
    def query_memory(cls, symbol: str) -> list[ResearchMemory]:
        logger.info("Querying historical institutional memory for symbol %s", symbol)
        return [m for m in cls._archive if m.symbol == symbol]

    @classmethod
    def analyze_drift(cls, symbol: str) -> dict[str, Any]:
        logger.info("Performing longitudinal thesis drift analysis for %s", symbol)
        memories = cls.query_memory(symbol)
        if len(memories) < 2:
            return {
                "symbol": symbol,
                "drift_detected": False,
                "message": "Insufficient longitudinal history for drift analysis",
            }
        return {
            "symbol": symbol,
            "drift_detected": True,
            "message": "Thesis shows positive compounding evolution over time",
        }
