from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from services.forecast.models import ForecastPackage


@dataclass(frozen=True, slots=True)
class ForecastResult:
    """Encapsulates the outcome of a forecast execution run."""

    package: ForecastPackage
    execution_time_ms: float
    status: str  # "SUCCESS" or "FAILED"
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "package": self.package.to_dict(),
            "execution_time_ms": self.execution_time_ms,
            "status": self.status,
            "error_message": self.error_message,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ForecastResult:
        return cls(
            package=ForecastPackage.from_dict(data["package"]),
            execution_time_ms=data["execution_time_ms"],
            status=data["status"],
            error_message=data.get("error_message"),
            metadata=dict(data.get("metadata", {})),
        )
