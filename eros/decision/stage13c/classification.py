from __future__ import annotations

"""
==========================================================
LONG-TERM EQUITY CLASSIFICATION DECISION SERVICE
Stage   : 13C.2
Status  : CONTROLLED
==========================================================

Purpose
-------
Consumes the authoritative Stage 13C.1 evidence records and
applies the declarative ClassificationRuleEvaluator.

This service:
    - does classify entities
    - does not perform valuation
    - does not calculate SOTP
    - does not authorize separate SOTP values

Stage 13C.1 remains responsible for evidence ingestion.
Stage 13C.2 is responsible for classification decisions.
"""

from typing import Any

from services.sotp_long_term_equity_classification_service import (
    ClassificationRuleEvaluator,
)
from services.sotp_long_term_equity_domain_constants import (
    CLASSIFICATION_STATUS_COMPLETE,
    CLASSIFICATION_STATUS_CONFLICTING,
    CLASSIFICATION_STATUS_PARTIAL,
    CLASSIFICATION_STATUS_UNRESOLVED,
    INTERPRETATION_ELIMINATED_ENTITY,
    INTERPRETATION_FINANCIAL_INVESTMENT,
    INTERPRETATION_INCUBATION_INVESTMENT,
    INTERPRETATION_NON_OPERATING_ASSET,
    INTERPRETATION_OPERATING_ENTITY,
    INTERPRETATION_OPERATING_INFRASTRUCTURE,
    INTERPRETATION_PASSIVE_INVESTMENT,
    INTERPRETATION_STRATEGIC_INVESTMENT,
    INTERPRETATION_UNRESOLVED,
)

STAGE_13C_2_ID = "STAGE_13C_2"
CLASSIFICATION_STAGE = "13C.2"


def _derive_interpretation(
    record: dict[str, Any],
) -> str:
    """
    Translate Stage 13C.1 economic evidence into the primary
    interpretation expected by the declarative rule engine.

    Conservative design:
    unsupported or ambiguous evidence remains UNRESOLVED.
    """

    economic_category = record.get("economic_category")
    relationship = record.get("ril_relationship")

    if economic_category == "STRATEGIC_INVESTMENT":
        return INTERPRETATION_STRATEGIC_INVESTMENT

    if economic_category == "FINANCIAL_INVESTMENT":
        return INTERPRETATION_FINANCIAL_INVESTMENT

    if economic_category == "INCUBATION_INVESTMENT":
        return INTERPRETATION_INCUBATION_INVESTMENT

    if economic_category == "PASSIVE_INVESTMENT":
        return INTERPRETATION_PASSIVE_INVESTMENT

    if economic_category == "INFRASTRUCTURE_INVESTMENT":
        return INTERPRETATION_OPERATING_INFRASTRUCTURE

    if economic_category == "NON_OPERATING_ASSET":
        return INTERPRETATION_NON_OPERATING_ASSET

    if economic_category == "ELIMINATED_ENTITY":
        return INTERPRETATION_ELIMINATED_ENTITY

    if economic_category == "OPERATING_ASSOCIATE":
        return INTERPRETATION_OPERATING_ENTITY

    if economic_category == "JOINT_OPERATION_EXPOSURE":
        if relationship == "JOINT_VENTURE":
            return INTERPRETATION_OPERATING_ENTITY
        return INTERPRETATION_UNRESOLVED

    return INTERPRETATION_UNRESOLVED


def classify_record(
    record: dict[str, Any],
    evaluator: ClassificationRuleEvaluator | None = None,
) -> dict[str, Any]:
    """
    Apply Stage 13C.2 declarative classification to one
    Stage 13C.1 evidence record.

    No valuation or SOTP authorization is performed here.
    """

    if not isinstance(record, dict):
        raise TypeError("Classification record must be a dictionary.")

    evaluator = evaluator or ClassificationRuleEvaluator()

    result = dict(record)

    interpretation = _derive_interpretation(record)

    relationship = record.get("ril_relationship")

    matches = evaluator.find_best_rule(
        interpretation=interpretation,
        ril_relationship=relationship,
        business_model=record.get("business_model"),
        asset_type=record.get("asset_type"),
        integration_level=record.get("integration_level"),
    )

    result["classification_stage"] = CLASSIFICATION_STAGE
    result["classification_interpretation"] = interpretation
    result["classification_rule_count"] = len(matches)

    # Hard control: no match means unresolved.
    if not matches:
        result["classification_status"] = CLASSIFICATION_STATUS_UNRESOLVED
        result["classification"] = CLASSIFICATION_STATUS_UNRESOLVED
        result["classification_source"] = None
        result["classification_reason"] = (
            "No declarative classification rule matched the available "
            "economic interpretation and contextual evidence."
        )
        result["separate_sotp_value_authorized"] = False
        return result

    highest_priority = matches[0].priority
    highest_priority_matches = [rule for rule in matches if rule.priority == highest_priority]

    # Multiple equally authoritative rules are a conflict.
    if len(highest_priority_matches) > 1:
        result["classification_status"] = CLASSIFICATION_STATUS_CONFLICTING
        result["classification"] = CLASSIFICATION_STATUS_UNRESOLVED
        result["classification_source"] = "DECLARATIVE_RULE_ENGINE"
        result["classification_reason"] = (
            "Multiple equally prioritized classification rules matched."
        )
        result["classification_rule_matches"] = [
            {
                "interpretation": rule.interpretation,
                "relationship": rule.relationship,
                "classification": rule.classification,
                "priority": rule.priority,
            }
            for rule in matches
        ]
        result["separate_sotp_value_authorized"] = False
        return result

    rule = highest_priority_matches[0]

    result["classification_status"] = CLASSIFICATION_STATUS_COMPLETE
    result["classification"] = rule.classification
    result["classification_source"] = "DECLARATIVE_RULE_ENGINE"
    result["classification_reason"] = (
        f"Rule matched interpretation={rule.interpretation!r}, "
        f"relationship={rule.relationship!r}, "
        f"priority={rule.priority}."
    )

    result["classification_rule_matches"] = [
        {
            "interpretation": matched.interpretation,
            "relationship": matched.relationship,
            "classification": matched.classification,
            "priority": matched.priority,
        }
        for matched in matches
    ]

    # Stage 13C.2 does not authorize valuation.
    result["separate_sotp_value_authorized"] = False

    return result


def classify_records(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Classify a complete Stage 13C.1 population.
    """

    evaluator = ClassificationRuleEvaluator()

    return [classify_record(record, evaluator=evaluator) for record in records]


def audit_classification_records(
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Produce a controlled Stage 13C.2 classification audit.
    """

    classified = classify_records(records)

    complete_count = sum(
        1
        for record in classified
        if record.get("classification_status") == CLASSIFICATION_STATUS_COMPLETE
    )

    partial_count = sum(
        1
        for record in classified
        if record.get("classification_status") == CLASSIFICATION_STATUS_PARTIAL
    )

    conflicting_count = sum(
        1
        for record in classified
        if record.get("classification_status") == CLASSIFICATION_STATUS_CONFLICTING
    )

    unresolved_count = sum(
        1
        for record in classified
        if record.get("classification_status") == CLASSIFICATION_STATUS_UNRESOLVED
    )

    return {
        "status": "OK",
        "stage": CLASSIFICATION_STAGE,
        "entity_count": len(classified),
        "complete_count": complete_count,
        "partial_count": partial_count,
        "conflicting_count": conflicting_count,
        "unresolved_count": unresolved_count,
        "classification_complete": (
            len(classified) > 0
            and complete_count == len(classified)
            and partial_count == 0
            and conflicting_count == 0
            and unresolved_count == 0
        ),
        "bridge_ready": False,
        "separate_sotp_value_authorized": False,
        "records": classified,
    }
