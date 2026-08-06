from __future__ import annotations

import json
import logging
from dataclasses import asdict, is_dataclass
from typing import Any
from services.report.models import GeneratedReport

logger = logging.getLogger(__name__)


class ReportEngine:
    """Institutional reporting engine producing multi-format outputs from research data."""

    def _safe_serialize(self, obj: Any) -> Any:
        """Recursively convert dataclasses and non-serializable types to dictionaries/primitives."""
        if is_dataclass(obj):
            return {k: self._safe_serialize(v) for k, v in asdict(obj).items()}
        if isinstance(obj, list):
            return [self._safe_serialize(item) for item in obj]
        if isinstance(obj, dict):
            return {str(k): self._safe_serialize(v) for k, v in obj.items()}
        return obj

    def generate(self, research_data: Any) -> GeneratedReport:
        """Generate professional multi-format reports from research data."""
        logger.info("Generating professional institutional reports")

        raw_dict = self._safe_serialize(research_data)
        json_data = json.dumps(raw_dict, indent=2, default=str)
        markdown_data = f"# Institutional Research Report\n\n```json\n{json_data}\n```"
        html_data = f"<html><body><h1>Research Report</h1><pre>{json_data}</pre></body></html>"

        symbol = getattr(research_data, "symbol", "UNKNOWN")

        return GeneratedReport(
            symbol=symbol,
            markdown_content=markdown_data,
            html_content=html_data,
            json_content=json_data,
            format_type="MULTI-FORMAT"
        )
