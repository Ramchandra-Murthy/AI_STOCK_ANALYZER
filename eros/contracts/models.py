"""
EROS 3.0 - Canonical Data Contracts

The canonical objects passed between:
data -> normalization -> quality -> scoring
-> classification -> valuation -> decision -> evidence -> API
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class FinancialSnapshot:
    symbol: str

    revenue: Optional[float] = None
    ebitda: Optional[float] = None
    ebit: Optional[float] = None
    pat: Optional[float] = None
    eps: Optional[float] = None

    total_assets: Optional[float] = None
    total_debt: Optional[float] = None
    cash: Optional[float] = None
    equity: Optional[float] = None

    operating_cash_flow: Optional[float] = None
    free_cash_flow: Optional[float] = None

    shares_outstanding: Optional[float] = None
    market_cap: Optional[float] = None
    current_price: Optional[float] = None

    currency: str = "INR"
    period: Optional[str] = None

    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityResult:
    passed: bool
    score: float = 0.0
    missing_fields: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class ScoreResult:
    score: Optional[float] = None
    components: dict[str, float] = field(default_factory=dict)
    rationale: list[str] = field(default_factory=list)


@dataclass
class ClassificationResult:
    classification: Optional[str] = None
    confidence: Optional[float] = None
    rationale: list[str] = field(default_factory=list)


@dataclass
class ValuationResult:
    value: Optional[float] = None
    low: Optional[float] = None
    high: Optional[float] = None
    method: Optional[str] = None
    currency: str = "INR"
    assumptions: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class Evidence:
    source: str
    field: str
    value: Any = None
    period: Optional[str] = None
    confidence: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EROSResult:
    symbol: str

    financials: Optional[FinancialSnapshot] = None
    quality: Optional[QualityResult] = None
    score: Optional[ScoreResult] = None
    classification: Optional[ClassificationResult] = None

    sotp: Optional[ValuationResult] = None
    dcf: Optional[ValuationResult] = None
    bridge: Optional[ValuationResult] = None

    stage13c: Optional[dict[str, Any]] = None
    stage14: Optional[dict[str, Any]] = None

    evidence: list[Evidence] = field(default_factory=list)

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
