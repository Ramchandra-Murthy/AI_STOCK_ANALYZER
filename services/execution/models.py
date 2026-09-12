from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class ExecutionOrder:
    """Executable portfolio order generated from validated sizing inputs."""

    symbol: str
    action: str
    quantity: float
    limit_price: float | None
    execution_priority: str
    estimated_slippage: float
    estimated_transaction_cost: float
    rationale: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
