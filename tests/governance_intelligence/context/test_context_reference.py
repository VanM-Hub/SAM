"""WP-16..17 - Context Resolution + Cross-Reference tests (IP-3.1-002).

Verifies ContextResolutionEngine produces a cross-domain GovernanceContext
and CrossReferenceEngine builds a deterministic ReferenceGraph.
"""

from __future__ import annotations

import pytest

from sam.governance_intelligence.knowledge.indexes import index_governance, index_mission
from sam.governance_intelligence.knowledge.loader import load_index
from sam.governance_intelligence.knowledge.repository import (
    ADRRepository,
    EvidenceRepository,
    MissionRepository,
    PolicyRepository,
    RuntimeRepository,
)
from sam.governance_intelligence.context import ContextResolutionEngine, GovernanceContext
from sam.governance_intelligence.reference_graph import CrossReferenceEngine, ReferenceGraph


def _fixtures():
    mission_text = (
        "# Mission\n\nGovern lifecycle with deterministic reasoning.\n\n"
        "# Objective\n\nProvide explainable governance.\n"
    )
    gov_text = (
        "# Approval\n\nApprove only with evidence.\n\n"
        "# Workflow Runtime\n\nWorkflow requires approval before execution.\n"
    )
    mission = MissionRepository(index_mission("docs/foundation/MISSION.md", mission_text))
    gov_idx = index_governance("docs/governance.md", gov_text)
    policy = PolicyRepository(gov_idx)
    runtime = RuntimeRepository(gov_idx)
    evidence = EvidenceRepository(load_index("evidence", "docs/foundation/MISSION.md", "evidence", mission_text))
    adr = ADRRepository(index_governance("docs/architecture/", "# ADR-001\n\nDecision.\n"))
    return mission, policy, runtime, evidence, adr


class TestContextResolution:
    def test_resolves_governance_context(self):
        mission, policy, runtime, evidence, adr = _fixtures()
        ctx: GovernanceContext = ContextResolutionEngine(
            mission, runtime, runtime, policy, evidence, adr
        ).resolve()
        assert isinstance(ctx, GovernanceContext)
        assert ctx.active_mission
        assert isinstance(ctx.active_policies, list)
        assert isinstance(ctx.evidence_availability, dict)
        assert isinstance(ctx.architectural_references, list)
        # readiness is one of the known levels
        assert ctx.readiness in ("LOW", "MEDIUM", "HIGH")

    def test_context_public_dict_stable(self):
        mission, policy, runtime, evidence, adr = _fixtures()
        ctx = ContextResolutionEngine(
            mission, runtime, runtime, policy, evidence, adr
        ).resolve()
        d = ctx.public_dict()
        assert set(d) == {
            "active_mission", "workflow_stage", "active_policies",
            "runtime_state", "readiness", "evidence_availability",
            "architectural_references",
        }


class TestCrossReference:
    def test_builds_reference_graph(self):
        mission, policy, runtime, evidence, adr = _fixtures()
        engine = CrossReferenceEngine(
            mission_items=mission.all(),
            workflow_items=runtime.all(),
            policy_items=policy.all(),
            evidence_items=evidence.all(),
            adr_items=adr.accepted(),
            recommendation_items=[],
        )
        graph: ReferenceGraph = engine.build()
        assert isinstance(graph, ReferenceGraph)
        assert isinstance(graph.nodes, tuple)
        # every node is namespaced by its layer
        for n in graph.nodes:
            assert ":" in n

    def test_graph_public_dict(self):
        mission, policy, runtime, evidence, adr = _fixtures()
        graph = CrossReferenceEngine(
            mission_items=mission.all(),
            workflow_items=runtime.all(),
            policy_items=policy.all(),
            evidence_items=evidence.all(),
            adr_items=adr.accepted(),
            recommendation_items=[],
        ).build()
        d = graph.public_dict()
        assert "nodes" in d and "edges" in d
