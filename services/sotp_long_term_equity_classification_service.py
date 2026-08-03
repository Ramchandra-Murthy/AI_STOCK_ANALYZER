from dataclasses import dataclass
from typing import Optional, List


@dataclass(frozen=True)
class ClassificationRule:
    """
    Declarative rule definition mapping economic interpretation and
    optional contextual attributes to target SOTP classifications.
    """

    interpretation: str
    relationship: Optional[str] = None

    # --- Future Domain Dimensions (Optional Predicates) ---
    business_model: Optional[str] = None
    asset_type: Optional[str] = None
    integration_level: Optional[str] = None

    classification: str = CLASSIFICATION_UNRESOLVED
    priority: int = 1


class ClassificationRuleEvaluator:
    """Evaluates interpreted evidence against declarative rules."""

    def __init__(self, custom_rules: Optional[List[ClassificationRule]] = None) -> None:
        # Standard default rules
        self.rules: List[ClassificationRule] = custom_rules or [
            # Example rule with extended dimensions
            ClassificationRule(
                interpretation=INTERPRETATION_OPERATING_INFRASTRUCTURE,
                asset_type="PIPELINE_NETWORK",
                classification=CLASSIFICATION_OPERATING_INFRASTRUCTURE,
                priority=95,
            ),
            # Standard rules...
        ]

    def find_best_rule(
        self,
        interpretation: str,
        ril_relationship: Optional[str],
        business_model: Optional[str] = None,
        asset_type: Optional[str] = None,
        integration_level: Optional[str] = None,
    ) -> List[ClassificationRule]:
        matched_rules = []
        for rule in self.rules:
            # Mandated Interpretation Match
            if rule.interpretation != interpretation:
                continue

            # Optional Contextual Attribute Checks (None acts as wildcard)
            if rule.relationship is not None and rule.relationship != ril_relationship:
                continue
            if (
                rule.business_model is not None
                and rule.business_model != business_model
            ):
                continue
            if rule.asset_type is not None and rule.asset_type != asset_type:
                continue
            if (
                rule.integration_level is not None
                and rule.integration_level != integration_level
            ):
                continue

            matched_rules.append(rule)
        return matched_rules
