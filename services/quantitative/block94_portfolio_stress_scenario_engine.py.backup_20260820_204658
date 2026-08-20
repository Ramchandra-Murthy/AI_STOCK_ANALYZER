"""
EROS 3.0 - Block 94
Portfolio Stress / Scenario Engine

Architectural authority
-----------------------
Block 94 owns deterministic portfolio stress and scenario analysis.

Upstream:
    Block 90 -> portfolio state
    Block 91 -> portfolio valuation
    Block 92 -> portfolio performance
    Block 93 -> performance risk / attribution

Block 94:
    stress / scenario analysis only

Downstream:
    Block 95 may consume certified stress evidence.

Hard boundaries:
    * no portfolio state mutation
    * no valuation mutation
    * no performance mutation
    * no risk-certificate mutation
    * no optimization
    * no order creation
    * no broker submission
    * no live execution

The implementation intentionally uses only the Python standard library.
All public calculations are deterministic for identical inputs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from math import isfinite
from statistics import mean
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
import copy
import json
import math


# ============================================================
# CONSTANTS
# ============================================================

BLOCK_ID = "EROS-BLOCK-94"
ENGINE_VERSION = "94.1.0"

STATUS_PASS = "PASS"
STATUS_BLOCKED = "BLOCKED"
STATUS_DUPLICATE = "DUPLICATE"
STATUS_CERTIFIED = "CERTIFIED"

CERTIFICATE_PREFIX = "EROS94-STRESS"

ALLOWED_SCENARIO_TYPES = {
    "PRICE",
    "MARKET",
    "VOLATILITY",
    "BENCHMARK",
    "SECTOR",
    "LIQUIDITY",
    "CORRELATION",
    "DOWNSIDE",
    "UPSIDE",
    "COMBINED",
}

_FORBIDDEN_KEYS = {
    "order",
    "orders",
    "broker",
    "broker_submission",
    "live_order",
    "live_execution",
    "execute_order",
    "submit_order",
    "trade",
}


# ============================================================
# LOW-LEVEL HELPERS
# ============================================================

def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default

    if not isfinite(number):
        return default

    return number


def _positive_float(value: Any) -> Optional[float]:
    number = _float(value)
    if number is None or number <= 0:
        return None
    return number


def _non_negative_float(value: Any) -> Optional[float]:
    number = _float(value)
    if number is None or number < 0:
        return None
    return number


def _number(value: Any) -> float:
    number = _float(value)
    if number is None:
        raise ValueError("invalid numeric value")
    return number


def _canonical(value: Any) -> Any:
    """
    Convert arbitrary mappings/sequences into deterministic JSON-safe
    structures suitable for hashing.
    """
    if isinstance(value, Mapping):
        return {
            str(key): _canonical(value[key])
            for key in sorted(value.keys(), key=lambda item: str(item))
        }

    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]

    if isinstance(value, float):
        if not isfinite(value):
            return str(value)
        return round(value, 12)

    if isinstance(value, (str, int, bool)) or value is None:
        return value

    return str(value)


def _hash_payload(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        _canonical(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")

    return sha256(encoded).hexdigest().upper()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _deepcopy(value: Any) -> Any:
    return copy.deepcopy(value)


def _contains_forbidden_content(value: Any) -> bool:
    """
    Recursively reject execution-oriented payload fields.

    This is intentionally strict. Block 94 is an analytical authority and
    should fail closed if execution semantics are supplied to it.
    """
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower()
            if normalized in _FORBIDDEN_KEYS:
                return True
            if _contains_forbidden_content(child):
                return True

    elif isinstance(value, (list, tuple)):
        return any(_contains_forbidden_content(item) for item in value)

    return False


def _first(mapping: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return default


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass(frozen=True)
class ScenarioDefinition:
    scenario_id: str
    scenario_type: str
    name: str
    description: str = ""
    price_shock_pct: float = 0.0
    market_shock_pct: float = 0.0
    volatility_shock_pct: float = 0.0
    benchmark_shock_pct: float = 0.0
    sector_shock_pct: float = 0.0
    liquidity_shock_pct: float = 0.0
    correlation_shock_pct: float = 0.0
    default_shock_pct: float = 0.0
    sector: str = ""
    benchmark: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def normalized(self) -> "ScenarioDefinition":
        return ScenarioDefinition(
            scenario_id=_text(self.scenario_id),
            scenario_type=_text(self.scenario_type).upper(),
            name=_text(self.name),
            description=_text(self.description),
            price_shock_pct=_number(self.price_shock_pct),
            market_shock_pct=_number(self.market_shock_pct),
            volatility_shock_pct=_number(self.volatility_shock_pct),
            benchmark_shock_pct=_number(self.benchmark_shock_pct),
            sector_shock_pct=_number(self.sector_shock_pct),
            liquidity_shock_pct=_number(self.liquidity_shock_pct),
            correlation_shock_pct=_number(self.correlation_shock_pct),
            default_shock_pct=_number(self.default_shock_pct),
            sector=_text(self.sector),
            benchmark=_text(self.benchmark),
            metadata=_deepcopy(dict(self.metadata)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_type": self.scenario_type,
            "name": self.name,
            "description": self.description,
            "price_shock_pct": self.price_shock_pct,
            "market_shock_pct": self.market_shock_pct,
            "volatility_shock_pct": self.volatility_shock_pct,
            "benchmark_shock_pct": self.benchmark_shock_pct,
            "sector_shock_pct": self.sector_shock_pct,
            "liquidity_shock_pct": self.liquidity_shock_pct,
            "correlation_shock_pct": self.correlation_shock_pct,
            "default_shock_pct": self.default_shock_pct,
            "sector": self.sector,
            "benchmark": self.benchmark,
            "metadata": _deepcopy(dict(self.metadata)),
        }


@dataclass(frozen=True)
class PositionExposure:
    symbol: str
    quantity: float
    price: float
    market_value: float
    sector: str = ""
    beta: float = 1.0
    volatility: float = 0.0
    liquidity_factor: float = 1.0
    benchmark: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "price": self.price,
            "market_value": self.market_value,
            "sector": self.sector,
            "beta": self.beta,
            "volatility": self.volatility,
            "liquidity_factor": self.liquidity_factor,
            "benchmark": self.benchmark,
        }


# ============================================================
# ENGINE
# ============================================================

class EROSBlock94PortfolioStressScenarioEngine:
    """
    Deterministic, read-only portfolio stress/scenario authority.

    The engine keeps only certificate history internally. It never changes
    an upstream portfolio object. All input objects are deep-copied before
    normalization.
    """

    def __init__(self, *, engine_version: str = ENGINE_VERSION) -> None:
        self.engine_version = engine_version
        self._certificates: Dict[str, Dict[str, Any]] = {}
        self._scenario_index: Dict[str, str] = {}

    # --------------------------------------------------------
    # Public API: run_scenario
    # --------------------------------------------------------

    def run_scenario(
        self,
        *,
        valuation: Mapping[str, Any],
        performance: Mapping[str, Any],
        risk: Mapping[str, Any],
        positions: Sequence[Mapping[str, Any]],
        scenario: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """
        Run one scenario without certifying it.

        This method is deliberately pure from the caller's perspective.
        It returns a new dictionary and does not modify any input.
        """
        validation = self._validate_inputs(
            valuation=valuation,
            performance=performance,
            risk=risk,
            positions=positions,
            scenario=scenario,
        )

        if validation["status"] != STATUS_PASS:
            return validation

        normalized_scenario = self._normalize_scenario(scenario)
        exposures = self._normalize_positions(positions)

        result = self._calculate_scenario(
            valuation=valuation,
            performance=performance,
            risk=risk,
            exposures=exposures,
            scenario=normalized_scenario,
        )

        return {
            "status": STATUS_PASS,
            "block_id": BLOCK_ID,
            "engine_version": self.engine_version,
            "scenario": normalized_scenario.to_dict(),
            "result": result,
        }

    # --------------------------------------------------------
    # Public API: run_scenarios
    # --------------------------------------------------------

    def run_scenarios(
        self,
        *,
        valuation: Mapping[str, Any],
        performance: Mapping[str, Any],
        risk: Mapping[str, Any],
        positions: Sequence[Mapping[str, Any]],
        scenarios: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        """
        Run a collection of scenarios.

        Duplicate scenario IDs are retained as DUPLICATE records rather than
        silently overwritten.
        """
        if not isinstance(scenarios, Sequence) or isinstance(
            scenarios, (str, bytes)
        ):
            return self._blocked("INVALID_SCENARIO_COLLECTION")

        outputs: List[Dict[str, Any]] = []
        seen: set[str] = set()

        for scenario in scenarios:
            scenario_id = _text(
                _first(scenario, "scenario_id", "id", default="")
                if isinstance(scenario, Mapping)
                else ""
            )

            if scenario_id and scenario_id in seen:
                outputs.append(
                    {
                        "status": STATUS_DUPLICATE,
                        "scenario_id": scenario_id,
                    }
                )
                continue

            if scenario_id:
                seen.add(scenario_id)

            outputs.append(
                self.run_scenario(
                    valuation=valuation,
                    performance=performance,
                    risk=risk,
                    positions=positions,
                    scenario=scenario,
                )
            )

        return {
            "status": STATUS_PASS,
            "block_id": BLOCK_ID,
            "count": len(outputs),
            "results": outputs,
        }

    # --------------------------------------------------------
    # Public API: stress_portfolio
    # --------------------------------------------------------

    def stress_portfolio(
        self,
        *,
        valuation: Mapping[str, Any],
        performance: Mapping[str, Any],
        risk: Mapping[str, Any],
        positions: Sequence[Mapping[str, Any]],
        scenarios: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        """
        Calculate all supplied scenarios and return an analytical stress book.

        No certificate is persisted by this method.
        """
        batch = self.run_scenarios(
            valuation=valuation,
            performance=performance,
            risk=risk,
            positions=positions,
            scenarios=scenarios,
        )

        if batch["status"] != STATUS_PASS:
            return batch

        valid_results = [
            item
            for item in batch["results"]
            if item.get("status") == STATUS_PASS
        ]

        return {
            "status": STATUS_PASS,
            "block_id": BLOCK_ID,
            "scenario_count": len(batch["results"]),
            "successful_scenarios": len(valid_results),
            "blocked_scenarios": sum(
                1
                for item in batch["results"]
                if item.get("status") == STATUS_BLOCKED
            ),
            "duplicate_scenarios": sum(
                1
                for item in batch["results"]
                if item.get("status") == STATUS_DUPLICATE
            ),
            "results": _deepcopy(batch["results"]),
        }

    # --------------------------------------------------------
    # Public API: certify
    # --------------------------------------------------------

    def certify(
        self,
        *,
        valuation: Mapping[str, Any],
        performance: Mapping[str, Any],
        risk: Mapping[str, Any],
        positions: Sequence[Mapping[str, Any]],
        scenarios: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        """
        Create and persist a deterministic stress/scenario certificate.

        Certification is allowed only if:
            * upstream evidence is certified
            * lineage exists
            * scenarios are valid
            * at least one scenario succeeds
        """
        gate = self._validate_certification_inputs(
            valuation=valuation,
            performance=performance,
            risk=risk,
            positions=positions,
            scenarios=scenarios,
        )

        if gate["status"] != STATUS_PASS:
            return gate

        stress = self.stress_portfolio(
            valuation=valuation,
            performance=performance,
            risk=risk,
            positions=positions,
            scenarios=scenarios,
        )

        if stress["status"] != STATUS_PASS:
            return stress

        successful = [
            item for item in stress["results"]
            if item.get("status") == STATUS_PASS
        ]

        if not successful:
            return self._blocked("NO_VALID_SCENARIO_RESULT")

        # ----------------------------------------------------
        # Block 94 -> Block 95 certificate evidence adapter.
        #
        # Preserve the existing run_scenario() contract:
        #   item["result"][...]
        #
        # Expose the analytical stress evidence at the
        # certificate scenario-result boundary as required
        # by Block 95.
        # ----------------------------------------------------
        certificate_scenarios = []

        for item in successful:
            adapted = _deepcopy(item)
            result = adapted.get("result")

            if isinstance(result, Mapping):
                adapted["stressed_pnl"] = result.get("stressed_pnl")
                adapted["stressed_drawdown_pct"] = result.get(
                    "stressed_drawdown_pct"
                )
                adapted["scenario_contribution"] = _deepcopy(
                    result.get("scenario_contribution", {})
                )

            certificate_scenarios.append(adapted)

        valuation_id = self._valuation_id(valuation)
        performance_id = self._performance_id(performance)
        risk_certificate_id = self._risk_certificate_id(risk)

        certificate_payload = {
            "block_id": BLOCK_ID,
            "engine_version": self.engine_version,
            "valuation_id": valuation_id,
            "performance_id": performance_id,
            "risk_certificate_id": risk_certificate_id,
            "scenario_results": certificate_scenarios,
        }

        certificate_id = (
            f"{CERTIFICATE_PREFIX}-"
            f"{_hash_payload(certificate_payload)[:20]}"
        )

        if certificate_id in self._certificates:
            return {
                "status": STATUS_DUPLICATE,
                "certificate_status": STATUS_DUPLICATE,
                "certificate_id": certificate_id,
            }

        certificate = {
            "status": STATUS_CERTIFIED,
            "certificate_status": STATUS_CERTIFIED,
            "certificate_id": certificate_id,
            "block_id": BLOCK_ID,
            "engine_version": self.engine_version,
            "created_at": _now_iso(),
            "valuation_id": valuation_id,
            "performance_id": performance_id,
            "risk_certificate_id": risk_certificate_id,
            "scenario_count": len(certificate_scenarios),
            "scenario_results": _deepcopy(certificate_scenarios),
            "non_mutation_invariant": True,
            "broker_submission": False,
            "live_order_submission": False,
        }

        self._certificates[certificate_id] = _deepcopy(certificate)

        for item in successful:
            scenario_id = _text(
                item.get("scenario", {}).get("scenario_id", "")
            )
            if scenario_id:
                self._scenario_index[scenario_id] = certificate_id

        return _deepcopy(certificate)

    # --------------------------------------------------------
    # Public API: snapshot
    # --------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        """
        Return an immutable-style snapshot of Block 94's certificate store.

        The returned object is a deep copy and can therefore be modified by
        the caller without changing the engine.
        """
        return {
            "block_id": BLOCK_ID,
            "engine_version": self.engine_version,
            "certificate_count": len(self._certificates),
            "scenario_count": len(self._scenario_index),
            "certificates": _deepcopy(
                list(self._certificates.values())
            ),
        }

    # --------------------------------------------------------
    # Public API: certificate_history
    # --------------------------------------------------------

    def certificate_history(self) -> List[Dict[str, Any]]:
        return _deepcopy(list(self._certificates.values()))

    # --------------------------------------------------------
    # Public API: scenario_history
    # --------------------------------------------------------

    def scenario_history(self) -> Dict[str, str]:
        return _deepcopy(self._scenario_index)

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    def _validate_certification_inputs(
        self,
        *,
        valuation: Mapping[str, Any],
        performance: Mapping[str, Any],
        risk: Mapping[str, Any],
        positions: Sequence[Mapping[str, Any]],
        scenarios: Sequence[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        base = self._validate_inputs(
            valuation=valuation,
            performance=performance,
            risk=risk,
            positions=positions,
            scenario=None,
        )

        if base["status"] != STATUS_PASS:
            return base

        if not self._is_certified(valuation):
            return self._blocked("VALUATION_NOT_CERTIFIED")

        if not self._is_certified(performance):
            return self._blocked("PERFORMANCE_NOT_CERTIFIED")

        if not self._is_certified(risk):
            return self._blocked("RISK_NOT_CERTIFIED")

        if not self._valuation_id(valuation):
            return self._blocked("MISSING_VALUATION_LINEAGE")

        if not self._performance_id(performance):
            return self._blocked("MISSING_PERFORMANCE_LINEAGE")

        if not self._risk_certificate_id(risk):
            return self._blocked("MISSING_RISK_LINEAGE")

        if not scenarios:
            return self._blocked("MISSING_SCENARIOS")

        if _contains_forbidden_content(
            {
                "valuation": valuation,
                "performance": performance,
                "risk": risk,
                "positions": positions,
                "scenarios": scenarios,
            }
        ):
            return self._blocked("EXECUTION_CONTENT_FORBIDDEN")

        return {"status": STATUS_PASS}

    def _validate_inputs(
        self,
        *,
        valuation: Mapping[str, Any],
        performance: Mapping[str, Any],
        risk: Mapping[str, Any],
        positions: Sequence[Mapping[str, Any]],
        scenario: Optional[Mapping[str, Any]],
    ) -> Dict[str, Any]:
        for name, payload in (
            ("valuation", valuation),
            ("performance", performance),
            ("risk", risk),
        ):
            if not isinstance(payload, Mapping):
                return self._blocked(f"MALFORMED_{name.upper()}")

        if not isinstance(positions, Sequence) or isinstance(
            positions, (str, bytes)
        ):
            return self._blocked("MALFORMED_POSITIONS")

        if not positions:
            return self._blocked("EMPTY_POSITIONS")

        if _contains_forbidden_content(
            {
                "valuation": valuation,
                "performance": performance,
                "risk": risk,
                "positions": positions,
                "scenario": scenario,
            }
        ):
            return self._blocked("EXECUTION_CONTENT_FORBIDDEN")

        if scenario is not None:
            if not isinstance(scenario, Mapping):
                return self._blocked("MALFORMED_SCENARIO")

            normalized = self._normalize_scenario_safe(scenario)

            if normalized is None:
                return self._blocked("INVALID_SCENARIO")

        return {"status": STATUS_PASS}

    # --------------------------------------------------------
    # Normalization
    # --------------------------------------------------------

    def _normalize_scenario_safe(
        self,
        scenario: Mapping[str, Any],
    ) -> Optional[ScenarioDefinition]:
        try:
            normalized = self._normalize_scenario(scenario)
        except (TypeError, ValueError):
            return None

        if not normalized.scenario_id:
            return None

        if normalized.scenario_type not in ALLOWED_SCENARIO_TYPES:
            return None

        if not normalized.name:
            return None

        shock_fields = (
            normalized.price_shock_pct,
            normalized.market_shock_pct,
            normalized.volatility_shock_pct,
            normalized.benchmark_shock_pct,
            normalized.sector_shock_pct,
            normalized.liquidity_shock_pct,
            normalized.correlation_shock_pct,
            normalized.default_shock_pct,
        )

        if any(abs(value) > 100 for value in shock_fields):
            return None

        return normalized

    def _normalize_scenario(
        self,
        scenario: Mapping[str, Any],
    ) -> ScenarioDefinition:
        return ScenarioDefinition(
            scenario_id=_text(
                _first(scenario, "scenario_id", "id", default="")
            ),
            scenario_type=_text(
                _first(
                    scenario,
                    "scenario_type",
                    "type",
                    default="",
                )
            ).upper(),
            name=_text(
                _first(
                    scenario,
                    "name",
                    "scenario_name",
                    default="",
                )
            ),
            description=_text(
                _first(scenario, "description", default="")
            ),
            price_shock_pct=_float(
                _first(scenario, "price_shock_pct", default=0.0),
                0.0,
            ),
            market_shock_pct=_float(
                _first(scenario, "market_shock_pct", default=0.0),
                0.0,
            ),
            volatility_shock_pct=_float(
                _first(scenario, "volatility_shock_pct", default=0.0),
                0.0,
            ),
            benchmark_shock_pct=_float(
                _first(scenario, "benchmark_shock_pct", default=0.0),
                0.0,
            ),
            sector_shock_pct=_float(
                _first(scenario, "sector_shock_pct", default=0.0),
                0.0,
            ),
            liquidity_shock_pct=_float(
                _first(scenario, "liquidity_shock_pct", default=0.0),
                0.0,
            ),
            correlation_shock_pct=_float(
                _first(scenario, "correlation_shock_pct", default=0.0),
                0.0,
            ),
            default_shock_pct=_float(
                _first(scenario, "default_shock_pct", default=0.0),
                0.0,
            ),
            sector=_text(
                _first(scenario, "sector", default="")
            ),
            benchmark=_text(
                _first(scenario, "benchmark", default="")
            ),
            metadata=_deepcopy(
                dict(
                    _first(scenario, "metadata", default={})
                    or {}
                )
            ),
        ).normalized()

    def _normalize_positions(
        self,
        positions: Sequence[Mapping[str, Any]],
    ) -> List[PositionExposure]:
        normalized: List[PositionExposure] = []

        for position in positions:
            if not isinstance(position, Mapping):
                raise ValueError("malformed position")

            quantity = _number(
                _first(position, "quantity", "qty", default=0)
            )
            price = _number(
                _first(position, "price", "current_price", default=0)
            )

            market_value = _float(
                _first(
                    position,
                    "market_value",
                    "value",
                    default=quantity * price,
                )
            )

            if market_value is None:
                raise ValueError("invalid market value")

            normalized.append(
                PositionExposure(
                    symbol=_text(
                        _first(
                            position,
                            "symbol",
                            "ticker",
                            default="",
                        )
                    ),
                    quantity=quantity,
                    price=price,
                    market_value=market_value,
                    sector=_text(
                        _first(position, "sector", default="")
                    ),
                    beta=_float(
                        _first(position, "beta", default=1.0),
                        1.0,
                    ) or 1.0,
                    volatility=_float(
                        _first(position, "volatility", default=0.0),
                        0.0,
                    ) or 0.0,
                    liquidity_factor=_float(
                        _first(
                            position,
                            "liquidity_factor",
                            default=1.0,
                        ),
                        1.0,
                    ) or 1.0,
                    benchmark=_text(
                        _first(position, "benchmark", default="")
                    ),
                )
            )

        if not normalized:
            raise ValueError("empty positions")

        return normalized

    # --------------------------------------------------------
    # Scenario calculations
    # --------------------------------------------------------

    def _calculate_scenario(
        self,
        *,
        valuation: Mapping[str, Any],
        performance: Mapping[str, Any],
        risk: Mapping[str, Any],
        exposures: Sequence[PositionExposure],
        scenario: ScenarioDefinition,
    ) -> Dict[str, Any]:
        base_equity = self._base_equity(valuation, exposures)

        position_results: List[Dict[str, Any]] = []

        for exposure in exposures:
            shock_pct = self._effective_shock(
                exposure=exposure,
                scenario=scenario,
                portfolio_beta=self._portfolio_beta(
                    risk=risk,
                    exposures=exposures,
                ),
            )

            stressed_value = exposure.market_value * (
                1.0 + shock_pct / 100.0
            )

            pnl = stressed_value - exposure.market_value

            position_results.append(
                {
                    "symbol": exposure.symbol,
                    "base_market_value": exposure.market_value,
                    "effective_shock_pct": shock_pct,
                    "stressed_market_value": stressed_value,
                    "stressed_pnl": pnl,
                    "contribution_pct": 0.0,
                }
            )

        total_stressed_value = sum(
            item["stressed_market_value"]
            for item in position_results
        )

        total_pnl = total_stressed_value - sum(
            item["base_market_value"]
            for item in position_results
        )

        if total_pnl != 0:
            for item in position_results:
                item["contribution_pct"] = (
                    item["stressed_pnl"] / total_pnl * 100.0
                )

        stressed_equity = base_equity + total_pnl

        drawdown_pct = (
            abs(min(total_pnl, 0.0)) / base_equity * 100.0
            if base_equity > 0
            else 0.0
        )

        return {
            "base_equity": base_equity,
            "base_market_value": sum(
                item["base_market_value"]
                for item in position_results
            ),
            "stressed_market_value": total_stressed_value,
            "stressed_equity": stressed_equity,
            "stressed_pnl": total_pnl,
            "stressed_return_pct": (
                total_pnl / base_equity * 100.0
                if base_equity > 0
                else 0.0
            ),
            "stressed_drawdown_pct": drawdown_pct,
            "scenario_contribution": _deepcopy(position_results),
            "risk_context": {
                "volatility": _float(
                    _first(
                        risk,
                        "volatility",
                        "portfolio_volatility",
                        default=0.0,
                    ),
                    0.0,
                ),
                "maximum_drawdown": _float(
                    _first(
                        risk,
                        "maximum_drawdown",
                        "max_drawdown",
                        default=0.0,
                    ),
                    0.0,
                ),
                "beta": self._portfolio_beta(
                    risk=risk,
                    exposures=exposures,
                ),
            },
            "performance_context": {
                "return_pct": _float(
                    _first(
                        performance,
                        "return_pct",
                        "portfolio_return_pct",
                        default=0.0,
                    ),
                    0.0,
                ),
            },
        }

    def _effective_shock(
        self,
        *,
        exposure: PositionExposure,
        scenario: ScenarioDefinition,
        portfolio_beta: float,
    ) -> float:
        shock = scenario.default_shock_pct

        shock += scenario.price_shock_pct

        if scenario.market_shock_pct:
            shock += scenario.market_shock_pct * max(
                abs(exposure.beta),
                0.0,
            )

        if scenario.volatility_shock_pct:
            shock += (
                scenario.volatility_shock_pct
                * max(exposure.volatility, 0.0)
            )

        if scenario.benchmark_shock_pct:
            if (
                scenario.benchmark
                and exposure.benchmark
                and scenario.benchmark == exposure.benchmark
            ):
                shock += scenario.benchmark_shock_pct

        if scenario.sector_shock_pct:
            if (
                scenario.sector
                and exposure.sector
                and scenario.sector == exposure.sector
            ):
                shock += scenario.sector_shock_pct

        if scenario.liquidity_shock_pct:
            liquidity_multiplier = max(
                min(exposure.liquidity_factor, 1.0),
                0.0,
            )
            shock += (
                scenario.liquidity_shock_pct
                * (1.0 - liquidity_multiplier)
            )

        if scenario.correlation_shock_pct:
            shock += (
                scenario.correlation_shock_pct
                * max(abs(portfolio_beta) - 1.0, 0.0)
            )

        return shock

    # --------------------------------------------------------
    # Lineage helpers
    # --------------------------------------------------------

    @staticmethod
    def _is_certified(payload: Mapping[str, Any]) -> bool:
        status = _text(
            _first(
                payload,
                "status",
                "certificate_status",
                "certified_status",
                default="",
            )
        ).upper()

        return status in {
            STATUS_CERTIFIED,
            "PASS",
            "CERTIFIED",
        }

    @staticmethod
    def _valuation_id(payload: Mapping[str, Any]) -> str:
        return _text(
            _first(
                payload,
                "valuation_id",
                "valuation_record_id",
                default="",
            )
        )

    @staticmethod
    def _performance_id(payload: Mapping[str, Any]) -> str:
        return _text(
            _first(
                payload,
                "performance_id",
                "performance_record_id",
                default="",
            )
        )

    @staticmethod
    def _risk_certificate_id(payload: Mapping[str, Any]) -> str:
        return _text(
            _first(
                payload,
                "certificate_id",
                "risk_certificate_id",
                default="",
            )
        )

    @staticmethod
    def _base_equity(
        valuation: Mapping[str, Any],
        exposures: Sequence[PositionExposure],
    ) -> float:
        value = _float(
            _first(
                valuation,
                "portfolio_equity",
                "equity",
                "total_equity",
                default=None,
            )
        )

        if value is not None and value > 0:
            return value

        return sum(
            max(exposure.market_value, 0.0)
            for exposure in exposures
        )

    @staticmethod
    def _portfolio_beta(
        *,
        risk: Mapping[str, Any],
        exposures: Sequence[PositionExposure],
    ) -> float:
        supplied = _float(
            _first(
                risk,
                "beta",
                "portfolio_beta",
                default=None,
            )
        )

        if supplied is not None:
            return supplied

        denominator = sum(
            abs(exposure.market_value)
            for exposure in exposures
        )

        if denominator == 0:
            return 1.0

        return sum(
            abs(exposure.market_value) * exposure.beta
            for exposure in exposures
        ) / denominator

    # --------------------------------------------------------
    # Common response
    # --------------------------------------------------------

    @staticmethod
    def _blocked(reason: str) -> Dict[str, Any]:
        return {
            "status": STATUS_BLOCKED,
            "block_id": BLOCK_ID,
            "reason": reason,
            "broker_submission": False,
            "live_order_submission": False,
            "portfolio_mutation": False,
            "valuation_mutation": False,
        }


# ============================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# ============================================================

def run_scenario(
    *,
    valuation: Mapping[str, Any],
    performance: Mapping[str, Any],
    risk: Mapping[str, Any],
    positions: Sequence[Mapping[str, Any]],
    scenario: Mapping[str, Any],
) -> Dict[str, Any]:
    engine = EROSBlock94PortfolioStressScenarioEngine()
    return engine.run_scenario(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenario=scenario,
    )


def certify_stress(
    *,
    valuation: Mapping[str, Any],
    performance: Mapping[str, Any],
    risk: Mapping[str, Any],
    positions: Sequence[Mapping[str, Any]],
    scenarios: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    engine = EROSBlock94PortfolioStressScenarioEngine()
    return engine.certify(
        valuation=valuation,
        performance=performance,
        risk=risk,
        positions=positions,
        scenarios=scenarios,
    )


__all__ = [
    "BLOCK_ID",
    "ENGINE_VERSION",
    "STATUS_PASS",
    "STATUS_BLOCKED",
    "STATUS_DUPLICATE",
    "STATUS_CERTIFIED",
    "ScenarioDefinition",
    "PositionExposure",
    "EROSBlock94PortfolioStressScenarioEngine",
    "run_scenario",
    "certify_stress",
]


