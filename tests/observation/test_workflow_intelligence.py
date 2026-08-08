"""Tests for C-Phase 3 (Workstream C2): Workflow Operational Intelligence.

Memverifikasi observer Workflow menghasilkan observasi operasional Workflow
(workflows, dependency graph, bottleneck) secara read-only, tanpa mutasi.
"""
from __future__ import annotations
import pytest

from sam.observation.publication import (
    PublicationAdapter,
    PublicationRegistry,
    RuntimePublication,
)
from sam.observation.workflow_intelligence import (
    Bottleneck,
    WorkflowBottleneckView,
    WorkflowDependencyGraph,
    WorkflowIntelligenceObserver,
    WorkflowIntelligenceReport,
    WorkflowStepDependency,
    WorkflowView,
)


# ── Fake WorkflowRegistry (read-only, untuk inject) ──

def _adapter_for(publication: RuntimePublication) -> PublicationAdapter:
    class _A(PublicationAdapter):
        def runtime_id(self) -> str:
            return publication.runtime_id
        def observe(self) -> RuntimePublication:
            return publication
    return _A()


def _pub_registry() -> PublicationRegistry:
    reg = PublicationRegistry()
    reg.register(_adapter_for(RuntimePublication(
        runtime_id="workflow",
        health_state="healthy",
        dashboard_count=9,
        metric_count=1,
        has_preview=True,
        has_metadata=True,
        has_lifecycle=False,
    )))
    return reg


class _FakeStep:
    def __init__(self, step_id, order, kind="compose", depends_on=()):
        self.step_id = step_id
        self.order = order
        self.kind = kind
        self.depends_on = list(depends_on)


class _FakeDescriptor:
    def __init__(self, id, name, steps=(), category="workflow", tags=(), runtimes=()):
        self.id = id
        self.name = name
        self.category = category
        self.description = ""
        self.tags = list(tags)
        self.integrated_runtimes = list(runtimes)
        self.steps = list(steps)


class _FakeRegistry:
    def __init__(self, descriptors):
        self._items = list(descriptors)
    def all(self):
        return list(self._items)
    def exists(self, workflow_id):
        return any(d.id == workflow_id for d in self._items)


def _wf_registry():
    return _FakeRegistry([
        _FakeDescriptor(
            "wf-1", "Mission Workflow",
            steps=[
                _FakeStep("s1", 0, "collect"),
                _FakeStep("s2", 1, "approve", depends_on=["s1"]),
                _FakeStep("s3", 2, "execute", depends_on=["s1"]),
            ],
            runtimes=["mission", "approval"],
        ),
    ])


class TestWorkflowViews:
    def test_lists_workflows(self):
        ob = WorkflowIntelligenceObserver(_pub_registry(), _wf_registry())
        wfs = ob.workflows()
        assert len(wfs) == 1
        assert isinstance(wfs[0], WorkflowView)
        assert wfs[0].workflow_id == "wf-1"
        assert wfs[0].name == "Mission Workflow"

    def test_step_count_from_descriptor(self):
        ob = WorkflowIntelligenceObserver(_pub_registry(), _wf_registry())
        wf = ob.workflows()[0]
        assert wf.step_count == 3


class TestWorkflowDependency:
    def test_dependency_graph_edges(self):
        ob = WorkflowIntelligenceObserver(_pub_registry(), _wf_registry())
        deps = ob.dependencies()
        assert len(deps) == 1
        g = deps[0]
        assert isinstance(g, WorkflowDependencyGraph)
        assert g.edge_count == 2  # s2->s1, s3->s1
        assert isinstance(g.steps[1], WorkflowStepDependency)
        assert list(g.steps[1].depends_on) == ["s1"]


class TestWorkflowBottleneck:
    def test_detects_fan_in_bottleneck(self):
        ob = WorkflowIntelligenceObserver(_pub_registry(), _wf_registry())
        b = ob.bottlenecks()
        assert isinstance(b, WorkflowBottleneckView)
        assert b.count == 1
        assert isinstance(b.bottlenecks[0], Bottleneck)
        # s1 paling banyak dijadikan dependency
        assert "s1" in b.bottlenecks[0].step_id


class TestWorkflowReport:
    def test_report_aggregates(self):
        ob = WorkflowIntelligenceObserver(_pub_registry(), _wf_registry())
        rep = ob.report()
        assert isinstance(rep, WorkflowIntelligenceReport)
        assert rep.total_workflows == 1
        d = rep.as_dict()
        assert d["total_workflows"] == 1


class TestWorkflowReadOnly:
    def test_pub_registry_unchanged(self):
        reg = _pub_registry()
        before = reg.observe_all().runtime_count
        ob = WorkflowIntelligenceObserver(reg, _wf_registry())
        ob.report(); ob.workflows(); ob.dependencies(); ob.bottlenecks()
        after = reg.observe_all().runtime_count
        assert before == after == 1
