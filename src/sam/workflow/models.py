"""Pydantic models for Workflow DSL."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class WorkflowTransition(BaseModel):
    """Defines transitions between workflow steps based on execution outcome."""

    on_success: Optional[str] = Field(default=None, description="Step ID to execute on success")
    on_failure: Optional[str] = Field(default=None, description="Step ID to execute on failure")
    on_timeout: Optional[str] = Field(default=None, description="Step ID to execute on timeout")

    class Config:
        extra = "forbid"


class WorkflowStep(BaseModel):
    """A single step in a workflow definition."""

    id: str = Field(description="Unique identifier within the workflow")
    capability: str = Field(description="Capability ID to execute")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="Input parameters for the capability")
    timeout: Optional[int] = Field(default=None, description="Timeout in seconds")
    retry: Optional[int] = Field(default=None, description="Number of retries on failure")
    transition: WorkflowTransition = Field(default_factory=WorkflowTransition)

    class Config:
        extra = "forbid"


class WorkflowDefinition(BaseModel):
    """Complete workflow definition."""

    name: str = Field(description="Workflow name")
    description: Optional[str] = Field(default=None, description="Workflow description")
    version: str = Field(default="1.0.0", description="Workflow version")
    steps: List[WorkflowStep] = Field(default_factory=list, description="Workflow steps")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        extra = "forbid"

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by its ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_step_ids(self) -> List[str]:
        """Get all step IDs in order."""
        return [step.id for step in self.steps]