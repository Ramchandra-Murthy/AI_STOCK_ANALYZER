from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass(frozen=True)
class RatioCategoryResult:
    category_name: str
    symbol: str
    period: str
    metrics: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
