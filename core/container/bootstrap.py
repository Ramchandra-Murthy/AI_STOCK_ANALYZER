<<<<<<< HEAD
﻿from __future__ import annotations

from core.container.container import Container


class ContainerBootstrap:
    """Handles global container initialization and service wire-up for AIERP V6."""

    _instance: Container | None = None

    @classmethod
    def get_container(cls) -> Container:
        """Retrieve or initialize the global container singleton."""
        if cls._instance is None:
            cls._instance = cls._initialize()
        return cls._instance

    @classmethod
    def _initialize(cls) -> Container:
        """Create and configure container bindings."""
        container = Container()
        # Future domain services and infrastructure providers will be bound here
        return container

    @classmethod
    def reset(cls) -> None:
        """Reset the global container (primarily used for testing)."""
        cls._instance = None
=======
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
>>>>>>> afd58f7f54a3fb77a08bb3a8a1c4b4e5e498fe47
