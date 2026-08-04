from __future__ import annotations

from typing import Protocol, runtime_checkable, Any

@runtime_checkable
class Serializable(Protocol):
    """Protocol for objects that can be converted to a dictionary representation."""
    def to_dict(self) -> dict[str, Any]:
        ...
