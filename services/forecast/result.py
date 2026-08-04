"""
==========================================================
FORECAST RESULT CONTRACTS
Module  : services.forecast.result
Layer   : Forecast Service Result
==========================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Mapping, Type, TypeVar
from services.forecast.models import ForecastPackage
from services.forecast.exceptions import ForecastSerializationError

T = TypeVar("T", bound="ForecastResult")


@dataclass(frozen=True, slots=True)
class ForecastResult:
    """Canonical immutable output contract encapsulating completed forecast packages."""

    package: ForecastPackage
    execution_time_ms: float
    status: str = "SUCCESS"
    error_message: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package": self.package.to_dict(),
            "execution_time_ms": self.execution_time_ms,
            "status": self.status,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls: Type[T], data: Mapping[str, object]) -> T:
        try:
            pkg_data = data["package"]
            if not isinstance(pkg_data, Mapping):
                raise ValueError("Package payload must be a mapping dictionary.")
            package_obj = ForecastPackage.from_dict(pkg_data)  # type: ignore
            return cls(
                package=package_obj,
                execution_time_ms=float(data.get("execution_time_ms", 0.0)),  # type: ignore
                status=str(data.get("status", "SUCCESS")),
                error_message=(
                    str(data["error_message"])
                    if data.get("error_message") is not None
                    else None
                ),
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ForecastSerializationError(
                f"Failed to deserialize ForecastResult: {e}"
            ) from e
