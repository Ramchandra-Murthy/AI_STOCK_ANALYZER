from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True, slots=True)
class ReportResult:
    """Professional multi-format institutional report output."""
    symbol: str
    html_content: str
    markdown_content: str
    json_content: str
    format_type: str = "MULTI-FORMAT"
    metadata: Dict[str, Any] = field(default_factory=dict)
