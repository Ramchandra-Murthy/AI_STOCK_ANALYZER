"""
==========================================================
CORE TYPES & PROTOCOLS
Module  : core.types
Layer   : Core Infrastructure
==========================================================
"""

from __future__ import annotations

from typing import Protocol, Dict, Any, runtime_checkable

Ticker = str
Currency = str
Year = int


@runtime_checkable
class Serializable(Protocol):
    """Protocol defining objects that support bidirectional dictionary conversion."""

    def to_dict(self) -> Dict[str, Any]:
        ...

    @classmethod
    from_dict(cls, data: Dict[str, Any]) -> Serializable:
    