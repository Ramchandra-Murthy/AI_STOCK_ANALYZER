from __future__ import annotations

import logging
import time
from typing import Callable, List, Dict, Any
from backend.workflow.workflow_state import WorkflowState
from backend.workflow.workflow_context import WorkflowContext
from backend.workflow.workflow_exceptions import InvalidStateTransitionError, StageExecutionError

logger = logging.getLogger(__name__)

VALID_TRANSITIONS = {
    WorkflowState.CREATED: {WorkflowState.QUEUED, WorkflowState.FAILED},
    WorkflowState.QUEUED: {WorkflowState.RUNNING, WorkflowState.FAILED},
    WorkflowState.RUNNING: {WorkflowState.VALIDATING, WorkflowState.FAILED},
    WorkflowState.VALIDATING: {WorkflowState.ANALYZING, WorkflowState.FAILED},
    WorkflowState.ANALYZING: {WorkflowState.SCORING, WorkflowState.FAILED},
    WorkflowState.SCORING: {WorkflowState.REPORTING, WorkflowState.FAILED},
    WorkflowState.REPORTING: {WorkflowState.COMPLETED, WorkflowState.FAILED},
    WorkflowState.COMPLETED: set(),
    WorkflowState.FAILED: set()
}

class WorkflowEngine:
    def __init__(self, workflow_id: str, symbol: str, user: str) -> None:
        self.context = WorkflowContext(workflow_id=workflow_id, symbol=symbol, user=user)
        self.state = WorkflowState.CREATED
        self.stages: List[Callable[[WorkflowContext], Dict[str, Any]]] = []
        self.retry_limit = 2

    def transition_to(self, new_state: WorkflowState) -> None:
        if new_state not in VALID_TRANSITIONS.get(self.state, set()):
            raise InvalidStateTransitionError(f"Invalid state transition from {self.state} to {new_state}")
        logger.info("Workflow %s transitioning state: %s -> %s", self.context.workflow_id, self.state, new_state)
        self.state = new_state

    def add_stage(self, stage_fn: Callable[[WorkflowContext], Dict[str, Any]]) -> None:
        self.stages.append(stage_fn)

    def execute(self) -> WorkflowContext:
        start_time = time.perf_counter()
        try:
            self.transition_to(WorkflowState.QUEUED)
            self.transition_to(WorkflowState.RUNNING)
            self.transition_to(WorkflowState.VALIDATING)
            
            # Validation pass
            if not self.context.symbol:
                raise StageExecutionError("Validation failed: Symbol is required.")

            self.transition_to(WorkflowState.ANALYZING)
            for stage in self.stages:
                attempts = 0
                success = False
                while attempts <= self.retry_limit and not success:
                    try:
                        stage_result = stage(self.context)
                        if stage_result:
                            self.context.shared_data.update(stage_result)
                        success = True
                    except Exception as e:
                        attempts += 1
                        logger.warning("Stage execution attempt %s failed: %s. Retrying...", attempts, str(e))
                        if attempts > self.retry_limit:
                            raise StageExecutionError(f"Stage failed after {self.retry_limit} retries: {str(e)}") from e

            self.transition_to(WorkflowState.SCORING)
            self.transition_to(WorkflowState.REPORTING)
            self.transition_to(WorkflowState.COMPLETED)

            duration = round((time.perf_counter() - start_time) * 1000.0, 2)
            self.context.metrics["total_duration_ms"] = duration
            logger.info("Workflow %s completed successfully in %s ms", self.context.workflow_id, duration)
            return self.context

        except Exception as e:
            logger.error("Workflow %s failed in state %s: %s", self.context.workflow_id, self.state, str(e))
            self.state = WorkflowState.FAILED
            raise StageExecutionError(f"Workflow execution failed: {str(e)}") from e