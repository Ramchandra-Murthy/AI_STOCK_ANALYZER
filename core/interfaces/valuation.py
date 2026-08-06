from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, TypeVar, runtime_checkable

TContext = TypeVar("TContext")
TResult = TypeVar("TResult")


@dataclass
class ValuationContext:
    """Encapsulates inputs required to perform a valuation."""

    symbol: str
    financials: Dict[str, Any] = field(default_factory=dict)
    market_data: Dict[str, Any] = field(default_factory=dict)
    assumptions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValuationResult:
    """Standardized output structure for any valuation model."""

    model_name: str
    intrinsic_value: float
    currency: str = "INR"
    confidence_score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class IValuationEngine(ABC, Generic[TContext, TResult]):
    """Interface implemented by all valuation plugins (DCF, SOTP, Relative, NAV)."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier name for the valuation engine."""
        pass

    @abstractmethod
    async def calculate(self, context: TContext) -> TResult:
        """Execute the valuation calculation asynchronously based on context."""
        pass
