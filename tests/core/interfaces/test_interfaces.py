import pytest
from abc import ABC
from core.interfaces import (
    ValuationEngine,
    ForecastEngine,
    ResearchEngine,
    MarketDataProvider,
    ReportGenerator,
)

def test_interfaces_are_abstract():
    """Verify that all core interfaces cannot be instantiated directly."""
    with pytest.raises(TypeError):
        ValuationEngine()
    with pytest.raises(TypeError):
        ForecastEngine()
    with pytest.raises(TypeError):
        ResearchEngine()
    with pytest.raises(TypeError):
        MarketDataProvider()
    with pytest.raises(TypeError):
        ReportGenerator()

def test_concrete_valuation_implementation():
    """Verify that a compliant subclass can be instantiated and executed."""
    class DummyValuation(ValuationEngine):
        def evaluate(self, symbol: str) -> dict:
            return {"symbol": symbol, "value": 100.0}

    engine = DummyValuation()
    result = engine.evaluate("AAPL")
    assert result["symbol"] == "AAPL"
    assert result["value"] == 100.0
