"""Regression tests for SOTP classification rule evaluation."""

from services.sotp_long_term_equity_classification_service import (
    ClassificationRule,
    ClassificationRuleEvaluator,
)
from services.sotp_long_term_equity_domain_constants import (
    CLASSIFICATION_OPERATING_INFRASTRUCTURE,
    CLASSIFICATION_UNRESOLVED,
    INTERPRETATION_OPERATING_INFRASTRUCTURE,
)


def test_module_imports_and_rule_defaults_to_unresolved() -> None:
    rule = ClassificationRule(interpretation="ANYTHING")

    assert rule.classification == CLASSIFICATION_UNRESOLVED
    assert rule.priority == 1


def test_default_rule_maps_pipeline_infrastructure() -> None:
    evaluator = ClassificationRuleEvaluator()

    matches = evaluator.find_best_rule(
        interpretation=INTERPRETATION_OPERATING_INFRASTRUCTURE,
        ril_relationship=None,
        asset_type="PIPELINE_NETWORK",
    )

    assert len(matches) == 1
    assert matches[0].classification == CLASSIFICATION_OPERATING_INFRASTRUCTURE
    assert matches[0].priority == 95


def test_default_rule_ignores_other_asset_types() -> None:
    evaluator = ClassificationRuleEvaluator()

    matches = evaluator.find_best_rule(
        interpretation=INTERPRETATION_OPERATING_INFRASTRUCTURE,
        ril_relationship=None,
        asset_type="SOMETHING_ELSE",
    )

    assert matches == []


def test_interpretation_constant_matches_expected_value() -> None:
    assert INTERPRETATION_OPERATING_INFRASTRUCTURE == "OPERATING_INFRASTRUCTURE"
