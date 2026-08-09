"""Workflow Foundation - WP-01..10 (MISSION-5.4 / IP-5.4-001).

Identity, definition, step model, input/output, state, dependency, validation,
persistence, explainability untuk Workflow Citizen.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


class WorkflowStatus(str, Enum):
    """Status workflow."""

    DEFINED = "defined"
    VALIDATED = "validated"
    ACTIVE = "active"
    RETIRED = "retired"


@dataclass(frozen=True)
class WorkflowIdentity:
    """Identitas workflow (immutable)."""

    workflow_id: str
    name: str
    version: str = "1.0.0"
    created_at: str = field(default_factory=_now_utc)

    @property
    def is_well_formed(self) -> bool:
        return bool(self.workflow_id.strip()) and bool(self.name.strip())

    def as_dict(self) -> dict:
        return {"workflow_id": self.workflow_id, "name": self.name, "version": self.version, "created_at": self.created_at}


class StepKind(str, Enum):
    """Jenis step dalam workflow."""

    TASK = "task"
    DECISION = "decision"
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    WAIT = "wait"


class StepState(str, Enum):
    """State step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True)
class WorkflowStep:
    """Satu step workflow."""

    step_id: str
    kind: StepKind = StepKind.TASK
    label: str = ""

    def as_dict(self) -> dict:
        return {"step_id": self.step_id, "kind": self.kind.value, "label": self.label}


@dataclass(frozen=True)
class WorkflowInput:
    """Contract input workflow."""

    fields: Tuple[str, ...] = field(default_factory=tuple)

    def requires(self, provided: Dict[str, Any]) -> bool:
        return all(f in provided for f in self.fields)

    def as_dict(self) -> dict:
        return {"fields": list(self.fields)}


@dataclass(frozen=True)
class WorkflowOutput:
    """Contract output workflow."""

    fields: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"fields": list(self.fields)}


@dataclass(frozen=True)
class StepDependency:
    """Dependency antar step."""

    step_id: str
    depends_on: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {"step_id": self.step_id, "depends_on": list(self.depends_on)}


@dataclass(frozen=True)
class WorkflowDefinition:
    """Definisi deklaratif workflow."""

    identity: WorkflowIdentity
    steps: Tuple[WorkflowStep, ...] = field(default_factory=tuple)
    inputs: Tuple[str, ...] = field(default_factory=tuple)
    outputs: Tuple[str, ...] = field(default_factory=tuple)
    dependencies: Tuple[StepDependency, ...] = field(default_factory=tuple)

    def step(self, step_id: str) -> Optional[WorkflowStep]:
        for s in self.steps:
            if s.step_id == step_id:
                return s
        return None

    def step_ids(self) -> Tuple[str, ...]:
        return tuple(s.step_id for s in self.steps)

    def as_dict(self) -> dict:
        return {
            "identity": self.identity.as_dict(),
            "steps": [s.as_dict() for s in self.steps],
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "dependencies": [d.as_dict() for d in self.dependencies],
        }


class WorkflowState(str, Enum):
    """State lifecycle deterministic workflow."""

    UNDEFINED = "undefined"
    VALIDATED = "validated"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


VALID_TRANSITIONS = {
    WorkflowState.UNDEFINED: {WorkflowState.VALIDATED},
    WorkflowState.VALIDATED: {WorkflowState.RUNNING},
    WorkflowState.RUNNING: {WorkflowState.COMPLETED, WorkflowState.FAILED},
    WorkflowState.COMPLETED: set(),
    WorkflowState.FAILED: set(),
}


@dataclass(frozen=True)
class WorkflowStateMachine:
    """State machine workflow deterministic."""

    workflow_id: str
    state: WorkflowState = WorkflowState.UNDEFINED

    def can_transition(self, target: WorkflowState) -> bool:
        return target in VALID_TRANSITIONS[self.state]

    def transition(self, target: WorkflowState) -> "WorkflowStateMachine":
        if not self.can_transition(target):
            raise ValueError(f"invalid transition {self.state} -> {target}")
        return WorkflowStateMachine(workflow_id=self.workflow_id, state=target)

    def as_dict(self) -> dict:
        return {"workflow_id": self.workflow_id, "state": self.state.value}


class WorkflowValidationResult:
    """Hasil validasi workflow."""

    def __init__(self, valid: bool, issues: Tuple[str, ...] = ()) -> None:
        self.valid = valid
        self.issues = issues

    def as_dict(self) -> dict:
        return {"valid": self.valid, "issues": list(self.issues)}


WORKFLOW_VALIDATION_STATE = WorkflowState  # alias re-export


class WorkflowValidator:
    """Validasi struktural & semantik workflow."""

    def validate(self, definition: WorkflowDefinition) -> WorkflowValidationResult:
        issues: list = []
        if not definition.identity.is_well_formed:
            issues.append("workflow identity malformed")
        step_ids = definition.step_ids()
        if not step_ids:
            issues.append("no steps defined")
        if len(set(step_ids)) != len(step_ids):
            issues.append("duplicate step ids")
        for dep in definition.dependencies:
            if dep.step_id not in step_ids:
                issues.append(f"dependency references unknown step {dep.step_id}")
            for parent in dep.depends_on:
                if parent not in step_ids:
                    issues.append(f"step {dep.step_id} depends on unknown step {parent}")
        if not definition.inputs and not definition.outputs:
            issues.append("no input/output contract declared")
        return WorkflowValidationResult(valid=not issues, issues=tuple(issues))


class WorkflowPersistence:
    """Repository sederhana untuk definition & state workflow."""

    def __init__(self) -> None:
        self._definitions: dict = {}
        self._states: dict = {}

    def save_definition(self, definition: WorkflowDefinition) -> None:
        self._definitions[definition.identity.workflow_id] = definition

    def load_definition(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        return self._definitions.get(workflow_id)

    def save_state(self, state: WorkflowStateMachine) -> None:
        self._states[state.workflow_id] = state

    def load_state(self, workflow_id: str) -> Optional[WorkflowStateMachine]:
        return self._states.get(workflow_id)


@dataclass(frozen=True)
class WorkflowTraceEntry:
    """Satu entri trace workflow."""

    step_id: str
    state: StepState
    note: str = ""

    def as_dict(self) -> dict:
        return {"step_id": self.step_id, "state": self.state.value, "note": self.note}


class WorkflowExplainer:
    """Menghasilkan penjelasan/trace workflow."""

    def explain(self, definition: WorkflowDefinition, trace: Tuple[WorkflowTraceEntry, ...] = ()) -> Dict[str, Any]:
        return {
            "workflow_id": definition.identity.workflow_id,
            "steps": list(definition.step_ids()),
            "dependencies": [d.as_dict() for d in definition.dependencies],
            "trace": [t.as_dict() for t in trace],
            "explainable": True,
        }


@dataclass(frozen=True)
class WorkflowComplianceResult:
    """Hasil compliance workflow foundation."""

    passed: bool
    checks: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)


class WorkflowComplianceChecker:
    """Checker compliance workflow."""

    def check(self, definition: WorkflowDefinition, *, deterministic=True, no_authority=True, governed=True, explainable=True, no_vendor_lockin=True) -> WorkflowComplianceResult:
        validator = WorkflowValidator().validate(definition).valid
        checks = [
            {"code": "VALID_DEFINITION", "passed": validator},
            {"code": "DETERMINISTIC", "passed": deterministic},
            {"code": "NO_AUTHORITY", "passed": no_authority},
            {"code": "GOVERNED", "passed": governed},
            {"code": "EXPLAINABLE", "passed": explainable},
            {"code": "NO_VENDOR_LOCKIN", "passed": no_vendor_lockin},
        ]
        return WorkflowComplianceResult(passed=all(c["passed"] for c in checks), checks=tuple(checks))

    def certify(self, definition: WorkflowDefinition, **kwargs: Any) -> Dict[str, Any]:
        result = self.check(definition, **kwargs)
        return {"component": "universal_workflow.foundation", "passed": result.passed, "certified": result.passed, "checks": [c for c in result.checks]}
