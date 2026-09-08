import importlib


def test_v43_valuation_dependencies_import():
    module = importlib.import_module("services.valuation_v43_service")
    assert callable(module.generate_valuation_v43)


def test_v43_dependency_modules_import():
    for name in (
        "services.peer_relevance_service",
        "services.peer_valuation_service",
        "services.valuation_quality_adjustment_service",
        "services.valuation_v4_service",
    ):
        assert importlib.import_module(name) is not None
