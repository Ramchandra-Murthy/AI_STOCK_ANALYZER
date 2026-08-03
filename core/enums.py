from __future__ import annotations

"""
==========================================================
PLATFORM ENUMS
Module  : core.enums
Version : 4.0.0
==========================================================
"""

from enum import Enum

class Status(str, Enum):
    OK = "OK"
    UNAVAILABLE = "UNAVAILABLE"
    UNRESOLVED = "UNRESOLVED"
    FAILED = "FAILED"
    WARNING = "WARNING"

class ValuationMethod(str, Enum):
    DCF = "DCF"
    NAV = "NAV"
    COMPARABLE = "COMPARABLE"
    MARKET = "MARKET"
    BOOK = "BOOK"
    PRECEDENT = "PRECEDENT"
    MONTE_CARLO = "MONTE_CARLO"
    SOTP = "SOTP"

class AccountingStandard(str, Enum):
    IND_AS = "IND_AS"
    US_GAAP = "US_GAAP"
    IFRS = "IFRS"

class Currency(str, Enum):
    INR = "INR"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"

class MetricUnit(str, Enum):
    CRORES = "CR"
    MILLIONS = "M"
    BILLIONS = "B"
    RAW = "RAW"
