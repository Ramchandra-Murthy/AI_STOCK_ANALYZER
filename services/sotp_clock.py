from __future__ import annotations

from datetime import UTC, datetime


def get_current_timestamp() -> str:
    return datetime.now(UTC).isoformat()
