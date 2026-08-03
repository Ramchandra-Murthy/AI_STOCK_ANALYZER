from __future__ import annotations

"""
==========================================================
VALUATION DISPATCHER (STRATEGY REGISTRY)
Module  : dispatcher
Version : V1.0
==========================================================

Central registry routing valuation tasks to engine strategies.
"""

from typing import Any, Dict
from services.valuation.base_engine import BaseValuationEngine
from services.valuation.models import ValuationResult


class ValuationDispatcher:
    """Registry managing valuation engine adapters."""

    def __init__(self):
        self._engines: Dict[str, BaseValuationEngine] = {}

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
