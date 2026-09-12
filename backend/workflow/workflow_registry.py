from __future__ import annotations

from backend.workflow.workflow_engine import WorkflowEngine


class WorkflowRegistry:
    _registry: dict[str, type[WorkflowEngine]] = {}

    @classmethod
    def register(cls, name: str, engine_cls: type[WorkflowEngine]) -> None:
        cls._registry[name] = engine_cls

    @classmethod
    def get(cls, name: str) -> type[WorkflowEngine]:
        if name not in cls._registry:
            raise KeyError(f"Workflow '{name}' not found in registry.")
        return cls._registry[name]
