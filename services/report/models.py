from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True, slots=True)
class GeneratedReport:
    """Multi-format output container for institutional equity reports."""
    symbol: str
    markdown_content: str
    html_content: str
    json_content: str
    format_type: str = "ALL"
