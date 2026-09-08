"""Public compatibility boundary for the restored EROS container."""

from core.container.container import ServiceContainer, container
from core.container.exceptions import (
    ContainerError,
    DuplicateServiceError,
    ServiceNotFoundError,
)
from core.container.registry import ServiceKey
from core.container.bootstrap import ContainerBootstrap, bootstrap_container

Container = ServiceContainer

__all__ = [
    "Container",
    "ServiceContainer",
    "container",
    "ServiceKey",
    "bootstrap_container",
    "ContainerBootstrap",
    "ContainerError",
    "ServiceNotFoundError",
    "DuplicateServiceError",
]
