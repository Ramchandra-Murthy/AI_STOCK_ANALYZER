from __future__ import annotations

from typing import Any, Dict, List

# ==========================================================
# RELIANCE FY2025-26 LONG-TERM EQUITY ENTITY EVIDENCE
# ==========================================================
#
# Source basis:
# Reliance Industries Limited Integrated Annual Report
# FY2025-26
#
# Important:
# This service is an EVIDENCE layer.
#
# It does NOT:
#   - authorize SOTP additions
#   - assign market values
#   - decide operating overlap automatically
#   - replace the accounting aggregate
#
# Entity classifications remain UNRESOLVED until a later
# policy/overlap service establishes their economic treatment.
# ==========================================================


RELIANCE_LONG_TERM_EQUITY_ENTITIES: List[Dict[str, Any]] = [
    {
        "name": "Alok Industries Limited",
        "country": "India",
        "ownership_percent": 40.01,
        "reported_investment_value": 268.81,
        "reported_amount_basis": "ANNEXURE_A_AMOUNT_OF_INVESTMENT",
        "comparable_to_consolidated_carrying_value": False,
        "relationship": "ASSOCIATE_OR_JV",
        "classification": "UNRESOLVED",
        "operating_segment": None,
        "operating_overlap": None,
        "valuation_basis": None,
        "source": "RIL Integrated Annual Report FY2025-26",
    },
    {
        "name": "BAM DLR Data Center Services Private Limited",
        "country": "India",
        "ownership_percent": 33.33,
        "reported_investment_value": 9.16,
        "reported_amount_basis": "ANNEXURE_A_AMOUNT_OF_INVESTMENT",
        "comparable_to_consolidated_carrying_value": False,
        "relationship": "ASSOCIATE_OR_JV",
        "classification": "UNRESOLVED",
        "operating_segment": None,
        "operating_overlap": None,
        "valuation_basis": None,
        "source": "RIL Integrated Annual Report FY2025-26",
    },
    {
        "name": "BAM DLR Kolkata Private Limited",
        "country": "India",
        "ownership_percent": 33.33,
        "reported_investment_value": 0.34,
        "reported_amount_basis": "ANNEXURE_A_AMOUNT_OF_INVESTMENT",
        "comparable_to_consolidated_carrying_value": False,
        "relationship": "ASSOCIATE_OR_JV",
        "classification": "UNRESOLVED",
        "operating_segment": None,
        "operating_overlap": None,
        "valuation_basis": None,
        "source": "RIL Integrated Annual Report FY2025-26",
    },
    {
        "name": "BAM DLR Mumbai Private Limited",
        "country": "India",
        "ownership_percent": 33.33,
        "reported_investment_value": 133.64,
        "reported_amount_basis": "ANNEXURE_A_AMOUNT_OF_INVESTMENT",
        "comparable_to_consolidated_carrying_value": False,
        "relationship": "ASSOCIATE_OR_JV",
        "classification": "UNRESOLVED",
        "operating_segment": None,
        "operating_overlap": None,
        "valuation_basis": None,
        "source": "RIL Integrated Annual Report FY2025-26",
    },
    {
        "name": "BAM DLR Network Services Private Limited",
        "country": "India",
        "ownership_percent": 33.33,
        "reported_investment_value": 1.98,
        "reported_amount_basis": "ANNEXURE_A_AMOUNT_OF_INVESTMENT",
        "comparable_to_consolidated_carrying_value": False,
        "relationship": "ASSOCIATE_OR_JV",
        "classification": "UNRESOLVED",
        "operating_segment": None,
        "operating_overlap": None,
        "valuation_basis": None,
        "source": "RIL Integrated Annual Report FY2025-26",
    },
    {
        "name": "BVM Overseas Limited",
        "country": None,
        "ownership_percent": 70.00,
        "reported_investment_value": None,
        "reported_amount_basis": "ANNEXURE_A_AMOUNT_OF_INVESTMENT",
        "comparable_to_consolidated_carrying_value": False,
        "relationship": "ASSOCIATE_OR_JV",
        "classification": "UNRESOLVED",
        "operating_segment": None,
        "operating_overlap": None,
        "valuation_basis": None,
        "source": "RIL Integrated Annual Report FY2025-26",
    },
    {
        "name": "DXDC Chennai Private Limited",
        "country": "India",
        "ownership_percent": 33.33,
        "reported_investment_value": 209.85,
        "reported_amount_basis": "ANNEXURE_A_AMOUNT_OF_INVESTMENT",
        "comparable_to_consolidated_carrying_value": False,
        "relationship": "ASSOCIATE_OR_JV",
        "classification": "UNRESOLVED",
        "operating_segment": None,
        "operating_overlap": None,
        "valuation_basis": None,
        "source": "RIL Integrated Annual Report FY2025-26",
    },
]


def _safe_float(value: Any):
    try:
        if value is None:
            return None

        value = float(value)

        if value != value:
            return None

        return value

    except (TypeError, ValueError):
        return None


def get_sotp_long_term_equity_entity_data(
    symbol: str,
) -> Dict[str, Any]:

    symbol = str(symbol or "").upper().strip()

    if symbol.endswith(".NS"):
        symbol = symbol[:-3]

    if symbol != "RELIANCE":
        return {
            "status": "UNAVAILABLE",
            "version": "V5.0",
            "symbol": symbol,
            "message": (
                "Entity-level long-term equity evidence "
                "is not configured for this symbol."
            ),
        }

    entities = [dict(entity) for entity in RELIANCE_LONG_TERM_EQUITY_ENTITIES]

    entity_count = len(entities)

    entities_with_ownership = sum(
        1
        for entity in entities
        if _safe_float(entity.get("ownership_percent")) is not None
    )

    entities_with_investment_value = sum(
        1
        for entity in entities
        if _safe_float(entity.get("reported_investment_value")) is not None
    )

    captured_investment_value = sum(
        _safe_float(entity.get("reported_investment_value")) or 0.0
        for entity in entities
    )

    reported_aggregate = 16226.0

    coverage_ratio = (
        captured_investment_value / reported_aggregate
        if reported_aggregate > 0
        else 0.0
    )

    complete_entity_population = False

    return {
        "status": "OK",
        "version": "V5.0",
        "symbol": symbol,
        "period": "2026-03-31",
        "currency": "INR",
        "unit": "crore",
        "reported_long_term_equity_investment": (reported_aggregate),
        "entity_count": entity_count,
        "entities_with_ownership": (entities_with_ownership),
        "entities_with_investment_value": (entities_with_investment_value),
        "captured_investment_value": round(
            captured_investment_value,
            2,
        ),
        "captured_value_coverage": round(
            coverage_ratio,
            4,
        ),
        "captured_value_coverage_percent": round(
            coverage_ratio * 100.0,
            2,
        ),
        "complete_entity_population": (complete_entity_population),
        "entity_level_holdings_available": (entity_count > 0),
        "entity_level_holdings_complete": (complete_entity_population),
        "bridge_ready": False,
        "entities": entities,
        "interpretation": (
            "Entity-level evidence has begun to be "
            "captured from the FY2025-26 annual report. "
            "The current dataset is intentionally partial "
            "and must not be treated as a complete "
            "reconciliation of the reported Long-Term "
            "Equity Investment aggregate."
        ),
        "warnings": [
            (
                "Entity-level evidence availability does "
                "not mean entity-level classification is "
                "complete."
            ),
            (
                "The current entity list is partial and "
                "must not authorize any SOTP adjustment."
            ),
            ("Operating overlap and valuation basis " "remain unresolved."),
            (
                "Reported investment amounts are "
                "accounting evidence and are not "
                "automatically fair values."
            ),
        ],
    }
