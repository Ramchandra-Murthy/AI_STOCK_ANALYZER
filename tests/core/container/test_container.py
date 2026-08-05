from __future__ import annotations
import pytest
from core.container.container import ServiceContainer

def test_register_and_resolve() -> None:
    container = ServiceContainer()
    obj = object()
    container.register("service", obj)
    assert container.resolve("service") is obj

def test_duplicate_registration() -> None:
    container = ServiceContainer()
    container.register("x", object())
    with pytest.raises(ValueError):
        container.register("x", object())

def test_unknown_service() -> None:
    container = ServiceContainer()
    with pytest.raises(KeyError):
        container.resolve("missing")

def test_clear_container() -> None:
    container = ServiceContainer()
    container.register("x", object())
    container.clear()
    with pytest.raises(KeyError):
        container.resolve("x")
