from __future__ import annotations

from typing import Any, Dict, List

from services.sotp_long_term_equity_entity_data_service import (
    get_sotp_long_term_equity_entity_data,
)

# ==========================================================
# LONG-TERM EQUITY ECONOMIC EVIDENCE SERVICE
# ==========================================================
#
# PURPOSE
#
# This service creates the economic-evidence layer required
# before entity-level SOTP classification.
#
# It does NOT:
#   - authorize an equity-bridge adjustment
#   - assign fair value
#   - assume operating overlap
#   - infer segment membership from entity names
#   - convert Annexure A amounts into carrying values
#
# Evidence must be explicitly established before an entity
# can move from UNRESOLVED to:
#
#   OPERATING_OVERLAP
#   INCREMENTAL_INVESTMENT
#   COMPONENT_ONLY
#
# ==========================================================


ECONOMIC_EVIDENCE: Dict[str, Dict[str, Any]] = {
    "Alok Industries Limited": {
        "business_activity": None,
        "ril_relationship": None,
        "candidate_operating_segment": None,
        "operating_overlap_evidence": None,
        "economic_independence_evidence": None,
        "valuation_evidence": None,
        "classification_evidence": None,
        "source": None,
        "evidence_complete": False,
    },
    "BAM DLR Data Center Services Private Limited": {
        "business_activity": None,
        "ril_relationship": None,
        "candidate_operating_segment": None,
        "operating_overlap_evidence": None,
        "economic_independence_evidence": None,
        "valuation_evidence": None,
        "classification_evidence": None,
        "source": None,
        "evidence_complete": False,
    },
    "BAM DLR Kolkata Private Limited": {
        "business_activity": None,
        "ril_relationship": None,
        "candidate_operating_segment": None,
        "operating_overlap_evidence": None,
        "economic_independence_evidence": None,
        "valuation_evidence": None,
        "classification_evidence": None,
        "source": None,
        "evidence_complete": False,
    },
    "BAM DLR Mumbai Private Limited": {
        "business_activity": None,
        "ril_relationship": None,
        "candidate_operating_segment": None,
        "operating_overlap_evidence": None,
        "economic_independence_evidence": None,
        "valuation_evidence": None,
        "classification_evidence": None,
        "source": None,
        "evidence_complete": False,
    },
    "BAM DLR Network Services Private Limited": {
        "business_activity": None,
        "ril_relationship": None,
        "candidate_operating_segment": None,
        "operating_overlap_evidence": None,
        "economic_independence_evidence": None,
        "valuation_evidence": None,
        "classification_evidence": None,
        "source": None,
        "evidence_complete": False,
    },
    "BVM Overseas Limited": {
        "business_activity": None,
        "ril_relationship": None,
        "candidate_operating_segment": None,
        "operating_overlap_evidence": None,
        "economic_independence_evidence": None,
        "valuation_evidence": None,
        "classification_evidence": None,
        "source": None,
        "evidence_complete": False,
    },
    "DXDC Chennai Private Limited": {
        "business_activity": None,
        "ril_relationship": None,
        "candidate_operating_segment": None,
        "operating_overlap_evidence": None,
        "economic_independence_evidence": None,
        "valuation_evidence": None,
        "classification_evidence": None,
        "source": None,
        "evidence_complete": False,
    },
}


def _clean_symbol(symbol: str) -> str:

    symbol = str(symbol or "").upper().strip()

    if symbol.endswith(".NS"):
        symbol = symbol[:-3]

    return symbol


def get_sotp_long_term_equity_economic_evidence(
    symbol: str,
) -> Dict[str, Any]:

    symbol = _clean_symbol(symbol)

    data = get_sotp_long_term_equity_entity_data(symbol)

    if not isinstance(data, dict) or data.get("status") != "OK":
        return {
            "status": "UNAVAILABLE",
            "version": "V5.0",
            "symbol": symbol,
            "message": ("Long-term equity entity data is unavailable."),
            "source_data": data,
        }

    entities = data.get("entities", [])

    if not isinstance(entities, list):
        entities = []

    results: List[Dict[str, Any]] = []

    evidence_available_count = 0
    evidence_complete_count = 0

    for entity in entities:

        if not isinstance(entity, dict):
            continue

        name = entity.get("name")

        evidence = ECONOMIC_EVIDENCE.get(name, {})

        if not isinstance(evidence, dict):
            evidence = {}

        evidence_available = bool(evidence)

        evidence_complete = (
            evidence_available and evidence.get("evidence_complete") is True
        )

        if evidence_available:
            evidence_available_count += 1

        if evidence_complete:
            evidence_complete_count += 1

        results.append(
            {
                "name": name,
                "ownership_percent": entity.get("ownership_percent"),
                "reported_investment_value": entity.get("reported_investment_value"),
                "reported_amount_basis": entity.get("reported_amount_basis"),
                "business_activity": evidence.get("business_activity"),
                "ril_relationship": evidence.get("ril_relationship"),
                "candidate_operating_segment": evidence.get(
                    "candidate_operating_segment"
                ),
                "operating_overlap_evidence": evidence.get(
                    "operating_overlap_evidence"
                ),
                "economic_independence_evidence": evidence.get(
                    "economic_independence_evidence"
                ),
                "valuation_evidence": evidence.get("valuation_evidence"),
                "classification_evidence": evidence.get("classification_evidence"),
                "evidence_source": evidence.get("source"),
                "evidence_available": evidence_available,
                "evidence_complete": evidence_complete,
            }
        )

    entity_count = len(results)

    all_entities_registered = (
        entity_count > 0 and evidence_available_count == entity_count
    )

    all_evidence_complete = entity_count > 0 and evidence_complete_count == entity_count

    return {
        "status": "OK",
        "version": "V5.0",
        "symbol": symbol,
        "period": data.get("period"),
        "currency": data.get("currency", "INR"),
        "unit": data.get("unit", "crore"),
        "entity_count": entity_count,
        "evidence_registered_count": (evidence_available_count),
        "evidence_complete_count": (evidence_complete_count),
        "all_entities_registered": (all_entities_registered),
        "all_evidence_complete": (all_evidence_complete),
        "classification_ready": (all_evidence_complete),
        "entities": results,
        "status_view": (
            "EVIDENCE_COMPLETE"
            if all_evidence_complete
            else "PENDING_ECONOMIC_EVIDENCE"
        ),
        "interpretation": (
            "This service records economic evidence required "
            "for entity-level SOTP classification. Registration "
            "of an entity does not constitute evidence that its "
            "economics overlap an operating segment or represent "
            "an incremental investment."
        ),
        "warnings": [
            (
                "Entity names must not be used as sufficient "
                "evidence of operating-segment membership."
            ),
            (
                "Annexure A investment amounts remain disclosure "
                "evidence and are not automatically SOTP values."
            ),
            (
                "No entity classification is authorized until "
                "the required economic evidence is complete."
            ),
            (
                "Economic evidence and valuation evidence are "
                "separate control layers."
            ),
        ],
        "source_data": data,
    }
