from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime

@dataclass(frozen=True)
class ExecutionOrder:
    symbol: str
    action: str # "BUY", "SELL", "HOLD"
    quantity: float
    limit_price: Optional[float]
    execution_priority: str # "HIGH", "NORMAL", "LOW"
    estimated_slippage: float
    estimated_transaction_cost: float
    rationale: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
