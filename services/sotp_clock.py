from __future__ import annotations

from datetime import datetime, timezone


def get_current_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()
