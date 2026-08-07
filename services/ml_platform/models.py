from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class ModelArtifact:
    model_id: str
    model_type: str # "XGBoost", "LightGBM", "RandomForest"
    version: str
    metrics: Dict[str, float]
    status: str # "CHAMPION", "CHALLENGER", "ARCHIVED"
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
