"""
==========================================================
Container Bootstrap / Composition Root
==========================================================
"""

from __future__ import annotations

from core.container.container import container
from core.container.registry import ServiceKey


class ResearchServiceFacade:
    """Service wrapper for research pipeline execution."""

    def run_pipeline(self, ticker: str) -> dict[str, str]:
        return {"ticker": ticker, "status": "analyzed"}


def bootstrap_container() -> None:
    """Wire up core services into the container.

    Registration is idempotent for application startup: an already-wired
    container is left unchanged rather than hiding arbitrary errors.
    """
    if ServiceKey.RESEARCH.value in container._singletons:
        return
    container.register_singleton(ServiceKey.RESEARCH, ResearchServiceFacade())
