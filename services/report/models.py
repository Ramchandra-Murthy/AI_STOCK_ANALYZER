from __main__ import *
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass(frozen=True, slots=True)
class GeneratedReport:
    """Multi-format output container for institutional equity reports."""
    symbol: str
    markdown_content: str
    html_content: str
    json_content: str
    format_type: str = "ALL"
