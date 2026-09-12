from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ModelArtifact:
    model_id: str
    model_type: str  # "XGBoost", "LightGBM", "RandomForest"
    version: str
    metrics: dict[str, float]
    status: str  # "CHAMPION", "CHALLENGER", "ARCHIVED"
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
