<<<<<<< HEAD
﻿from __future__ import annotations

from core.container.container import Container
from core.container.registry import ServiceRegistry
from core.container.providers import BaseProvider, SingletonProvider, TransientProvider
from core.container.bootstrap import ContainerBootstrap

__all__ = [
    "Container",
    "ServiceRegistry",
    "BaseProvider",
    "SingletonProvider",
    "TransientProvider",
    "ContainerBootstrap",
=======
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
>>>>>>> afd58f7f54a3fb77a08bb3a8a1c4b4e5e498fe47
]
