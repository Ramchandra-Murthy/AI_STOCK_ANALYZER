from __future__ import annotations

"""
==========================================================
VALUATION DISPATCHER (STRATEGY REGISTRY)
Module  : dispatcher
Version : V1.0
==========================================================

Central registry routing valuation tasks to engine strategies.
"""

from typing import Any

from services.valuation.base_engine import BaseValuationEngine
from services.valuation.models import ValuationResult


class ValuationDispatcher:

    def list_supported_methods(self) -> list[str]:
        """Return a list of supported valuation method names."""
        if not hasattr(self, "engines"):
            return []
        return list(self.engines.keys())

    def register_engine(self, name: str, engine: Any) -> None:
        """Register a valuation engine."""
        if not hasattr(self, "engines"):
            self.engines = {}
        self.engines[name] = engine
    """Registry managing valuation engine adapters."""

    def __init__(self):
        self._engines: dict[str, BaseValuationEngine] = {}

    def register(self, engine: BaseValuationEngine) -> None:
        """Registers a valuation engine adapter."""
        method_key = engine.valuation_method.upper()
        self._engines[method_key] = engine

    def get_engine(self, method: str) -> BaseValuationEngine:
        """Retrieves an engine strategy by method key."""
        key = method.upper()
        if key not in self._engines:
            raise KeyError(f"No valuation engine registered for method: '{method}'.")
        return self._engines[key]

    def value(self, method: str, entity: Any) -> ValuationResult:
        """Executes valuation using the requested method key."""
        engine = self.get_engine(method)
        return engine.value(entity)

    def dispatch(self, method: str, entity: Any) -> ValuationResult:
        """Alias for value()."""
        return self.value(method, entity)
