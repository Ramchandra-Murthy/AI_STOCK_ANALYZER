"""
EROS 3.0 - BLOCK 93
Performance Risk / Attribution Certification Engine.

Architectural boundary
----------------------
Block 90 owns portfolio state.
Block 91 owns portfolio valuation.
Block 92 owns portfolio performance.
Block 93 owns read-only performance risk and attribution certification.

This module deliberately has no broker, order, execution, portfolio-state mutation,
valuation mutation, or optimization capability.

The implementation is intentionally defensive:
- strict lineage validation
- deterministic numeric handling
- explicit status/reason codes
- controlled baseline behavior
- duplicate certificate protection
- immutable certificate snapshots
- history isolation
- benchmark-relative risk analytics
- security-level and portfolio-level attribution
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from math import isfinite, sqrt
from statistics import mean, pstdev, stdev
from types import MappingProxyType
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


BLOCK93_VERSION = "EROS-3.0-BLOCK-93.1"
STATUS_CERTIFIED = "CERTIFIED"
STATUS_BLOCKED = "BLOCKED"
STATUS_DUPLICATE = "DUPLICATE"
STATUS_BASELINE = "BASELINE"

REASON_CERTIFIED = "CERTIFIED"
REASON_MISSING_PERFORMANCE_ID = "MISSING_PERFORMANCE_ID"
REASON_MISSING_VALUATION_ID = "MISSING_VALUATION_ID"
REASON_MISSING_SETTLEMENT_ID = "MISSING_SETTLEMENT_ID"
REASON_MISSING_AUDIT_ID = "MISSING_AUDIT_ID"
REASON_MISSING_DECISION_ID = "MISSING_DECISION_ID"
REASON_INVALID_PERFORMANCE_STATUS = "INVALID_PERFORMANCE_STATUS"
REASON_INVALID_EQUITY = "INVALID_EQUITY"
REASON_INVALID_RETURN = "INVALID_RETURN"
REASON_INVALID_BENCHMARK = "INVALID_BENCHMARK"
REASON_INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
REASON_DUPLICATE_PERFORMANCE = "DUPLICATE_PERFORMANCE"
REASON_DUPLICATE_CERTIFICATE = "DUPLICATE_CERTIFICATE"
REASON_MALFORMED_OBSERVATION = "MALFORMED_OBSERVATION"
REASON_INVALID_DATE_ORDER = "INVALID_DATE_ORDER"
REASON_INVALID_SECURITY_DATA = "INVALID_SECURITY_DATA"
REASON_NO_ATTRIBUTION_DATA = "NO_ATTRIBUTION_DATA"


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _number(value: Any, default: Optional[float] = None) -> float:
    if value is None or value == "":
        if default is not None:
            return float(default)
        raise ValueError("INVALID_NUMERIC_VALUE")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("INVALID_NUMERIC_VALUE") from exc
    if not isfinite(result):
        raise ValueError("NON_FINITE_NUMERIC_VALUE")
    return result


def _round(value: float, places: int = 10) -> float:
    return round(float(value), places)


def _mean(values: Sequence[float]) -> float:
    return mean(values) if values else 0.0


def _population_volatility(values: Sequence[float]) -> float:
    return pstdev(values) if len(values) >= 2 else 0.0


def _sample_volatility(values: Sequence[float]) -> float:
    return stdev(values) if len(values) >= 2 else 0.0


def _safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    if abs(denominator) <= 1e-15:
        return default
    return numerator / denominator


def _covariance(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    mx = _mean(x)
    my = _mean(y)
    return _mean([(a - mx) * (b - my) for a, b in zip(x, y)])


def _variance(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    return _mean([(x - m) ** 2 for x in values])


def _return_from_equity(current: float, prior: float) -> float:
    if prior == 0:
        raise ValueError("ZERO_BASELINE")
    return current / prior - 1.0


def _certificate_hash(payload: Mapping[str, Any]) -> str:
    normalized = repr(sorted((str(k), repr(v)) for k, v in payload.items())).encode("utf-8")
    return sha256(normalized).hexdigest().upper()


def _immutable_copy(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(k): _immutable_copy(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_immutable_copy(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_immutable_copy(v) for v in value)
    return value


@dataclass(frozen=True)
class PerformanceObservation:
    period: str
    portfolio_return: float
    benchmark_return: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "period": self.period,
            "portfolio_return": _round(self.portfolio_return),
            "benchmark_return": _round(self.benchmark_return),
            "active_return": _round(self.portfolio_return - self.benchmark_return),
        }


@dataclass(frozen=True)
class RiskMetrics:
    observation_count: int
    volatility: float
    downside_volatility: float
    maximum_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    beta: float
    alpha: float
    tracking_error: float
    information_ratio: float
    cumulative_return: float
    benchmark_cumulative_return: float
    active_return: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "observation_count": self.observation_count,
            "volatility": _round(self.volatility),
            "downside_volatility": _round(self.downside_volatility),
            "maximum_drawdown": _round(self.maximum_drawdown),
            "sharpe_ratio": _round(self.sharpe_ratio),
            "sortino_ratio": _round(self.sortino_ratio),
            "beta": _round(self.beta),
            "alpha": _round(self.alpha),
            "tracking_error": _round(self.tracking_error),
            "information_ratio": _round(self.information_ratio),
            "cumulative_return": _round(self.cumulative_return),
            "benchmark_cumulative_return": _round(self.benchmark_cumulative_return),
            "active_return": _round(self.active_return),
        }


@dataclass(frozen=True)
class AttributionRecord:
    symbol: str
    portfolio_weight: float
    benchmark_weight: float
    portfolio_return: float
    benchmark_return: float
    portfolio_contribution: float
    benchmark_contribution: float
    active_contribution: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "portfolio_weight": _round(self.portfolio_weight),
            "benchmark_weight": _round(self.benchmark_weight),
            "portfolio_return": _round(self.portfolio_return),
            "benchmark_return": _round(self.benchmark_return),
            "portfolio_contribution": _round(self.portfolio_contribution),
            "benchmark_contribution": _round(self.benchmark_contribution),
            "active_contribution": _round(self.active_contribution),
        }


@dataclass(frozen=True)
class Block93Certificate:
    certificate_id: str
    status: str
    reason_code: str
    performance_id: str
    valuation_id: str
    settlement_id: str
    audit_id: str
    decision_id: str
    observation_count: int
    metrics: Mapping[str, Any]
    attribution: Tuple[Mapping[str, Any], ...]
    certificate_hash: str
    version: str = BLOCK93_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "certificate_id": self.certificate_id,
            "status": self.status,
            "reason_code": self.reason_code,
            "performance_id": self.performance_id,
            "valuation_id": self.valuation_id,
            "settlement_id": self.settlement_id,
            "audit_id": self.audit_id,
            "decision_id": self.decision_id,
            "observation_count": self.observation_count,
            "metrics": dict(self.metrics),
            "attribution": [dict(x) for x in self.attribution],
            "certificate_hash": self.certificate_hash,
            "version": self.version,
        }


class EROSBlock93PerformanceRiskAttributionEngine:
    """
    Read-only risk and attribution authority for EROS 3.0 Block 93.

    The engine owns only analytical certificates and their history. It never
    writes to Block 90, Block 91, Block 92, a broker, an order queue, or an
    execution subsystem.
    """

    def __init__(
        self,
        *,
        risk_free_rate: float = 0.0,
        target_return: float = 0.0,
        minimum_history: int = 2,
    ) -> None:
        self.risk_free_rate = _number(risk_free_rate)
        self.target_return = _number(target_return)
        if minimum_history < 1:
            raise ValueError("minimum_history must be >= 1")
        self.minimum_history = int(minimum_history)
        self._certificates: Dict[str, Block93Certificate] = {}
        self._performance_ids: set[str] = set()
        self._history: List[Dict[str, Any]] = []

    # ------------------------------------------------------
    # Lineage extraction
    # ------------------------------------------------------

    @staticmethod
    def _performance_id(performance: Mapping[str, Any]) -> str:
        return _text(
            performance.get("performance_id")
            or performance.get("performance_record_id")
        )

    @staticmethod
    def _valuation_id(performance: Mapping[str, Any]) -> str:
        return _text(performance.get("valuation_id"))

    @staticmethod
    def _settlement_id(performance: Mapping[str, Any]) -> str:
        return _text(performance.get("settlement_id"))

    @staticmethod
    def _audit_id(performance: Mapping[str, Any]) -> str:
        return _text(performance.get("audit_id"))

    @staticmethod
    def _decision_id(performance: Mapping[str, Any]) -> str:
        return _text(performance.get("decision_id"))

    @staticmethod
    def _status(performance: Mapping[str, Any]) -> str:
        return _text(
            performance.get("performance_status")
            or performance.get("status")
        ).upper()

    def _lineage_error(self, performance: Mapping[str, Any]) -> Optional[str]:
        if not self._performance_id(performance):
            return REASON_MISSING_PERFORMANCE_ID
        if not self._valuation_id(performance):
            return REASON_MISSING_VALUATION_ID
        if not self._settlement_id(performance):
            return REASON_MISSING_SETTLEMENT_ID
        if not self._audit_id(performance):
            return REASON_MISSING_AUDIT_ID
        if not self._decision_id(performance):
            return REASON_MISSING_DECISION_ID
        return None

    # ------------------------------------------------------
    # Observation parsing
    # ------------------------------------------------------

    @staticmethod
    def _observations(
        performance: Mapping[str, Any],
    ) -> Tuple[PerformanceObservation, ...]:
        raw = performance.get("performance_history")
        if raw is None:
            raw = performance.get("history")
        if raw is None:
            raw = performance.get("observations")
        if raw is None:
            raw = []

        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            raise ValueError(REASON_MALFORMED_OBSERVATION)

        result: List[PerformanceObservation] = []
        previous_period = ""
        for item in raw:
            if not isinstance(item, Mapping):
                raise ValueError(REASON_MALFORMED_OBSERVATION)

            period = _text(item.get("period") or item.get("date") or item.get("timestamp"))
            if not period:
                raise ValueError(REASON_MALFORMED_OBSERVATION)
            if previous_period and period < previous_period:
                raise ValueError(REASON_INVALID_DATE_ORDER)
            previous_period = period

            if "portfolio_return" in item:
                portfolio_return = _number(item["portfolio_return"])
                if abs(portfolio_return) > 10:
                    raise ValueError(REASON_INVALID_RETURN)
            elif "return_pct" in item:
                portfolio_return = _number(item["return_pct"]) / 100.0
            elif "portfolio_return_pct" in item:
                portfolio_return = _number(item["portfolio_return_pct"]) / 100.0
            else:
                raise ValueError(REASON_MALFORMED_OBSERVATION)

            if "benchmark_return" in item:
                benchmark_return = _number(item["benchmark_return"])
                if abs(benchmark_return) > 10:
                    raise ValueError(REASON_INVALID_BENCHMARK)
            elif "benchmark_return_pct" in item:
                benchmark_return = _number(item["benchmark_return"]) / 100.0
            else:
                benchmark_return = 0.0

            result.append(
                PerformanceObservation(
                    period=period,
                    portfolio_return=portfolio_return,
                    benchmark_return=benchmark_return,
                )
            )

        return tuple(result)

    @staticmethod
    def _equity_history(performance: Mapping[str, Any]) -> Tuple[float, ...]:
        raw = performance.get("equity_history")
        if raw is None:
            return tuple()

        if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
            raise ValueError(REASON_MALFORMED_OBSERVATION)

        result = tuple(_number(x) for x in raw)
        if any(x <= 0 for x in result):
            raise ValueError(REASON_INVALID_EQUITY)
        return result

    # ------------------------------------------------------
    # Risk calculations
    # ------------------------------------------------------

    def _calculate_volatility(self, returns: Sequence[float]) -> float:
        return _sample_volatility(returns)

    def _calculate_downside_volatility(self, returns: Sequence[float]) -> float:
        downside = [
            min(0.0, value - self.target_return)
            for value in returns
        ]
        return sqrt(_mean([x * x for x in downside]))

    def _calculate_max_drawdown(
        self,
        returns: Sequence[float],
        equity_history: Sequence[float],
    ) -> float:
        if len(equity_history) >= 2:
            peak = equity_history[0]
            maximum = 0.0
            for equity in equity_history:
                peak = max(peak, equity)
                drawdown = _safe_div(equity - peak, peak)
                maximum = min(maximum, drawdown)
            return abs(maximum)

        wealth = 1.0
        peak = wealth
        maximum = 0.0
        for value in returns:
            wealth *= 1.0 + value
            peak = max(peak, wealth)
            maximum = min(maximum, _safe_div(wealth - peak, peak))
        return abs(maximum)

    def _calculate_sharpe(self, returns: Sequence[float]) -> float:
        excess = [x - self.risk_free_rate for x in returns]
        return _safe_div(_mean(excess), _sample_volatility(excess))

    def _calculate_sortino(self, returns: Sequence[float]) -> float:
        excess = [x - self.target_return for x in returns]
        downside = self._calculate_downside_volatility(returns)
        return _safe_div(_mean(excess), downside)

    def _calculate_beta(
        self,
        portfolio_returns: Sequence[float],
        benchmark_returns: Sequence[float],
    ) -> float:
        return _safe_div(
            _covariance(portfolio_returns, benchmark_returns),
            _variance(benchmark_returns),
        )

    def _calculate_alpha(
        self,
        portfolio_returns: Sequence[float],
        benchmark_returns: Sequence[float],
    ) -> float:
        beta = self._calculate_beta(portfolio_returns, benchmark_returns)
        return _mean(portfolio_returns) - (
            self.risk_free_rate
            + beta * (_mean(benchmark_returns) - self.risk_free_rate)
        )

    def _calculate_tracking_error(
        self,
        portfolio_returns: Sequence[float],
        benchmark_returns: Sequence[float],
    ) -> float:
        active = [
            p - b
            for p, b in zip(portfolio_returns, benchmark_returns)
        ]
        return _sample_volatility(active)

    def _calculate_information_ratio(
        self,
        portfolio_returns: Sequence[float],
        benchmark_returns: Sequence[float],
    ) -> float:
        active = [
            p - b
            for p, b in zip(portfolio_returns, benchmark_returns)
        ]
        return _safe_div(_mean(active), _sample_volatility(active))

    @staticmethod
    def _compound(values: Sequence[float]) -> float:
        wealth = 1.0
        for value in values:
            wealth *= 1.0 + value
        return wealth - 1.0

    def calculate_risk_metrics(
        self,
        performance: Mapping[str, Any],
    ) -> Dict[str, Any]:
        observations = self._observations(performance)
        if len(observations) < self.minimum_history:
            raise ValueError(REASON_INSUFFICIENT_HISTORY)

        portfolio_returns = [x.portfolio_return for x in observations]
        benchmark_returns = [x.benchmark_return for x in observations]
        equity_history = self._equity_history(performance)

        metrics = RiskMetrics(
            observation_count=len(observations),
            volatility=self._calculate_volatility(portfolio_returns),
            downside_volatility=self._calculate_downside_volatility(portfolio_returns),
            maximum_drawdown=self._calculate_max_drawdown(
                portfolio_returns,
                equity_history,
            ),
            sharpe_ratio=self._calculate_sharpe(portfolio_returns),
            sortino_ratio=self._calculate_sortino(portfolio_returns),
            beta=self._calculate_beta(
                portfolio_returns,
                benchmark_returns,
            ),
            alpha=self._calculate_alpha(
                portfolio_returns,
                benchmark_returns,
            ),
            tracking_error=self._calculate_tracking_error(
                portfolio_returns,
                benchmark_returns,
            ),
            information_ratio=self._calculate_information_ratio(
                portfolio_returns,
                benchmark_returns,
            ),
            cumulative_return=self._compound(portfolio_returns),
            benchmark_cumulative_return=self._compound(benchmark_returns),
            active_return=(
                self._compound(portfolio_returns)
                - self._compound(benchmark_returns)
            ),
        )
        return metrics.to_dict()

    # ------------------------------------------------------
    # Attribution
    # ------------------------------------------------------

    @staticmethod
    def _attribution_source(
        performance: Mapping[str, Any],
    ) -> Sequence[Mapping[str, Any]]:
        raw = performance.get("attribution")
        if raw is None:
            raw = performance.get("positions_attribution")
        if raw is None:
            raw = performance.get("security_attribution")
        return raw or []

    def calculate_attribution(
        self,
        performance: Mapping[str, Any],
    ) -> List[Dict[str, Any]]:
        raw = self._attribution_source(performance)
        if not raw:
            return []

        records: List[AttributionRecord] = []
        for item in raw:
            if not isinstance(item, Mapping):
                raise ValueError(REASON_INVALID_SECURITY_DATA)

            symbol = _text(item.get("symbol") or item.get("security"))
            if not symbol:
                raise ValueError(REASON_INVALID_SECURITY_DATA)

            portfolio_weight = _number(
                item.get("portfolio_weight", item.get("weight", 0.0))
            )
            benchmark_weight = _number(
                item.get("benchmark_weight", 0.0)
            )
            portfolio_return = _number(
                item.get("portfolio_return", item.get("return", 0.0))
            )
            benchmark_return = _number(
                item.get("benchmark_return", 0.0)
            )

            records.append(
                AttributionRecord(
                    symbol=symbol,
                    portfolio_weight=portfolio_weight,
                    benchmark_weight=benchmark_weight,
                    portfolio_return=portfolio_return,
                    benchmark_return=benchmark_return,
                    portfolio_contribution=portfolio_weight * portfolio_return,
                    benchmark_contribution=benchmark_weight * benchmark_return,
                    active_contribution=(
                        portfolio_weight * portfolio_return
                        - benchmark_weight * benchmark_return
                    ),
                )
            )

        records.sort(key=lambda x: x.symbol)
        return [x.to_dict() for x in records]

    def benchmark_risk(
        self,
        performance: Mapping[str, Any],
    ) -> Dict[str, Any]:
        observations = self._observations(performance)
        if len(observations) < self.minimum_history:
            raise ValueError(REASON_INSUFFICIENT_HISTORY)

        benchmark = [x.benchmark_return for x in observations]
        return {
            "benchmark_observation_count": len(benchmark),
            "benchmark_volatility": _round(_sample_volatility(benchmark)),
            "benchmark_cumulative_return": _round(self._compound(benchmark)),
            "benchmark_mean_return": _round(_mean(benchmark)),
            "benchmark_downside_volatility": _round(
                sqrt(
                    _mean(
                        [
                            min(0.0, x - self.target_return) ** 2
                            for x in benchmark
                        ]
                    )
                )
            ),
        }

    # ------------------------------------------------------
    # Certificate construction
    # ------------------------------------------------------

    def _certificate_payload(
        self,
        *,
        performance: Mapping[str, Any],
        metrics: Mapping[str, Any],
        attribution: Sequence[Mapping[str, Any]],
        status: str,
        reason_code: str,
    ) -> Dict[str, Any]:
        return {
            "version": BLOCK93_VERSION,
            "status": status,
            "reason_code": reason_code,
            "performance_id": self._performance_id(performance),
            "valuation_id": self._valuation_id(performance),
            "settlement_id": self._settlement_id(performance),
            "audit_id": self._audit_id(performance),
            "decision_id": self._decision_id(performance),
            "metrics": dict(metrics),
            "attribution": [dict(x) for x in attribution],
        }

    def _make_certificate(
        self,
        *,
        performance: Mapping[str, Any],
        metrics: Mapping[str, Any],
        attribution: Sequence[Mapping[str, Any]],
        status: str = STATUS_CERTIFIED,
        reason_code: str = REASON_CERTIFIED,
    ) -> Block93Certificate:
        payload = self._certificate_payload(
            performance=performance,
            metrics=metrics,
            attribution=attribution,
            status=status,
            reason_code=reason_code,
        )
        digest = _certificate_hash(payload)
        certificate_id = f"EROS93-{digest[:20]}"

        return Block93Certificate(
            certificate_id=certificate_id,
            status=status,
            reason_code=reason_code,
            performance_id=payload["performance_id"],
            valuation_id=payload["valuation_id"],
            settlement_id=payload["settlement_id"],
            audit_id=payload["audit_id"],
            decision_id=payload["decision_id"],
            observation_count=int(metrics.get("observation_count", 0)),
            metrics=_immutable_copy(dict(metrics)),
            attribution=tuple(
                _immutable_copy(dict(x))
                for x in attribution
            ),
            certificate_hash=digest,
        )

    # ------------------------------------------------------
    # Public certification API
    # ------------------------------------------------------

    def certify(
        self,
        performance: Mapping[str, Any],
    ) -> Dict[str, Any]:
        if not isinstance(performance, Mapping):
            return {
                "status": STATUS_BLOCKED,
                "reason_code": REASON_MALFORMED_OBSERVATION,
            }

        if self._status(performance) != STATUS_CERTIFIED:
            return {
                "status": STATUS_BLOCKED,
                "reason_code": REASON_INVALID_PERFORMANCE_STATUS,
                "performance_id": self._performance_id(performance),
            }

        lineage_error = self._lineage_error(performance)
        if lineage_error:
            return {
                "status": STATUS_BLOCKED,
                "reason_code": lineage_error,
                "performance_id": self._performance_id(performance),
            }

        performance_id = self._performance_id(performance)
        if performance_id in self._performance_ids:
            return {
                "status": STATUS_DUPLICATE,
                "reason_code": REASON_DUPLICATE_PERFORMANCE,
                "performance_id": performance_id,
            }

        try:
            observations = self._observations(performance)
            if len(observations) < self.minimum_history:
                return {
                    "status": STATUS_BLOCKED,
                    "reason_code": REASON_INSUFFICIENT_HISTORY,
                    "performance_id": performance_id,
                }

            metrics = self.calculate_risk_metrics(performance)
            attribution = self.calculate_attribution(performance)
            benchmark_metrics = self.benchmark_risk(performance)
            metrics = {
                **metrics,
                **benchmark_metrics,
            }
        except ValueError as exc:
            return {
                "status": STATUS_BLOCKED,
                "reason_code": str(exc),
                "performance_id": performance_id,
            }

        certificate = self._make_certificate(
            performance=performance,
            metrics=metrics,
            attribution=attribution,
        )

        if certificate.certificate_id in self._certificates:
            return {
                "status": STATUS_DUPLICATE,
                "reason_code": REASON_DUPLICATE_CERTIFICATE,
                "certificate_id": certificate.certificate_id,
            }

        self._certificates[certificate.certificate_id] = certificate
        self._performance_ids.add(performance_id)
        self._history.append(certificate.to_dict())

        result = certificate.to_dict()
        result["status"] = STATUS_CERTIFIED
        result["risk_metrics"] = dict(metrics)
        result["attribution"] = [dict(x) for x in attribution]
        result["non_bypass_invariant"] = True
        result["broker_submission"] = False
        result["live_order_submission"] = False
        return result

    def value_performance(
        self,
        performance: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Alias-style analytical entry point for downstream consumers."""
        return self.certify(performance)

    def snapshot(self) -> Dict[str, Any]:
        return {
            "version": BLOCK93_VERSION,
            "certificate_count": len(self._certificates),
            "performance_count": len(self._performance_ids),
            "history_count": len(self._history),
            "certificates": [
                self._certificates[key].to_dict()
                for key in sorted(self._certificates)
            ],
        }

    def certificate_history(self) -> List[Dict[str, Any]]:
        return [
            dict(item)
            for item in self._history
        ]

    def get_certificate(
        self,
        certificate_id: str,
    ) -> Optional[Dict[str, Any]]:
        certificate = self._certificates.get(_text(certificate_id))
        return certificate.to_dict() if certificate else None

    # ------------------------------------------------------
    # Explicit forbidden-operation API
    # ------------------------------------------------------

    def create_order(self, *_: Any, **__: Any) -> Dict[str, Any]:
        return {
            "status": STATUS_BLOCKED,
            "reason_code": "ORDER_CREATION_FORBIDDEN",
        }

    def submit_broker_order(self, *_: Any, **__: Any) -> Dict[str, Any]:
        return {
            "status": STATUS_BLOCKED,
            "reason_code": "BROKER_SUBMISSION_FORBIDDEN",
        }

    def execute_live_order(self, *_: Any, **__: Any) -> Dict[str, Any]:
        return {
            "status": STATUS_BLOCKED,
            "reason_code": "LIVE_EXECUTION_FORBIDDEN",
        }

    def mutate_portfolio(self, *_: Any, **__: Any) -> Dict[str, Any]:
        return {
            "status": STATUS_BLOCKED,
            "reason_code": "PORTFOLIO_MUTATION_FORBIDDEN",
        }

    def mutate_valuation(self, *_: Any, **__: Any) -> Dict[str, Any]:
        return {
            "status": STATUS_BLOCKED,
            "reason_code": "VALUATION_MUTATION_FORBIDDEN",
        }

    def optimize_portfolio(self, *_: Any, **__: Any) -> Dict[str, Any]:
        return {
            "status": STATUS_BLOCKED,
            "reason_code": "PORTFOLIO_OPTIMIZATION_FORBIDDEN",
        }


__all__ = [
    "BLOCK93_VERSION",
    "STATUS_CERTIFIED",
    "STATUS_BLOCKED",
    "STATUS_DUPLICATE",
    "STATUS_BASELINE",
    "PerformanceObservation",
    "RiskMetrics",
    "AttributionRecord",
    "Block93Certificate",
    "EROSBlock93PerformanceRiskAttributionEngine",
]
