from __future__ import annotations

"""
==========================================================
BASE VALUATION ENGINE
Module  : base_engine
Version : V1.1
==========================================================

Canonical abstract interface for all valuation engines.

All concrete valuation engines must return the canonical
domain-level ValuationResult.
"""

from abc import ABC, abstractmethod
from typing import Any

from domain.valuation.result import ValuationResult


class BaseValuationEngine(ABC):
    """
    Abstract base class for all valuation engines.
    """

    @property
    @abstractmethod
    def valuation_method(self) -> str:
        """Return the valuation methodology identifier."""
        raise NotImplementedError

    @abstractmethod
    def value(self, entity: Any) -> ValuationResult:
        """
        Execute valuation and return the canonical
        domain-level ValuationResult.
        """
        raise NotImplementedError

    @property
    def engine_name(self) -> str:
        """Human-readable engine name."""
        return self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self.engine_name}(method={self.valuation_method})"
