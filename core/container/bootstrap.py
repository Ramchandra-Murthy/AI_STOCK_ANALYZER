from __future__ import annotations

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
        # Future domain services and infrastructure providers will be bound here.
        return container

    @classmethod
    def reset(cls) -> None:
        """Reset the global container (primarily used for testing)."""
        cls._instance = None


def bootstrap_container() -> Container:
    """Compatibility entry point returning the initialized application container."""
    return ContainerBootstrap.get_container()
