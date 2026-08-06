from __future__ import annotations

"""
==========================================================
VALUATION DISPATCHER (STRATEGY REGISTRY)
Module  : dispatcher
Version : V2.0
==========================================================

Central registry routing valuation tasks to engine strategies.
"""

from typing import Any

from services.valuation.base_engine import BaseValuationEngine
from services.valuation.models import ValuationResult
from services.valuation.engines.dcf_engine import DCFValuationEngine
from services.valuation.engines.nav_engine import NAVValuationEngine
from services.valuation.engines.sotp_engine import SOTPValuationEngine


class ValuationDispatcher:
    def __init__(self):
        self._engines: dict[str, BaseValuationEngine] = {}
        self.engines = self._engines  # Backwards compatibility alias
        
        # Register default engines
        try:
            self.register(DCFValuationEngine())
        except Exception:
            pass
        try:
            self.register(NAVValuationEngine())
        except Exception:
            pass
        try:
            self.register(SOTPValuationEngine())
        except Exception:
            pass

    def list_supported_methods(self) -> list[str]:
        """Return a list of supported valuation method names."""
        return list(self._engines.keys())

    def register_engine(self, name: str, engine: Any) -> None:
        """Register a valuation engine."""
        self._engines[name.upper()] = engine

    def register(self, engine: BaseValuationEngine) -> None:
        """Registers a valuation engine adapter."""
        method_key = getattr(engine, "valuation_method", engine.__class__.__name__.replace("ValuationEngine", "")).upper()
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
