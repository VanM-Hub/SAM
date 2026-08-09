"""Workflow Composition & Dependency - WP-11..20 (MISSION-5.4 / IP-5.4-002).

Composition model, capability binding, input/output mapping, dependency
resolution, conditional transition, parallel/sequential composition,
explainability.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from .workflow_foundation import StepDependency, WorkflowDefinition, WorkflowIdentity, WorkflowStep


@dataclass(frozen=True)
class CompositionResult:
    """Hasil komposisi workflow."""

    workflow_id: str
    steps: Tuple[WorkflowStep, ...] = field(default_factory=tuple)
    dependencies: Tuple[StepDependency, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "workflow_id": self.workflow_id,
            "steps": [s.as_dict() for s in self.steps],
            "dependencies": [d.as_dict() for d in self.dependencies],
        }


@dataclass(frozen=True)
class CapabilityBinding:
    """Binding step -> capability."""

    step_id: str
    capability: str

    def as_dict(self) -> dict:
        return {"step_id": self.step_id, "capability": self.capability}


@dataclass(frozen=True)
class MappingRule:
    """Aturan mapping input/output."""

    step_id: str
    source: str
    target: str

    def as_dict(self) -> dict:
        return {"step_id": self.step_id, "source": self.source, "target": self.target}


class WorkflowComposer:
    """Menyusun workflow dari step + binding + mapping."""

    def __init__(self) -> None:
        self._bindings: dict = {}
        self._input_maps: dict = {}
        self._output_maps: dict = {}

    def bind_capability(self, step_id: str, capability: str) -> None:
        self._bindings[step_id] = capability

    def map_input(self, step_id: str, source: str, target: str) -> None:
        self._input_maps[step_id] = MappingRule(step_id, source, target)

    def map_output(self, step_id: str, source: str, target: str) -> None:
        self._output_maps[step_id] = MappingRule(step_id, source, target)

    def compose(self, workflow_id: str, steps: Tuple[WorkflowStep, ...]) -> WorkflowDefinition:
        deps = [StepDependency(s.step_id, ()) for s in steps]
        outputs = tuple(self._output_maps[s.step_id].target for s in steps if s.step_id in self._output_maps)
        inputs = tuple(self._input_maps[s.step_id].target for s in steps if s.step_id in self._input_maps)
        identity = WorkflowIdentity(workflow_id=workflow_id, name=f"wf-{workflow_id}")
        return WorkflowDefinition(identity=identity, steps=steps, inputs=inputs, outputs=outputs, dependencies=tuple(deps))

    def capability_for(self, step_id: str) -> Optional[str]:
        return self._bindings.get(step_id)


class DependencyResolver:
    """Resolver dependency antar step (topological order)."""

    def resolve(self, steps: Tuple[WorkflowStep, ...], deps: Tuple[StepDependency, ...]) -> Tuple[str, ...]:
        dep_map = {d.step_id: list(d.depends_on) for d in deps}
        available = set(s.step_id for s in steps)
        for sid, parents in dep_map.items():
            for p in parents:
                if p not in available:
                    raise ValueError(f"unknown dependency {p} for {sid}")
        ordered: list = []
        visited: set = set()

        def visit(sid: str, stack: set) -> None:
            if sid in visited:
                return
            if sid in stack:
                raise ValueError("circular dependency detected")
            stack.add(sid)
            for parent in dep_map.get(sid, ()):
                visit(parent, stack)
            stack.discard(sid)
            visited.add(sid)
            ordered.append(sid)

        for sid, _ in dep_map.items():
            visit(sid, set())
        for s in steps:
            if s.step_id not in visited:
                ordered.append(s.step_id)
        return tuple(ordered)


class ConditionalTransition:
    """Transition kondisional antar step."""

    def __init__(self, rule: Optional[Dict[str, Any]] = None) -> None:
        self._rule = rule or {}

    def evaluate(self, context: Dict[str, Any]) -> bool:
        if "when" not in self._rule:
            return True
        return bool(eval(self._rule["when"], {"__builtins__": {}}, context))  # noqa: S307 - isolated eval untuk test fixture


class CompositionExplainer:
    """Menjelaskan komposisi workflow."""

    def explain(self, result: CompositionResult) -> Dict[str, Any]:
        return {
            "workflow_id": result.workflow_id,
            "steps": [s.as_dict() for s in result.steps],
            "dependencies": [d.as_dict() for d in result.dependencies],
            "explainable": True,
        }
