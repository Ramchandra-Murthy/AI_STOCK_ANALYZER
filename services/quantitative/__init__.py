"""
EROS 3.0 quantitative service package.

Block 84:
    Core screening, optimization, risk, governance and paper execution.

Block 85:
    Quantitative execution certification.

Block 86:
    Institutional control plane and audit decision.
"""

from .block85_execution_certification import (
    Block85Certification,
    EROSBlock85ExecutionCertificationEngine,
)
from .block86_control_plane import (
    Block86ControlDecision,
    EROSBlock86ControlPlane,
)

__all__ = [
    "Block85Certification",
    "EROSBlock85ExecutionCertificationEngine",
    "Block86ControlDecision",
    "EROSBlock86ControlPlane",
]
