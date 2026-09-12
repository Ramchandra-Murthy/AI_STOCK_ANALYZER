from __future__ import annotations

import enum


class WorkflowState(str, enum.Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    VALIDATING = "VALIDATING"
    ANALYZING = "ANALYZING"
    SCORING = "SCORING"
    REPORTING = "REPORTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
