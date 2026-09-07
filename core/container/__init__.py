"""Compatibility exports for the EROS application container."""

from core.container.container import ServiceContainer, container
from core.container.exceptions import (
    ContainerError,
    DuplicateServiceError,
    ServiceNotFoundError,
)
from core.container.registry import ServiceKey
from core.container.bootstrap import bootstrap_container

__all__ = [
    "ServiceContainer",
    "container",
    "ServiceKey",
    "bootstrap_container",
    "ContainerError",
    "ServiceNotFoundError",
    "DuplicateServiceError",
]
