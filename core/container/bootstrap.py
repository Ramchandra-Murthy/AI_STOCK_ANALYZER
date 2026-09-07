from __future__ import annotations

"""Composition root for the legacy EROS application pipeline."""

from core.container.container import container
from core.container.exceptions import ServiceNotFoundError
from core.container.registry import ServiceKey
from services.eros_research_service import EROSResearchService


def bootstrap_container() -> None:
    """Register the real EROS application service exactly once."""
    try:
        container.resolve(ServiceKey.RESEARCH)
        return
    except ServiceNotFoundError:
        pass

    container.register_singleton(
        ServiceKey.RESEARCH,
        EROSResearchService(),
    )
