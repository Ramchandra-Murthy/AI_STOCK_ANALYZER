from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, runtime_checkable


@runtime_checkable
class IReportExporter(ABC):
    """Interface for rendering analytical models into exportable formats (PDF, HTML)."""

    @abstractmethod
    async def export(self, data: dict[str, Any], output_path: str) -> str:
        """Render and save the report asynchronously, returning the final file path."""
        pass
