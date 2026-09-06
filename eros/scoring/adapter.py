"""
EROS scoring boundary.

The existing scoring engines remain authoritative.
EROS only selects and invokes them.
"""

from typing import Any

from services.scoring.fundamental import FundamentalScoringEngine
from services.scoring.risk_scoring import RiskScoringEngine


def fundamental_score(financials: Any):
    engine = FundamentalScoringEngine()
    return engine.evaluate(financials)


def risk_score(financials: Any):
    engine = RiskScoringEngine()
    return engine.evaluate(financials)


__all__ = [
    "FundamentalScoringEngine",
    "RiskScoringEngine",
    "fundamental_score",
    "risk_score",
]
