from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_type: str # e.g., "Company", "Sector", "Commodity", "MacroIndicator"
    label: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

@dataclass(frozen=True)
class GraphEdge:
    source: str
    target: str
    relationship: str # e.g., "belongs_to", "peer_of", "supplier_to", "affected_by"
    weight: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
