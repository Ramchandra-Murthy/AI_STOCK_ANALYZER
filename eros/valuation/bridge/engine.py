"""EROS valuation bridge and executable boundary.

EROS owns orchestration and result contracts.
Canonical SOTP and DCF engines remain the authorities for
valuation mathematics.

SOTP and DCF are intentionally preserved independently.
No simple mean is calculated here.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValuationBoundary:
    """Executable EROS valuation boundary."""

    sotp: Any = None
    dcf: Any = None
    provenance: dict[str, Any] = field(default_factory=dict)

    def evaluate_sotp(
        self,
        data: dict[str, Any] | None = None,
    ):
        """Execute the canonical SOTP engine."""

        from eros.valuation.sotp import evaluate_sotp

        if data is None:
            data = {}

        try:
            self.sotp = evaluate_sotp(data)
        except Exception as exc:
            self.sotp = None
            self.provenance["sotp_error"] = f"{type(exc).__name__}: {exc}"

        return self.sotp

    def evaluate_dcf(
        self,
        data: dict[str, Any] | None = None,
    ):
        """Execute the canonical DCF engine."""

        from eros.valuation.dcf import evaluate_dcf

        if data is None:
            data = {}

        try:
            self.dcf = evaluate_dcf(data)
        except Exception as exc:
            self.dcf = None
            self.provenance["dcf_error"] = f"{type(exc).__name__}: {exc}"

        return self.dcf

    def evaluate(
        self,
        data: dict[str, Any] | None = None,
        provenance: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Evaluate valuation and return the canonical EROS result.

        Empty input and incomplete boundary input remain safe.

        The returned dictionary deliberately exposes SOTP and DCF
        independently. No averaging or synthetic valuation is created.
        """

        if data is None:
            data = {}

        base_provenance = {
            **(provenance or {}),
            "sotp_executed": False,
            "dcf_executed": False,
        }

        # --------------------------------------------------------
        # EMPTY INPUT
        # --------------------------------------------------------

        if not isinstance(data, dict) or not data:
            self.sotp = None
            self.dcf = None
            self.provenance = {
                **base_provenance,
                "valuation_status": "INPUT_REQUIRED",
            }

            return {
                "status": "INPUT_REQUIRED",
                "sotp": None,
                "dcf": None,
                "provenance": self.provenance,
                "warnings": ["Valuation input is required."],
            }

        # --------------------------------------------------------
        # EXPLICIT BOUNDARY PAYLOAD
        # --------------------------------------------------------

        if set(data.keys()).issubset({"sotp", "dcf", "provenance"}):
            self.sotp = data.get("sotp")
            self.dcf = data.get("dcf")

            supplied_provenance = data.get("provenance")

            if isinstance(supplied_provenance, dict):
                self.provenance = {
                    **base_provenance,
                    **supplied_provenance,
                }
            else:
                self.provenance = {
                    **base_provenance,
                }

            self.provenance["valuation_status"] = "INPUT_REQUIRED"

            return {
                "status": "INPUT_REQUIRED",
                "sotp": self.sotp,
                "dcf": self.dcf,
                "provenance": self.provenance,
                "warnings": ["Valuation input is required."],
            }

        # --------------------------------------------------------
        # REAL VALUATION EXECUTION
        # --------------------------------------------------------

        self.provenance = {
            **base_provenance,
            "valuation_status": "EXECUTED",
        }

        warnings: list[str] = []

        try:
            self.evaluate_sotp(data)
        except Exception as exc:
            warnings.append(f"SOTP valuation failed: {type(exc).__name__}: {exc}")

        try:
            self.evaluate_dcf(data)
        except Exception as exc:
            warnings.append(f"DCF valuation failed: {type(exc).__name__}: {exc}")

        self.provenance["sotp_executed"] = self.sotp is not None
        self.provenance["dcf_executed"] = self.dcf is not None
        self.provenance["warnings"] = warnings

        return {
            "status": "COMPLETE",
            "sotp": self.sotp,
            "dcf": self.dcf,
            "provenance": self.provenance,
            "warnings": warnings,
        }


def create_valuation_boundary(
    sotp: Any = None,
    dcf: Any = None,
    provenance: dict[str, Any] | None = None,
) -> ValuationBoundary:
    """Create an executable valuation boundary."""

    return ValuationBoundary(
        sotp=sotp,
        dcf=dcf,
        provenance=provenance or {},
    )


def build_bridge(
    sotp: Any = None,
    dcf: Any = None,
    provenance: dict[str, Any] | None = None,
) -> ValuationBoundary:
    """Build an independent SOTP/DCF valuation bridge."""

    return create_valuation_boundary(
        sotp=sotp,
        dcf=dcf,
        provenance=provenance,
    )


__all__ = [
    "ValuationBoundary",
    "create_valuation_boundary",
    "build_bridge",
]
