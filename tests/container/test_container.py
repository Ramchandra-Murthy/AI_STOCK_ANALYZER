import pytest

from core.container.container import ServiceContainer
from core.container.exceptions import DuplicateServiceError, ServiceNotFoundError


def test_register_and_resolve_singleton():
    container = ServiceContainer()
    service = {"status": "active"}
    container.register_singleton("test_service", service)

    resolved = container.resolve("test_service")
    assert resolved is service


def test_register_duplicate_raises_error():
    container = ServiceContainer()
    container.register_singleton("svc", "first")

    with pytest.raises(DuplicateServiceError):
        container.register_singleton("svc", "second")


def test_resolve_missing_service_raises_error():
    container = ServiceContainer()
    with pytest.raises(ServiceNotFoundError):
        container.resolve("non_existent")


def test_register_factory_and_resolve():
    container = ServiceContainer()
    container.register_factory("factory_svc", lambda: "factory_instance")

    resolved = container.resolve("factory_svc")
    assert resolved == "factory_instance"


def test_clear_container():
    container = ServiceContainer()
    container.register_singleton("svc", "value")
    container.clear()

    with pytest.raises(ServiceNotFoundError):
        container.resolve("svc")
