from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime

@dataclass(frozen=True)
class ApiResponse:
    success: bool
    version: str
    timestamp: str
    data: Dict[str, Any]
    errors: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
