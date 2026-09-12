from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class DecisionPolicyEngine:
    """Applies institutional investment mandates and weighting profiles to decision scoring."""

    PROFILES = {
        "Conservative": {"return_weight": 0.4, "risk_weight": 0.5, "confidence_weight": 0.1},
        "Growth": {"return_weight": 0.7, "risk_weight": 0.2, "confidence_weight": 0.1},
        "Institutional": {"return_weight": 0.5, "risk_weight": 0.3, "confidence_weight": 0.2},
    }

    @classmethod
    def get_profile_weights(cls, profile_name: str) -> dict[str, float]:
        logger.info("Retrieving policy weights for profile: %s", profile_name)
        return cls.PROFILES.get(profile_name, cls.PROFILES["Institutional"])
