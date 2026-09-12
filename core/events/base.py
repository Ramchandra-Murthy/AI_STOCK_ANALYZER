from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BaseDomainEvent:
    """Standard concrete implementation of a domain event."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
