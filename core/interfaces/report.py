# core/interfaces/report.py
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class IReportExporter(ABC):
    """Interface for rendering analytical models into exportable formats (PDF, HTML)."""

    @abstractmethod
    def export(self, data: Dict[str, Any], output_path: str) -> str:
        """Render and save the report, returning the final file path."""
        pass
