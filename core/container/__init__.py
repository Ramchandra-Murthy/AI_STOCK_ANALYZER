"""
==========================================================
Core Dependency Injection Package
==========================================================
"""
from core.container.container import ServiceContainer
from core.container.registry import ServiceRegistry

__all__ = ["ServiceContainer", "ServiceRegistry"]
