from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True, slots=True)
class BaseDomainEvent:
    """Standardized base contract for all domain events in the pipeline."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    name: str = ""
    symbol: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Enforce strict runtime assertions before dispatch or initialization."""
        assert isinstance(self.symbol, str), f"Event symbol must be a string, got {type(self.symbol)}"
        assert self.symbol != "", "Event symbol cannot be empty"
        assert isinstance(self.payload, dict), f"Event payload must be a dictionary, got {type(self.payload)}"


# Backward compatibility alias
DomainEvent = BaseDomainEvent
