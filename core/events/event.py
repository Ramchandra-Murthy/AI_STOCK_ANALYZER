from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, runtime_checkable


@runtime_checkable
class DomainEvent(Protocol):
    """Protocol defining an immutable domain event structure."""
    event_id: str
    timestamp: float
    name: str
    payload: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class BaseEvent:
    """Standard concrete implementation of an immutable domain event."""
    name: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
