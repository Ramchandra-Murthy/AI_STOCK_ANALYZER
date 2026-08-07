from __future__ import annotations
from backend.exceptions import ServiceError

class WorkflowEngineError(ServiceError):
    """Base exception for workflow engine failures."""
    pass

class InvalidStateTransitionError(WorkflowEngineError):
    """Raised when attempting an illegal workflow state transition."""
    pass

class StageExecutionError(WorkflowEngineError):
    """Raised when an individual workflow stage execution fails."""
    pass