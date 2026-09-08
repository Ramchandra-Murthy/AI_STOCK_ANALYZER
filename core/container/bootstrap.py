from __future__ import annotations

"""Composition root for the restored legacy EROS application pipeline."""

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

    container.register_singleton(ServiceKey.RESEARCH, EROSResearchService())


class ContainerBootstrap:
    """Backward-compatible wrapper for the historical container API."""

    @classmethod
    def get_container(cls):
        bootstrap_container()
        return container

    @classmethod
    def reset(cls) -> None:
        container.clear()
