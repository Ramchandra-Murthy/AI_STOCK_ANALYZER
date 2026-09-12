from dataclasses import dataclass

from services.sotp_long_term_equity_domain_constants import (
    CLASSIFICATION_ELIMINATE,
    CLASSIFICATION_FINANCIAL_INVESTMENT,
    CLASSIFICATION_INCUBATION_INVESTMENT,
    CLASSIFICATION_NON_OPERATING_ASSET,
    CLASSIFICATION_OPERATING_ASSOCIATE,
    CLASSIFICATION_OPERATING_INFRASTRUCTURE,
    CLASSIFICATION_OPERATING_JOINT_VENTURE,
    CLASSIFICATION_OPERATING_SUBSIDIARY,
    CLASSIFICATION_PASSIVE_INVESTMENT,
    CLASSIFICATION_STRATEGIC_INVESTMENT,
    CLASSIFICATION_UNRESOLVED,
    INTERPRETATION_ELIMINATED_ENTITY,
    INTERPRETATION_FINANCIAL_INVESTMENT,
    INTERPRETATION_INCUBATION_INVESTMENT,
    INTERPRETATION_NON_OPERATING_ASSET,
    INTERPRETATION_OPERATING_ENTITY,
    INTERPRETATION_OPERATING_INFRASTRUCTURE,
    INTERPRETATION_PASSIVE_INVESTMENT,
    INTERPRETATION_STRATEGIC_INVESTMENT,
    INTERPRETATION_UNRESOLVED,
    RELATIONSHIP_ASSOCIATE,
    RELATIONSHIP_CONTROLLED_ENTITY,
    RELATIONSHIP_JOINT_VENTURE,
    RELATIONSHIP_SUBSIDIARY,
)


@dataclass(frozen=True)
class ClassificationRule:
    """
    Declarative Stage 13C.1 rule definition.

    Interpretation is the primary predicate.
    Relationship and future contextual dimensions are optional predicates.

    Rules do not authorize valuation or SOTP bridge values.
    """

    interpretation: str
    relationship: str | None = None

    # Future domain dimensions
    business_model: str | None = None
    asset_type: str | None = None
    integration_level: str | None = None

    classification: str = CLASSIFICATION_UNRESOLVED
    priority: int = 1


class ClassificationRuleEvaluator:
    """Evaluates interpreted evidence against declarative rules."""

    def __init__(
        self,
        custom_rules: list[ClassificationRule] | None = None,
    ) -> None:
        self.rules: list[ClassificationRule] = (
            custom_rules if custom_rules is not None else self._default_rules()
        )

    @staticmethod
    def _default_rules() -> list[ClassificationRule]:
        return [
            # ------------------------------------------------------
            # OPERATING ENTITIES
            # ------------------------------------------------------
            ClassificationRule(
                interpretation=INTERPRETATION_OPERATING_ENTITY,
                relationship=RELATIONSHIP_SUBSIDIARY,
                classification=CLASSIFICATION_OPERATING_SUBSIDIARY,
                priority=100,
            ),
            ClassificationRule(
                interpretation=INTERPRETATION_OPERATING_ENTITY,
                relationship=RELATIONSHIP_CONTROLLED_ENTITY,
                classification=CLASSIFICATION_OPERATING_SUBSIDIARY,
                priority=99,
            ),
            ClassificationRule(
                interpretation=INTERPRETATION_OPERATING_ENTITY,
                relationship=RELATIONSHIP_ASSOCIATE,
                classification=CLASSIFICATION_OPERATING_ASSOCIATE,
                priority=100,
            ),
            ClassificationRule(
                interpretation=INTERPRETATION_OPERATING_ENTITY,
                relationship=RELATIONSHIP_JOINT_VENTURE,
                classification=CLASSIFICATION_OPERATING_JOINT_VENTURE,
                priority=100,
            ),
            # ------------------------------------------------------
            # OPERATING INFRASTRUCTURE
            # ------------------------------------------------------
            ClassificationRule(
                interpretation=INTERPRETATION_OPERATING_INFRASTRUCTURE,
                classification=CLASSIFICATION_OPERATING_INFRASTRUCTURE,
                priority=95,
            ),
            # ------------------------------------------------------
            # INVESTMENTS
            # ------------------------------------------------------
            ClassificationRule(
                interpretation=INTERPRETATION_STRATEGIC_INVESTMENT,
                classification=CLASSIFICATION_STRATEGIC_INVESTMENT,
                priority=90,
            ),
            ClassificationRule(
                interpretation=INTERPRETATION_FINANCIAL_INVESTMENT,
                classification=CLASSIFICATION_FINANCIAL_INVESTMENT,
                priority=90,
            ),
            ClassificationRule(
                interpretation=INTERPRETATION_INCUBATION_INVESTMENT,
                classification=CLASSIFICATION_INCUBATION_INVESTMENT,
                priority=90,
            ),
            ClassificationRule(
                interpretation=INTERPRETATION_PASSIVE_INVESTMENT,
                classification=CLASSIFICATION_PASSIVE_INVESTMENT,
                priority=90,
            ),
            # ------------------------------------------------------
            # NON-OPERATING / ELIMINATION
            # ------------------------------------------------------
            ClassificationRule(
                interpretation=INTERPRETATION_NON_OPERATING_ASSET,
                classification=CLASSIFICATION_NON_OPERATING_ASSET,
                priority=90,
            ),
            ClassificationRule(
                interpretation=INTERPRETATION_ELIMINATED_ENTITY,
                classification=CLASSIFICATION_ELIMINATE,
                priority=90,
            ),
            # ------------------------------------------------------
            # EXPLICIT UNRESOLVED FALLBACK
            # ------------------------------------------------------
            ClassificationRule(
                interpretation=INTERPRETATION_UNRESOLVED,
                classification=CLASSIFICATION_UNRESOLVED,
                priority=0,
            ),
        ]

    def find_best_rule(
        self,
        interpretation: str,
        ril_relationship: str | None,
        business_model: str | None = None,
        asset_type: str | None = None,
        integration_level: str | None = None,
    ) -> list[ClassificationRule]:
        """
        Return all matching rules ordered by priority.

        Returning a list intentionally preserves the ability of later
        Stage 13C logic to detect multiple equally applicable rules
        instead of silently selecting one.
        """
        matched_rules: list[ClassificationRule] = []

        for rule in self.rules:
            if rule.interpretation != interpretation:
                continue

            if rule.relationship is not None and rule.relationship != ril_relationship:
                continue

            if rule.business_model is not None and rule.business_model != business_model:
                continue

            if rule.asset_type is not None and rule.asset_type != asset_type:
                continue

            if rule.integration_level is not None and rule.integration_level != integration_level:
                continue

            matched_rules.append(rule)

        return sorted(
            matched_rules,
            key=lambda rule: rule.priority,
            reverse=True,
        )
