"""
EROS 3.0 - SOTP Facade

This module is intentionally thin.

Existing SOTP mathematics remains in the proven legacy engine.
EROS calls that engine through this boundary and normalizes the
result.
"""


def evaluate_sotp(*args, **kwargs):
    """
    Placeholder facade for the canonical SOTP engine.

    The exact legacy callable is wired after source inspection
    confirms the authoritative implementation.
    """

    raise NotImplementedError(
        "Canonical SOTP engine has not yet been wired. " "Do not duplicate SOTP mathematics here."
    )


__all__ = ["evaluate_sotp"]
