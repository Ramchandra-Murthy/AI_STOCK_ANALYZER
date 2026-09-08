"""
EROS 3.0 Decision Pipeline.

Orchestration only.
Existing business mathematics remains owned by canonical engines.
"""

from dataclasses import dataclass, field
from typing import Any

from eros.data import prepare_raw_data
from eros.normalization import normalize
from eros.scoring import fundamental_score, risk_score
from eros.valuation.adapter import evaluate_valuation
from eros.valuation.bridge import build_bridge
@dataclass
class PipelineContext:
    symbol: str

    raw_data: Any = None
    financials: Any = None
    normalized: Any = None

    quality: Any = None
    score: Any = None
    risk: Any = None
    classification: Any = None

    sotp: Any = None
    dcf: Any = None
    valuation_bridge: Any = None

    stage13c: Any = None
    stage14: Any = None

    evidence: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    status: str = "INITIALIZED"


def create_context(symbol: str) -> PipelineContext:
    prepared = prepare_raw_data(symbol)

    return PipelineContext(
        symbol=prepared["symbol"],
        raw_data=prepared,
    )


def attach(context: PipelineContext, name: str, value: Any):
    setattr(context, name, value)
    return context


def add_warning(context: PipelineContext, message: str):
    if message:
        context.warnings.append(str(message))


def add_evidence(context: PipelineContext, evidence: Any):
    if evidence is not None:
        context.evidence.append(evidence)


def run_foundation(
    context: PipelineContext,
    raw_data: Any = None,
):
    if raw_data is not None:
        context.raw_data = prepare_raw_data(
            context.symbol,
            raw_data,
        )

    payload = context.raw_data.get("data")

    if not payload:
        add_warning(
            context,
            "No financial payload supplied; foundation execution skipped.",
        )
        context.status = "INPUT_REQUIRED"
        return context

    try:
        context.financials = normalize(payload)
        context.normalized = context.financials
    except Exception as exc:
        add_warning(
            context,
            f"Normalization failed: {type(exc).__name__}: {exc}",
        )
        context.status = "NORMALIZATION_FAILED"
        return context

    try:
        context.score = fundamental_score(context.financials)
    except Exception as exc:
        add_warning(
            context,
            f"Fundamental scoring failed: {type(exc).__name__}: {exc}",
        )

    try:
        context.risk = risk_score(context.financials)
    except Exception as exc:
        add_warning(
            context,
            f"Risk scoring failed: {type(exc).__name__}: {exc}",
        )

    context.status = "FOUNDATION_COMPLETE"
    return context


def run_valuation(context):
    """
    Execute the EROS valuation stage.

    Public valuation execution returns the canonical result dictionary.
    PipelineContext, however, retains the executable ValuationBoundary
    object so downstream stages can independently access SOTP and DCF.

    No valuation mathematics is performed here.
    """

    from eros.valuation.adapter import evaluate_valuation
    from eros.valuation.bridge import build_bridge

    # --------------------------------------------------------
    # Pre-foundation safety
    # --------------------------------------------------------

    if context.raw_data is None:
        context.valuation_bridge = build_bridge(
            sotp=None,
            dcf=None,
            provenance={
                "orchestrator": "EROS_3.0",
                "symbol": context.symbol,
                "valuation_status": "INPUT_REQUIRED",
            },
        )

        if hasattr(context, "warnings"):
            context.warnings.append(
                "Valuation requires foundation data."
            )

        return context

    # --------------------------------------------------------
    # Execute canonical valuation adapter
    # --------------------------------------------------------

    try:
        result = evaluate_valuation(
            context.raw_data,
            provenance={
                "orchestrator": "EROS_3.0",
                "symbol": context.symbol,
            },
        )

        # ----------------------------------------------------
        # IMPORTANT:
        # evaluate_valuation() intentionally returns a dict.
        # The pipeline stores the boundary object internally.
        # ----------------------------------------------------

        context.valuation_bridge = build_bridge(
            sotp=result.get("sotp"),
            dcf=result.get("dcf"),
            provenance=result.get("provenance", {}),
        )

        # Preserve valuation warnings at pipeline level.
        warnings = result.get("warnings", [])

        if warnings and hasattr(context, "warnings"):
            context.warnings.extend(warnings)

        # Do not overwrite a valid foundation state merely
        # because valuation inputs are incomplete.
        if result.get("status") == "EXECUTED":
            context.status = "VALUATION_COMPLETE"
        elif result.get("status") == "INPUT_REQUIRED":
            if hasattr(context, "warnings"):
                context.warnings.append(
                    "Valuation input is incomplete."
                )

        return context

    except Exception as exc:

        if hasattr(context, "warnings"):
            context.warnings.append(
                f"Valuation execution failed: "
                f"{type(exc).__name__}: {exc}"
            )

        context.valuation_bridge = build_bridge(
            sotp=None,
            dcf=None,
            provenance={
                "orchestrator": "EROS_3.0",
                "symbol": context.symbol,
                "valuation_status": "ERROR",
                "error_type": type(exc).__name__,
            },
        )

        return context

def finalize(context: PipelineContext):
    if context.status == "INITIALIZED":
        context.status = "INPUT_REQUIRED"
        add_warning(
            context,
            "Pipeline was finalized before foundation execution.",
        )

    return {
        "symbol": context.symbol,
        "status": context.status,

        "raw_data": context.raw_data,
        "financials": context.financials,
        "normalized": context.normalized,

        "quality": context.quality,
        "score": context.score,
        "risk": context.risk,
        "classification": context.classification,

        "sotp": context.sotp,
        "dcf": context.dcf,
        "valuation_bridge": context.valuation_bridge,

        "stage13c": context.stage13c,
        "stage14": context.stage14,

        "evidence": context.evidence,
        "warnings": context.warnings,

        "provenance": {
            "orchestrator": "EROS_3.0",
            "pipeline_status": context.status,
            "symbol": context.symbol,
        },
    }


__all__ = [
    "PipelineContext",
    "create_context",
    "attach",
    "add_warning",
    "add_evidence",
    "run_foundation",
    "run_valuation",
    "finalize",
]

