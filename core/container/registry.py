"""
==========================================================
Service Registry Enums
==========================================================
"""
from enum import Enum

class ServiceKey(str, Enum):
    RESEARCH = "research"
    FORECAST = "forecast"
    PORTFOLIO = "portfolio"
    MARKET = "market"
    VALUATION = "valuation"
    REPORT = "report"
