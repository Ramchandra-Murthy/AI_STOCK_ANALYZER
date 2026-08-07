from __future__ import annotations

from typing import Dict, Type
from backend.workflow.workflow_engine import WorkflowEngine

class WorkflowRegistry:
    _registry: Dict[str, Type[WorkflowEngine]] = {}

    @classmethod
    def register(cls, name: str, engine_cls: Type[WorkflowEngine]) -> None:
        cls._registry[name] = engine_cls

    @classmethod
    def get(cls, name: str) -> Type[WorkflowEngine]:
        if name not in cls._registry:
            raise KeyError(f"Workflow '{name}' not found in registry.")
        return cls._registry[name]