from __future__ import annotations

from typing import Any, Dict

from services.sotp_long_term_equity_entity_data_service import (
    get_sotp_long_term_equity_entity_data,
)


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


def reconcile_sotp_long_term_equity_entities(
    symbol: str,
) -> Dict[str, Any]:

    symbol = str(symbol or "").upper().strip()

    if symbol.endswith(".NS"):
        symbol = symbol[:-3]

    data = get_sotp_long_term_equity_entity_data(symbol)

    if data.get("status") != "OK":
        return {
            "status": "UNAVAILABLE",
            "version": "V5.0",
            "symbol": symbol,
            "message": ("Long-term equity entity data is unavailable."),
            "source_data": data,
        }

    reported_aggregate = _num(data.get("reported_long_term_equity_investment")) or 0.0

    entities = data.get("entities", [])

    if not isinstance(entities, list):
        entities = []

    captured_value = 0.0

    valued_entity_count = 0
    unresolved_entity_count = 0

    for entity in entities:

        if not isinstance(entity, dict):
            continue

        value = _num(entity.get("reported_investment_value"))

        if value is not None:
            captured_value += value
            valued_entity_count += 1

        if entity.get("classification") in (
            None,
            "UNRESOLVED",
        ):
            unresolved_entity_count += 1

    reconciliation_gap = reported_aggregate - captured_value

    if reported_aggregate > 0:
        coverage = captured_value / reported_aggregate
    else:
        coverage = 0.0

    accounting_reconciles = abs(reconciliation_gap) <= 1.0

    entity_population_complete = bool(data.get("entity_level_holdings_complete"))

    classification_complete = (
        entity_population_complete and unresolved_entity_count == 0
    )

    bridge_ready = (
        accounting_reconciles and entity_population_complete and classification_complete
    )

    return {
        "status": "OK",
        "version": "V5.0",
        "symbol": symbol,
        "period": data.get("period"),
        "currency": data.get("currency", "INR"),
        "unit": data.get("unit", "crore"),
        "reported_long_term_equity_investment": (round(reported_aggregate, 2)),
        "captured_entity_value": round(
            captured_value,
            2,
        ),
        "reconciliation_gap": round(
            reconciliation_gap,
            2,
        ),
        "captured_value_coverage": round(
            coverage,
            4,
        ),
        "captured_value_coverage_percent": round(
            coverage * 100.0,
            2,
        ),
        "entity_count": len(entities),
        "valued_entity_count": (valued_entity_count),
        "unresolved_entity_count": (unresolved_entity_count),
        "accounting_reconciles": (accounting_reconciles),
        "entity_population_complete": (entity_population_complete),
        "classification_complete": (classification_complete),
        "bridge_ready": bridge_ready,
        "authorization_tests": {
            "aggregate_reconciles": (accounting_reconciles),
            "entity_population_complete": (entity_population_complete),
            "classification_complete": (classification_complete),
        },
        "sotp_adjustment": {
            "included_value": 0.0,
            "pending_value": round(
                reported_aggregate,
                2,
            ),
            "treatment": "DO_NOT_ADD_YET",
        },
        "status_view": (
            "RECONCILED" if bridge_ready else "PENDING_ENTITY_RECONCILIATION"
        ),
        "interpretation": (
            "This control compares captured entity-level "
            "investment evidence with the reported "
            "Long-Term Equity Investment aggregate. "
            "Reconciliation alone does not authorize "
            "addition to SOTP equity value."
        ),
        "warnings": [
            (
                "The entity population is incomplete "
                "until the captured investment values "
                "reconcile to the reported aggregate."
            ),
            (
                "Accounting reconciliation does not "
                "resolve operating-segment overlap."
            ),
            ("Accounting carrying value is not " "automatically SOTP fair value."),
            (
                "No long-term equity investment may "
                "enter the equity bridge while "
                "bridge_ready is false."
            ),
        ],
        "source_data": data,
    }
