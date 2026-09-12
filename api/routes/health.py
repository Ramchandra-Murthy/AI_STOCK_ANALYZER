from __future__ import annotations

from datetime import UTC, datetime

from api.schemas import ApiResponse


def get_health() -> ApiResponse:
    """Return the EROS API health payload."""
    return ApiResponse(
        success=True,
        version="1.0.0",
        timestamp=datetime.now(UTC).isoformat(),
        data={
            "database": "OK",
            "workflow": "OK",
            "forecast_engine": "OK",
            "committee": "OK",
            "reporting": "OK",
        },
        errors=[],
        metadata={"service": "EROS Enterprise API"},
    )
