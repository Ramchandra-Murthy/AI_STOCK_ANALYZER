from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import mean, stdev
from typing import Any, Dict, List, Mapping, Optional


ENGINE_VERSION = "EROS-3.0-BLOCK-92"
PERFORMANCE_SCHEMA_VERSION = "1.0"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _number(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default

    if not math.isfinite(result):
        return default

    return result


def _dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _first(
    payload: Mapping[str, Any],
    *keys: str,
    default: Any = None,
) -> Any:
    for key in keys:
        if key in payload and payload[key] is not None:
            return payload[key]
    return default


def _hash_payload(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class PortfolioPerformanceRecord:
    performance_id: str
    performance_schema_version: str
    engine_version: str
    timestamp_utc: str

    valuation_id: str
    prior_valuation_id: str

    settlement_id: str
    audit_id: str
    decision_id: str

    portfolio_id: str
    benchmark_name: str

    current_equity: float
    prior_equity: float

    absolute_pnl: float
    return_pct: float

    benchmark_return_pct: Optional[float]
    active_return_pct: Optional[float]

    alpha: Optional[float]
    beta: Optional[float]
    tracking_error_pct: Optional[float]
    information_ratio: Optional[float]

    performance_status: str
    calculation_status: str

    mutation_allowed: bool
    broker_submission: bool
    live_order_submission: bool

    performance_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "performance_id": self.performance_id,
            "performance_schema_version": self.performance_schema_version,
            "engine_version": self.engine_version,
            "timestamp_utc": self.timestamp_utc,
            "valuation_id": self.valuation_id,
            "prior_valuation_id": self.prior_valuation_id,
            "settlement_id": self.settlement_id,
            "audit_id": self.audit_id,
            "decision_id": self.decision_id,
            "portfolio_id": self.portfolio_id,
            "benchmark_name": self.benchmark_name,
            "current_equity": round(self.current_equity, 6),
            "prior_equity": round(self.prior_equity, 6),
            "absolute_pnl": round(self.absolute_pnl, 6),
            "return_pct": round(self.return_pct, 6),
            "benchmark_return_pct": (
                None
                if self.benchmark_return_pct is None
                else round(self.benchmark_return_pct, 6)
            ),
            "active_return_pct": (
                None
                if self.active_return_pct is None
                else round(self.active_return_pct, 6)
            ),
            "alpha": (
                None
                if self.alpha is None
                else round(self.alpha, 6)
            ),
            "beta": (
                None
                if self.beta is None
                else round(self.beta, 6)
            ),
            "tracking_error_pct": (
                None
                if self.tracking_error_pct is None
                else round(self.tracking_error_pct, 6)
            ),
            "information_ratio": (
                None
                if self.information_ratio is None
                else round(self.information_ratio, 6)
            ),
            "performance_status": self.performance_status,
            "calculation_status": self.calculation_status,
            "mutation_allowed": self.mutation_allowed,
            "broker_submission": self.broker_submission,
            "live_order_submission": self.live_order_submission,
            "performance_hash": self.performance_hash,
        }


@dataclass(frozen=True)
class Block92PerformanceCertificate:
    status: str
    performance_id: str
    valuation_id: str
    prior_valuation_id: str
    settlement_id: str
    audit_id: str
    decision_id: str
    portfolio_id: str
    performance_hash: str
    certificate_hash: str
    mutation_allowed: bool
    broker_submission: bool
    live_order_submission: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "performance_id": self.performance_id,
            "valuation_id": self.valuation_id,
            "prior_valuation_id": self.prior_valuation_id,
            "settlement_id": self.settlement_id,
            "audit_id": self.audit_id,
            "decision_id": self.decision_id,
            "portfolio_id": self.portfolio_id,
            "performance_hash": self.performance_hash,
            "certificate_hash": self.certificate_hash,
            "mutation_allowed": self.mutation_allowed,
            "broker_submission": self.broker_submission,
            "live_order_submission": self.live_order_submission,
        }


class EROSBlock92PortfolioPerformanceEngine:
    """
    EROS 3.0 Block 92.

    Authoritative responsibility:
        Certified Block 91 valuation
            ->
        portfolio performance and benchmark analytics.

    Block 92 is read-only.

    It MUST NOT:
        - mutate portfolio state
        - create orders
        - submit orders
        - call a broker
        - alter Block 90 state
        - alter Block 91 valuation
    """

    def __init__(self) -> None:
        self._processed_performance: Dict[str, PortfolioPerformanceRecord] = {}
        self._history: List[Dict[str, Any]] = []

    # ----------------------------------------------------------
    # INPUT EXTRACTION
    # ----------------------------------------------------------

    @staticmethod
    def _valuation(payload: Mapping[str, Any]) -> Dict[str, Any]:
        value = _first(
            payload,
            "valuation",
            "valuation_record",
            "portfolio_valuation",
            default=payload,
        )
        return _dict(value)

    @staticmethod
    def _certificate(payload: Mapping[str, Any]) -> Dict[str, Any]:
        value = _first(
            payload,
            "certificate",
            "valuation_certificate",
            default={},
        )
        return _dict(value)

    @staticmethod
    def _valuation_id(
        valuation: Mapping[str, Any],
        certificate: Mapping[str, Any],
    ) -> str:
        # Block 92 requires valuation lineage to originate from
        # the certified valuation itself. The certificate MUST NOT
        # repair a malformed valuation payload.
        if "valuation_id" in valuation:
            return _text(valuation.get("valuation_id"))
        if "valuation_record_id" in valuation:
            return _text(valuation.get("valuation_record_id"))
        return ""

    @staticmethod
    def _settlement_id(
        valuation: Mapping[str, Any],
        certificate: Mapping[str, Any],
    ) -> str:
        # Settlement lineage must come from the valuation payload.
        if "settlement_id" in valuation:
            return _text(valuation.get("settlement_id"))
        return ""

    @staticmethod
    def _audit_id(
        valuation: Mapping[str, Any],
        certificate: Mapping[str, Any],
    ) -> str:
        # Audit lineage must come from the valuation payload.
        if "audit_id" in valuation:
            return _text(valuation.get("audit_id"))
        return ""

    @staticmethod
    def _decision_id(
        valuation: Mapping[str, Any],
        certificate: Mapping[str, Any],
    ) -> str:
        # Decision lineage must come from the valuation payload.
        if "decision_id" in valuation:
            return _text(valuation.get("decision_id"))
        return ""

    @staticmethod
    def _portfolio_id(valuation: Mapping[str, Any]) -> str:
        return _text(
            _first(
                valuation,
                "portfolio_id",
                "portfolio_name",
                default="",
            )
        )

    @staticmethod
    def _status(
        valuation: Mapping[str, Any],
        certificate: Mapping[str, Any],
    ) -> str:
        return _text(
            _first(
                certificate,
                "status",
                default=_first(
                    valuation,
                    "valuation_status",
                    "status",
                    "state_status",
                    default="",
                ),
            )
        ).upper()

    # ----------------------------------------------------------
    # VALIDATION
    # ----------------------------------------------------------

    def _validate_input(
        self,
        valuation: Mapping[str, Any],
        certificate: Mapping[str, Any],
    ) -> List[str]:
        errors: List[str] = []

        status = self._status(valuation, certificate)

        if status not in {"PASS", "CERTIFIED", "VALUED"}:
            errors.append(
                f"INVALID_VALUATION_STATUS:{status or 'MISSING'}"
            )

        valuation_id = self._valuation_id(valuation, certificate)
        settlement_id = self._settlement_id(valuation, certificate)
        audit_id = self._audit_id(valuation, certificate)
        decision_id = self._decision_id(valuation, certificate)

        if not valuation_id:
            errors.append("MISSING_VALUATION_ID")

        if not settlement_id:
            errors.append("MISSING_SETTLEMENT_ID")

        if not audit_id:
            errors.append("MISSING_AUDIT_ID")

        if not decision_id:
            errors.append("MISSING_DECISION_ID")

        current_equity = _number(
            _first(
                valuation,
                "portfolio_equity",
                "equity",
                "total_equity",
                default=None,
            )
        )

        if current_equity is None:
            errors.append("MISSING_PORTFOLIO_EQUITY")
        elif current_equity < 0:
            errors.append("INVALID_PORTFOLIO_EQUITY")

        return errors

    @staticmethod
    def _benchmark_return(
        benchmark: Optional[Mapping[str, Any]],
    ) -> Optional[float]:
        if not benchmark:
            return None

        value = _first(
            benchmark,
            "return_pct",
            "benchmark_return_pct",
            "return",
        )

        result = _number(value)

        if result is None:
            return None

        return result

    @staticmethod
    def _beta(
        benchmark: Optional[Mapping[str, Any]],
    ) -> Optional[float]:
        if not benchmark:
            return None

        value = _number(
            _first(
                benchmark,
                "beta",
                default=None,
            )
        )

        return value

    @staticmethod
    def _series(
        payload: Optional[Mapping[str, Any]],
        *keys: str,
    ) -> List[float]:
        if not payload:
            return []

        value = _first(payload, *keys, default=[])

        result: List[float] = []

        for item in _list(value):
            number = _number(item)

            if number is not None:
                result.append(number)

        return result

    @staticmethod
    def _tracking_error(
        portfolio_returns: List[float],
        benchmark_returns: List[float],
    ) -> Optional[float]:
        if len(portfolio_returns) != len(benchmark_returns):
            return None

        if len(portfolio_returns) < 2:
            return None

        active = [
            portfolio_returns[index] - benchmark_returns[index]
            for index in range(len(portfolio_returns))
        ]

        return stdev(active)

    @staticmethod
    def _information_ratio(
        portfolio_returns: List[float],
        benchmark_returns: List[float],
    ) -> Optional[float]:
        if len(portfolio_returns) != len(benchmark_returns):
            return None

        if len(portfolio_returns) < 2:
            return None

        active = [
            portfolio_returns[index] - benchmark_returns[index]
            for index in range(len(portfolio_returns))
        ]

        tracking_error = stdev(active)

        if tracking_error == 0:
            return None

        return mean(active) / tracking_error

    # ----------------------------------------------------------
    # PERFORMANCE
    # ----------------------------------------------------------

    def _build_performance(
        self,
        valuation: Mapping[str, Any],
        certificate: Mapping[str, Any],
        prior_valuation: Optional[Mapping[str, Any]],
        benchmark: Optional[Mapping[str, Any]],
    ) -> PortfolioPerformanceRecord:
        valuation_id = self._valuation_id(valuation, certificate)
        settlement_id = self._settlement_id(valuation, certificate)
        audit_id = self._audit_id(valuation, certificate)
        decision_id = self._decision_id(valuation, certificate)
        portfolio_id = self._portfolio_id(valuation)

        current_equity = _number(
            _first(
                valuation,
                "portfolio_equity",
                "equity",
                "total_equity",
                default=0.0,
            ),
            0.0,
        ) or 0.0

        prior_equity = 0.0

        if prior_valuation:
            prior_equity = _number(
                _first(
                    prior_valuation,
                    "portfolio_equity",
                    "equity",
                    "total_equity",
                    default=0.0,
                ),
                0.0,
            ) or 0.0

        absolute_pnl = current_equity - prior_equity

        if prior_valuation is None:
            return_pct = 0.0
        elif prior_equity == 0:
            return_pct = 0.0
        else:
            return_pct = (
                absolute_pnl / prior_equity
            ) * 100.0

        benchmark_return = self._benchmark_return(benchmark)

        active_return = (
            None
            if benchmark_return is None
            else return_pct - benchmark_return
        )

        portfolio_returns = self._series(
            benchmark,
            "portfolio_returns",
        )

        benchmark_returns = self._series(
            benchmark,
            "benchmark_returns",
        )

        tracking_error = self._tracking_error(
            portfolio_returns,
            benchmark_returns,
        )

        information_ratio = self._information_ratio(
            portfolio_returns,
            benchmark_returns,
        )

        beta = self._beta(benchmark)

        # Alpha is only reported when a benchmark return is explicitly
        # supplied. This is a one-period active-return proxy, not a
        # regression-derived Jensen alpha.
        alpha = active_return

        performance_payload = {
            "valuation_id": valuation_id,
            "prior_valuation_id": (
                _text(
                    _first(
                        prior_valuation or {},
                        "valuation_id",
                        "valuation_record_id",
                        default="",
                    )
                )
            ),
            "settlement_id": settlement_id,
            "audit_id": audit_id,
            "decision_id": decision_id,
            "portfolio_id": portfolio_id,
            "benchmark_name": _text(
                _first(
                    benchmark or {},
                    "benchmark_name",
                    "name",
                    default="",
                )
            ),
            "current_equity": current_equity,
            "prior_equity": prior_equity,
            "absolute_pnl": absolute_pnl,
            "return_pct": return_pct,
            "benchmark_return_pct": benchmark_return,
            "active_return_pct": active_return,
            "alpha": alpha,
            "beta": beta,
            "tracking_error_pct": tracking_error,
            "information_ratio": information_ratio,
        }

        performance_hash = _hash_payload(performance_payload)

        performance_id = (
            f"EROS92-{performance_hash[:16].upper()}"
        )

        return PortfolioPerformanceRecord(
            performance_id=performance_id,
            performance_schema_version=PERFORMANCE_SCHEMA_VERSION,
            engine_version=ENGINE_VERSION,
            timestamp_utc=_utc_now(),
            valuation_id=valuation_id,
            prior_valuation_id=performance_payload[
                "prior_valuation_id"
            ],
            settlement_id=settlement_id,
            audit_id=audit_id,
            decision_id=decision_id,
            portfolio_id=portfolio_id,
            benchmark_name=performance_payload[
                "benchmark_name"
            ],
            current_equity=current_equity,
            prior_equity=prior_equity,
            absolute_pnl=absolute_pnl,
            return_pct=return_pct,
            benchmark_return_pct=benchmark_return,
            active_return_pct=active_return,
            alpha=alpha,
            beta=beta,
            tracking_error_pct=tracking_error,
            information_ratio=information_ratio,
            performance_status="CALCULATED",
            calculation_status="CERTIFIED",
            mutation_allowed=False,
            broker_submission=False,
            live_order_submission=False,
            performance_hash=performance_hash,
        )

    def _certificate_for(
        self,
        performance: PortfolioPerformanceRecord,
        status: str,
    ) -> Block92PerformanceCertificate:
        payload = {
            "status": status,
            "performance_id": performance.performance_id,
            "valuation_id": performance.valuation_id,
            "prior_valuation_id": performance.prior_valuation_id,
            "settlement_id": performance.settlement_id,
            "audit_id": performance.audit_id,
            "decision_id": performance.decision_id,
            "portfolio_id": performance.portfolio_id,
            "performance_hash": performance.performance_hash,
            "mutation_allowed": False,
            "broker_submission": False,
            "live_order_submission": False,
        }

        certificate_hash = _hash_payload(payload)

        return Block92PerformanceCertificate(
            status=status,
            performance_id=performance.performance_id,
            valuation_id=performance.valuation_id,
            prior_valuation_id=performance.prior_valuation_id,
            settlement_id=performance.settlement_id,
            audit_id=performance.audit_id,
            decision_id=performance.decision_id,
            portfolio_id=performance.portfolio_id,
            performance_hash=performance.performance_hash,
            certificate_hash=certificate_hash,
            mutation_allowed=False,
            broker_submission=False,
            live_order_submission=False,
        )

    # ----------------------------------------------------------
    # PUBLIC API
    # ----------------------------------------------------------

    def calculate_performance(
        self,
        valuation_payload: Mapping[str, Any],
        prior_valuation: Optional[Mapping[str, Any]] = None,
        benchmark: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        valuation = self._valuation(valuation_payload)
        certificate = self._certificate(valuation_payload)

        errors = self._validate_input(
            valuation,
            certificate,
        )

        if errors:
            return {
                "status": "BLOCKED",
                "calculation_status": "BLOCKED",
                "errors": errors,
                "performance": None,
                "certificate": None,
                "mutation_allowed": False,
                "broker_submission": False,
                "live_order_submission": False,
            }

        performance = self._build_performance(
            valuation,
            certificate,
            prior_valuation,
            benchmark,
        )

        if performance.performance_id in self._processed_performance:
            existing = self._processed_performance[
                performance.performance_id
            ]

            return {
                "status": "DUPLICATE",
                "calculation_status": "DUPLICATE",
                "performance": existing.to_dict(),
                "certificate": self._certificate_for(
                    existing,
                    "DUPLICATE",
                ).to_dict(),
                "mutation_allowed": False,
                "broker_submission": False,
                "live_order_submission": False,
            }

        self._processed_performance[
            performance.performance_id
        ] = performance

        record = performance.to_dict()

        self._history.append(record)

        certificate_result = self._certificate_for(
            performance,
            "CERTIFIED",
        )

        return {
            "status": "PASS",
            "calculation_status": "CERTIFIED",
            "performance": record,
            "certificate": certificate_result.to_dict(),
            "mutation_allowed": False,
            "broker_submission": False,
            "live_order_submission": False,
        }

    def benchmark_performance(
        self,
        valuation_payload: Mapping[str, Any],
        prior_valuation: Optional[Mapping[str, Any]] = None,
        benchmark: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.calculate_performance(
            valuation_payload,
            prior_valuation=prior_valuation,
            benchmark=benchmark,
        )

    def snapshot(self) -> Dict[str, Any]:
        return {
            "engine_version": ENGINE_VERSION,
            "performance_schema_version": PERFORMANCE_SCHEMA_VERSION,
            "performance_count": len(
                self._processed_performance
            ),
            "history_count": len(self._history),
            "mutation_allowed": False,
            "broker_submission": False,
            "live_order_submission": False,
            "performance_ids": sorted(
                self._processed_performance.keys()
            ),
        }

    def performance_history(self) -> List[Dict[str, Any]]:
        return [dict(item) for item in self._history]

