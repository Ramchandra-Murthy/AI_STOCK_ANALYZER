from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ReportResult:
    """Multi-format professional institutional report generation result."""

    symbol: str
    format_type: str  # HTML, PDF, MARKDOWN, JSON
    file_path: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
