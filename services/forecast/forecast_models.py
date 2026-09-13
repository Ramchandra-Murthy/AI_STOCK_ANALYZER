"""Compatibility exports for the legacy forecast API.

The current forecast implementation uses ``services.forecast.models``.  Older
callers import the scenario and method enums from this module, so keep those
names available without duplicating the underlying method enum.
"""

from __future__ import annotations

from enum import Enum

from services.forecast.models import ForecastMethod


class ScenarioType(str, Enum):
    BASE = "BASE"
    BULL = "BULL"
    BEAR = "BEAR"


__all__ = ["ForecastMethod", "ScenarioType"]
