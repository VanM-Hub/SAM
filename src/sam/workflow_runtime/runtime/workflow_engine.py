"""Workflow Engine — info engine workflow (Sprint 199)."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowEngineInfo:
    """Info engine workflow (immutable)."""
    name: str = "workflow_engine"
    no_inference: bool = True
    is_llm: bool = False
    is_ai: bool = False
    deterministic: bool = True
    preview_only: bool = True


class WorkflowEngine:
    """Engine workflow. Hanya menyusun DTO, tidak scheduling/reasoning."""

    def info(self) -> WorkflowEngineInfo:
        return WorkflowEngineInfo()
