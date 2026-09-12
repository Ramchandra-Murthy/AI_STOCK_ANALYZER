"""
EROS 3.0 - Canonical Data Contracts

The canonical objects passed between:
data -> normalization -> quality -> scoring
-> classification -> valuation -> decision -> evidence -> API
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FinancialSnapshot:
    symbol: str

    revenue: float | None = None
    ebitda: float | None = None
    ebit: float | None = None
    pat: float | None = None
    eps: float | None = None

    total_assets: float | None = None
    total_debt: float | None = None
    cash: float | None = None
    equity: float | None = None

    operating_cash_flow: float | None = None
    free_cash_flow: float | None = None

    shares_outstanding: float | None = None
    market_cap: float | None = None
    current_price: float | None = None

    currency: str = "INR"
    period: str | None = None

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
    score: float | None = None
    components: dict[str, float] = field(default_factory=dict)
    rationale: list[str] = field(default_factory=list)


@dataclass
class ClassificationResult:
    classification: str | None = None
    confidence: float | None = None
    rationale: list[str] = field(default_factory=list)


@dataclass
class ValuationResult:
    value: float | None = None
    low: float | None = None
    high: float | None = None
    method: str | None = None
    currency: str = "INR"
    assumptions: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


@dataclass
class Evidence:
    source: str
    field: str
    value: Any = None
    period: str | None = None
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class EROSResult:
    symbol: str

    financials: FinancialSnapshot | None = None
    quality: QualityResult | None = None
    score: ScoreResult | None = None
    classification: ClassificationResult | None = None

    sotp: ValuationResult | None = None
    dcf: ValuationResult | None = None
    bridge: ValuationResult | None = None

    stage13c: dict[str, Any] | None = None
    stage14: dict[str, Any] | None = None

    evidence: list[Evidence] = field(default_factory=list)

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
