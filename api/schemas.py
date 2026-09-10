from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ApiResponse:
    success: bool
    version: str
    timestamp: str
    data: dict[str, Any]
    errors: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)
