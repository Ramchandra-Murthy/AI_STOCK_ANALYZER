"""
EROS 3.0 Decision Pipeline.

Orchestration only.

Existing business mathematics remains owned by canonical
financial, valuation, scoring, and decision engines.
"""

from dataclasses import dataclass, field
from typing import Any

from eros.data import prepare_raw_data
from eros.normalization import normalize
from eros.scoring import fundamental_score, risk_score


# =========================================================
# PIPELINE CONTEXT
# =========================================================

@dataclass
class PipelineContext:
    """Mutable execution context for the EROS decision pipeline."""

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


# =========================================================
# CONTEXT CREATION
# =========================================================

def create_context(symbol: str) -> PipelineContext:
    """Create a normalized EROS pipeline context."""

    prepared = prepare_raw_data(symbol)

    return PipelineContext(
        symbol=prepared["symbol"],
        raw_data=prepared,
    )


# =========================================================
# GENERIC CONTEXT HELPERS
# =========================================================

def attach(
    context: PipelineContext,
    name: str,
    value: Any,
):
    """Attach a value to the pipeline context."""

    setattr(context, name, value)

    return context


def add_warning(
    context: PipelineContext,
    message: str,
):
    """Append a warning to the pipeline context."""

    if message:
        context.warnings.append(str(message))


def add_evidence(
    context: PipelineContext,
    evidence: Any,
):
    """Append non-null evidence to the pipeline context."""

    if evidence is not None:
        context.evidence.append(evidence)


# =========================================================
# FOUNDATION
# =========================================================

def run_foundation(
    context: PipelineContext,
    raw_data: Any = None,
):
    """
    Execute the EROS foundation stage.

    Flow:

        raw input
            ->
        normalization
            ->
        fundamental scoring
            ->
        risk scoring

    No valuation mathematics is performed here.
    """

    # -----------------------------------------------------
    # Accept new raw data when supplied
    # -----------------------------------------------------

    if raw_data is not None:
        context.raw_data = prepare_raw_data(
            context.symbol,
            raw_data,
        )

    # -----------------------------------------------------
    # Extract payload
    # -----------------------------------------------------

    payload = context.raw_data.get("data")

    if not payload:
        add_warning(
            context,
            "No financial payload supplied; foundation execution skipped.",
        )

        context.status = "INPUT_REQUIRED"

        return context

    # -----------------------------------------------------
    # Normalization
    # -----------------------------------------------------

    try:
        context.financials = normalize(payload)
        context.normalized = context.financials

    except Exception as exc:
        add_warning(
            context,
            f"Normalization failed: "
            f"{type(exc).__name__}: {exc}",
        )

        context.status = "NORMALIZATION_FAILED"

        return context

    # -----------------------------------------------------
    # Fundamental score
    # -----------------------------------------------------

    try:
        context.score = fundamental_score(
            context.financials
        )

    except Exception as exc:
        add_warning(
            context,
            f"Fundamental scoring failed: "
            f"{type(exc).__name__}: {exc}",
        )

    # -----------------------------------------------------
    # Risk score
    # -----------------------------------------------------

    try:
        context.risk = risk_score(
            context.financials
        )

    except Exception as exc:
        add_warning(
            context,
            f"Risk scoring failed: "
            f"{type(exc).__name__}: {exc}",
        )

    # -----------------------------------------------------
    # Foundation complete
    # -----------------------------------------------------

    context.status = "FOUNDATION_COMPLETE"

    return context


# =========================================================
# VALUATION
# =========================================================

def run_valuation(
    context: PipelineContext,
):
    """
    Execute the EROS valuation stage.

    Foundation FinancialStatements are converted into the
    canonical DCF/SOTP valuation payload.

    No valuation mathematics is performed directly here.
    """

    from eros.valuation.adapter import (
        evaluate_valuation,
        valuation_available,
    )
    from eros.valuation.bridge import build_bridge
    from services.financials.builders import build_dcf_input

    # -----------------------------------------------------
    # PRE-FOUNDATION SAFETY
    # -----------------------------------------------------

    if context.financials is None:
        add_warning(
            context,
            "Valuation requires foundation data.",
        )

        # Preserve the safe upstream state.
        # Missing input is not a valuation execution failure.
        if context.status == "INPUT_REQUIRED":
            return context

        context.status = "VALUATION_FAILED"
        return context

    # -----------------------------------------------------
    # BUILD CANONICAL VALUATION PAYLOAD
    # -----------------------------------------------------

    try:
        dcf_input = build_dcf_input(
            context.financials
        )

        valuation_data = {
            # -------------------------------------------------
            # COMPANY
            # -------------------------------------------------

            "company_name": dcf_input.company_name,
            "currency": dcf_input.currency,
            "shares_outstanding": (
                dcf_input.shares_outstanding
            ),

            # -------------------------------------------------
            # HISTORICAL / FORECAST OPERATING DRIVERS
            # -------------------------------------------------

            "last_historical_revenue": (
                dcf_input.last_historical_revenue
            ),
            "revenue_growth_rates": (
                dcf_input.revenue_growth_rates
            ),
            "ebit_margin_forecast": (
                dcf_input.ebit_margin_forecast
            ),
            "capex_pct_rev": (
                dcf_input.capex_pct_rev
            ),
            "nwc_pct_rev": (
                dcf_input.nwc_pct_rev
            ),
            "dna_pct_rev": (
                dcf_input.dna_pct_rev
            ),

            # -------------------------------------------------
            # DCF ASSUMPTIONS
            # -------------------------------------------------

            "tax_rate": dcf_input.tax_rate,
            "cost_of_equity": (
                dcf_input.cost_of_equity
            ),
            "cost_of_debt_post_tax": (
                dcf_input.cost_of_debt_post_tax
            ),
            "equity_weight": (
                dcf_input.equity_weight
            ),
            "debt_weight": (
                dcf_input.debt_weight
            ),
            "terminal_growth_rate": (
                dcf_input.terminal_growth_rate
            ),

            # -------------------------------------------------
            # EQUITY BRIDGE
            # -------------------------------------------------

            "total_debt": dcf_input.total_debt,
            "cash_and_equivalents": (
                dcf_input.cash_and_equivalents
            ),
            "minority_interest": (
                dcf_input.minority_interest
            ),
            "preferred_stock": (
                dcf_input.preferred_stock
            ),

            # -------------------------------------------------
            # SOTP
            # -------------------------------------------------

            "dcf_segments": [
                {
                    "segment_name": (
                        dcf_input.company_name
                    ),
                    "currency": (
                        dcf_input.currency
                    ),
                    "last_historical_revenue": (
                        dcf_input.last_historical_revenue
                    ),
                    "revenue_growth_rates": (
                        dcf_input.revenue_growth_rates
                    ),
                    "ebit_margin_forecast": (
                        dcf_input.ebit_margin_forecast
                    ),
                    "capex_pct_rev": (
                        dcf_input.capex_pct_rev
                    ),
                    "nwc_pct_rev": (
                        dcf_input.nwc_pct_rev
                    ),
                    "dna_pct_rev": (
                        dcf_input.dna_pct_rev
                    ),
                    "tax_rate": (
                        dcf_input.tax_rate
                    ),
                    "cost_of_equity": (
                        dcf_input.cost_of_equity
                    ),
                    "cost_of_debt_post_tax": (
                        dcf_input.cost_of_debt_post_tax
                    ),
                    "equity_weight": (
                        dcf_input.equity_weight
                    ),
                    "debt_weight": (
                        dcf_input.debt_weight
                    ),
                    "terminal_growth_rate": (
                        dcf_input.terminal_growth_rate
                    ),
                    "total_debt": (
                        dcf_input.total_debt
                    ),
                    "cash_and_equivalents": (
                        dcf_input.cash_and_equivalents
                    ),
                    "shares_outstanding": (
                        dcf_input.shares_outstanding
                    ),
                    "weight": 1.0,
                }
            ],

            "other_segments": [],
            "holdco_discount": 0.0,
        }

    except Exception as exc:
        add_warning(
            context,
            "Valuation payload construction failed: "
            f"{type(exc).__name__}: {exc}",
        )
        context.status = "VALUATION_FAILED"
        return context

    # -----------------------------------------------------
    # INPUT AVAILABILITY GATE
    # -----------------------------------------------------

    if not valuation_available(valuation_data):
        context.status = "INPUT_REQUIRED"

        context.sotp = None
        context.dcf = None
        context.valuation_bridge = None

        add_warning(
            context,
            "Valuation input is required.",
        )

        return context

    # -----------------------------------------------------
    # EXECUTE CANONICAL VALUATION ADAPTER
    # -----------------------------------------------------

    try:
        result = evaluate_valuation(
            valuation_data,
            provenance={
                "orchestrator": "EROS_3.0",
                "symbol": context.symbol,
                "source": "foundation",
            },
        )

        # -------------------------------------------------
        # ADAPTER CONTRACT
        # -------------------------------------------------

        if not isinstance(result, dict):
            raise TypeError(
                "evaluate_valuation() must return a dict"
            )

        # -------------------------------------------------
        # EXTRACT COMPONENTS
        # -------------------------------------------------

        sotp = result.get("sotp")
        dcf = result.get("dcf")

        provenance = result.get(
            "provenance",
            {},
        )

        warnings = result.get(
            "warnings",
            [],
        )

        # -------------------------------------------------
        # BUILD EXECUTABLE VALUATION BOUNDARY
        # -------------------------------------------------

        context.valuation_bridge = build_bridge(
            sotp=sotp,
            dcf=dcf,
            provenance=provenance,
        )

        # -------------------------------------------------
        # KEEP DIRECT CONTEXT REFERENCES IN SYNC
        # -------------------------------------------------

        context.sotp = sotp
        context.dcf = dcf

        # -------------------------------------------------
        # PRESERVE WARNINGS
        # -------------------------------------------------

        if warnings:
            context.warnings.extend(
                warnings
            )

        # -------------------------------------------------
        # PIPELINE STATUS
        # -------------------------------------------------

        status = result.get("status")

        if status in (
            "COMPLETE",
            "EXECUTED",
        ):
            context.status = (
                "VALUATION_COMPLETE"
            )

        elif status == "INPUT_REQUIRED":
            context.status = (
                "FOUNDATION_COMPLETE"
            )

            add_warning(
                context,
                "Valuation input is incomplete.",
            )

        else:
            context.status = (
                "VALUATION_FAILED"
            )

        return context

    # -----------------------------------------------------
    # ERROR HANDLING
    # -----------------------------------------------------

    except Exception as exc:
        add_warning(
            context,
            "Valuation execution failed: "
            f"{type(exc).__name__}: {exc}",
        )

        context.sotp = None
        context.dcf = None

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

        context.status = (
            "VALUATION_FAILED"
        )

        return context


# =========================================================
# STAGE 13C
# =========================================================

def run_stage13c(
    context: PipelineContext,
):
    """
    Execute the Stage 13C decision classification stage.

    Stage 13C performs decision classification only.
    It does not perform valuation mathematics.
    """

    # -----------------------------------------------------
    # Pre-foundation safety
    # -----------------------------------------------------

    if context.financials is None:

        add_warning(
            context,
            "Stage 13C requires foundation data.",
        )

        return context

    # -----------------------------------------------------
    # Evidence requirement
    # -----------------------------------------------------

    records = context.evidence

    if not records:

        context.stage13c = {
            "status": "INPUT_REQUIRED",
            "stage": "13C.2",
            "entity_count": 0,
            "complete_count": 0,
            "partial_count": 0,
            "conflicting_count": 0,
            "unresolved_count": 0,
            "classification_complete": False,
            "bridge_ready": False,
            "separate_sotp_value_authorized": False,
            "records": [],
        }

        context.classification = None

        add_warning(
            context,
            "Stage 13C evidence is required.",
        )

        return context

    # -----------------------------------------------------
    # Execute Stage 13C.2
    # -----------------------------------------------------

    try:

        from eros.decision.stage13c.classification import (
            audit_classification_records,
        )

        audit = audit_classification_records(
            records
        )

        context.stage13c = audit

        classified_records = audit.get(
            "records",
            [],
        )

        context.classification = (
            classified_records
        )

        if audit.get(
            "classification_complete"
        ):
            context.status = (
                "DECISION_COMPLETE"
            )
        else:
            context.status = (
                "DECISION_INPUT_REQUIRED"
            )

        return context

    except Exception as exc:

        add_warning(
            context,
            "Stage 13C execution failed: "
            f"{type(exc).__name__}: {exc}",
        )

        context.stage13c = {
            "status": "ERROR",
            "stage": "13C.2",
            "classification_complete": False,
            "bridge_ready": False,
            "separate_sotp_value_authorized": False,
            "records": [],
        }

        context.classification = None

        return context


# =========================================================
# FINALIZE
# =========================================================

def finalize(
    context: PipelineContext,
):
    """
    Convert PipelineContext into the public EROS result.
    """

    if context.status == "INITIALIZED":

        context.status = (
            "INPUT_REQUIRED"
        )

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

        "classification": (
            context.classification
        ),

        "sotp": context.sotp,

        "dcf": context.dcf,

        "valuation_bridge": (
            context.valuation_bridge
        ),

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


# =========================================================
# PUBLIC EXPORTS
# =========================================================

__all__ = [
    "PipelineContext",
    "create_context",
    "attach",
    "add_warning",
    "add_evidence",
    "run_foundation",
    "run_valuation",
    "run_stage13c",
    "finalize",
]