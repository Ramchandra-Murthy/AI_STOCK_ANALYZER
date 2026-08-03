import os

# Create core package directory
os.makedirs("core", exist_ok=True)

files = {
    "core/__init__.py": '"""Core platform framework package initialization."""\n',
    
    "core/version.py": '''from __future__ import annotations

"""
==========================================================
PLATFORM VERSION & METADATA
Module  : core.version
Version : 4.0.0
==========================================================
"""

PLATFORM_NAME = "AI Institutional Equity Research Platform"
PLATFORM_VERSION = "4.0.0"
AUTHOR = "Ramchandra Murthy"
BUILD = "2026.08"
PYTHON_VERSION = "3.13+"
ARCHITECTURE = "Modular Institutional Valuation Platform"

def get_version_info() -> dict[str, str]:
    return {
        "platform_name": PLATFORM_NAME,
        "version": PLATFORM_VERSION,
        "author": AUTHOR,
        "build": BUILD,
        "python_version": PYTHON_VERSION,
        "architecture": ARCHITECTURE,
    }
''',

    "core/exceptions.py": '''from __future__ import annotations

"""
==========================================================
CUSTOM DOMAIN EXCEPTIONS
Module  : core.exceptions
Version : 4.0.0
==========================================================
"""

from typing import Any

class PlatformError(Exception):
    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

class ValidationError(PlatformError):
    def __init__(self, message: str, discrepancies: dict[str, Any] | None = None) -> None:
        super().__init__(message, details=discrepancies)

class ParserError(PlatformError):
    pass

class RepositoryError(PlatformError):
    pass

class ValuationError(PlatformError):
    pass

class ForecastError(PlatformError):
    pass

class DispatcherError(PlatformError):
    pass

class ReportGenerationError(PlatformError):
    pass

class ConfigurationError(PlatformError):
    pass
''',

    "core/enums.py": '''from __future__ import annotations

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
''',

    "core/logger.py": '''from __future__ import annotations

"""
==========================================================
SYSTEM LOGGER
Module  : core.logger
Version : 4.0.0
==========================================================
"""

import logging
import sys

class SystemLogger:
    def __init__(self, name: str = "EQUITY_PLATFORM") -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def info(self, msg: str) -> None:
        self.logger.info(msg)

    def warning(self, msg: str) -> None:
        self.logger.warning(msg)

    def error(self, msg: str) -> None:
        self.logger.error(msg)

logger = SystemLogger()
''',

    "core/settings.py": '''from __future__ import annotations

"""
==========================================================
GLOBAL PLATFORM CONFIGURATION & DEFAULTS
Module  : core.settings
Version : 4.0.0
==========================================================
"""

from dataclasses import dataclass

@dataclass(frozen=True)
class DCFSettings:
    DEFAULT_TAX_RATE: float = 0.25
    DEFAULT_COST_OF_EQUITY: float = 0.12
    DEFAULT_COST_OF_DEBT_POST_TAX: float = 0.06
    DEFAULT_EQUITY_WEIGHT: float = 0.80
    DEFAULT_DEBT_WEIGHT: float = 0.20
    DEFAULT_TERMINAL_GROWTH: float = 0.03
    DEFAULT_FORECAST_YEARS: int = 5
    DEFAULT_REVENUE_GROWTH: float = 0.08
    DEFAULT_CAPEX_PCT_REV: float = 0.05
    DEFAULT_NWC_PCT_REV: float = 0.02

@dataclass(frozen=True)
class NAVSettings:
    DEFAULT_HOLDCO_DISCOUNT: float = 0.15

@dataclass(frozen=True)
class AccountingSettings:
    STRICT_BALANCE_SHEET_CHECK: bool = True
    BALANCE_SHEET_TOLERANCE: float = 1.0

@dataclass(frozen=True)
class PlatformSettings:
    ENV: str = "DEVELOPMENT"
    dcf: DCFSettings = DCFSettings()
    nav: NAVSettings = NAVSettings()
    accounting: AccountingSettings = AccountingSettings()

settings = PlatformSettings()
'''
}

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✓ Created {path}")

print("\n==========================================================")
print("MILESTONE 1 (CORE FRAMEWORK) DEPLOYED SUCCESSFULLY")
print("==========================================================")
