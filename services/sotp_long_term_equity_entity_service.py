from __future__ import annotations

from typing import Any, Dict, List

from services.sotp_long_term_equity_overlap_service import (
    evaluate_long_term_equity_overlap,
)

# ==========================================================
# ENTITY CLASSIFICATION POLICY
# ==========================================================
#
# An entity may ultimately be classified as:
#
# OPERATING_OVERLAP
#     Economics already represented by an operating segment EV.
#
# INCREMENTAL_INVESTMENT
#     Investment is economically separate from operating SOTP.
#
# COMPONENT_ONLY
#     Accounting component; never add separately.
#
# UNRESOLVED
#     Evidence is insufficient.
#
# IMPORTANT:
# No entity becomes bridge-ready merely because it appears
# in an associate/JV disclosure.
# ==========================================================


def _num(value: Any):
    try:
        if value is None:
            return None

        value = float(value)

        if value != value:
            return None

        return value

    except (TypeError, ValueError):
        return None


def classify_long_term_equity_entities(
    symbol: str,
) -> Dict[str, Any]:

    base_symbol = str(symbol).upper().replace(".NS", "").strip()

    overlap = evaluate_long_term_equity_overlap(base_symbol)

    if not isinstance(overlap, dict) or overlap.get("status") != "OK":
        return {
            "status": "UNAVAILABLE",
            "symbol": base_symbol,
            "message": "Long-term equity overlap analysis is unavailable.",
            "source": overlap,
        }

    reported_value = _num(overlap.get("reported_long_term_equity_investment"))

    components = overlap.get("components", {})

    if not isinstance(components, dict):
        components = {}

    joint_venture_value = _num(components.get("joint_venture_investments"))

    associate_value = _num(components.get("associate_investments"))

    # ------------------------------------------------------
    # ENTITY-LEVEL DATA
    # ------------------------------------------------------
    #
    # We deliberately do NOT invent entity-level allocations
    # from aggregate accounting balances.
    #
    # The next evidence layer must populate this list from
    # authoritative entity-level disclosures.
    # ------------------------------------------------------

    entities: List[Dict[str, Any]] = []

    entity_level_holdings_available = len(entities) > 0

    # ------------------------------------------------------
    # CLASSIFICATION SUMMARY
    # ------------------------------------------------------

    operating_overlap_value = 0.0
    incremental_investment_value = 0.0
    unresolved_entity_value = 0.0

    operating_overlap_count = 0
    incremental_investment_count = 0
    unresolved_entity_count = 0

    for entity in entities:

        classification = entity.get("classification")
        value = _num(entity.get("value"))

        if classification == "OPERATING_OVERLAP":

            operating_overlap_count += 1

            if value is not None:
                operating_overlap_value += value

        elif classification == "INCREMENTAL_INVESTMENT":

            incremental_investment_count += 1

            if value is not None:
                incremental_investment_value += value

        else:

            unresolved_entity_count += 1

            if value is not None:
                unresolved_entity_value += value

    # ------------------------------------------------------
    # AUTHORIZATION TESTS
    # ------------------------------------------------------

    ownership_structure_confirmed = False
    operating_segment_overlap_resolved = False
    valuation_basis_confirmed = False

    classification_complete = (
        entity_level_holdings_available
        and ownership_structure_confirmed
        and operating_segment_overlap_resolved
    )

    bridge_ready = (
        classification_complete
        and valuation_basis_confirmed
        and unresolved_entity_count == 0
    )

    unresolved_tests = []

    if not entity_level_holdings_available:
        unresolved_tests.append("ENTITY_LEVEL_HOLDINGS")

    if not ownership_structure_confirmed:
        unresolved_tests.append("OWNERSHIP_STRUCTURE")

    if not operating_segment_overlap_resolved:
        unresolved_tests.append("OPERATING_SEGMENT_OVERLAP")

    if not valuation_basis_confirmed:
        unresolved_tests.append("VALUATION_BASIS")

    return {
        "status": "OK",
        "version": "V5.0",
        "symbol": base_symbol,
        "currency": overlap.get("currency", "INR"),
        "unit": overlap.get("unit", "crore"),
        "period": overlap.get("period"),
        "reported_long_term_equity_investment": reported_value,
        "accounting_components": {
            "joint_venture_investments": joint_venture_value,
            "associate_investments": associate_value,
            "component_total": _num(components.get("component_total")),
        },
        "entity_level_holdings_available": (entity_level_holdings_available),
        "entities": entities,
        "classification_summary": {
            "operating_overlap_count": operating_overlap_count,
            "operating_overlap_value": round(operating_overlap_value, 2),
            "incremental_investment_count": (incremental_investment_count),
            "incremental_investment_value": round(incremental_investment_value, 2),
            "unresolved_entity_count": unresolved_entity_count,
            "unresolved_entity_value": round(unresolved_entity_value, 2),
        },
        "authorization_tests": {
            "entity_level_holdings_available": (entity_level_holdings_available),
            "ownership_structure_confirmed": (ownership_structure_confirmed),
            "operating_segment_overlap_resolved": (operating_segment_overlap_resolved),
            "valuation_basis_confirmed": (valuation_basis_confirmed),
        },
        "classification_complete": classification_complete,
        "bridge_ready": bridge_ready,
        "authorized_adjustment": (
            round(incremental_investment_value, 2) if bridge_ready else 0.0
        ),
        "pending_value": (
            reported_value if reported_value is not None and not bridge_ready else 0.0
        ),
        "unresolved_tests": unresolved_tests,
        "unresolved_test_count": len(unresolved_tests),
        "status_view": (
            "BRIDGE_READY" if bridge_ready else "PENDING_ENTITY_CLASSIFICATION"
        ),
        "interpretation": (
            "The Long-Term Equity Investment aggregate has "
            "already been reconciled to JV and associate "
            "components. Entity-level classification is the "
            "next control layer. No portion of the aggregate "
            "is authorized for addition to SOTP equity value "
            "until individual holdings are identified, "
            "ownership is established, operating-segment "
            "overlap is resolved and an appropriate valuation "
            "basis is authorized."
        ),
        "warnings": [
            (
                "The reported Long-Term Equity Investment "
                "aggregate must not be added directly to "
                "SOTP equity value."
            ),
            ("JV and associate component balances must " "not be added separately."),
            (
                "An associate or JV may already be represented "
                "inside operating segment EBITDA and therefore "
                "may create double counting."
            ),
            (
                "Accounting carrying value does not "
                "automatically constitute authorized SOTP "
                "fair value."
            ),
        ],
        "source_overlap_analysis": overlap,
    }
