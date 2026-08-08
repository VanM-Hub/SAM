"""WP-27 + WP-28 - Evidence Navigation & Governance Relationship tests
(IP-3.1-003).

WP-27: operator can walk the evidence hierarchy
    Mission -> Workflow -> Policy -> Evidence -> ADR -> Architecture Order
    -> Decision  via EvidenceNavigationTree (model only, no UI).

WP-28: internal graph model DTO of governance relationships (no UI).
"""

from __future__ import annotations

from sam.governance_intelligence.knowledge.indexes import index_governance, index_mission
from sam.governance_intelligence.knowledge.loader import load_index
from sam.governance_intelligence.knowledge.repository import (
    ADRRepository,
    EvidenceRepository,
    MissionRepository,
    PolicyRepository,
    RuntimeRepository,
)
from sam.governance_intelligence.navigation import EvidenceNavigationEngine
from sam.governance_intelligence.relationship import GovernanceRelationshipEngine


def _build():
    mission_text = (
        "# Mission\n\nGovern lifecycle with deterministic reasoning.\n\n"
        "# Objective\n\nsafe, explainable operation gated by approval\n"
    )
    gov_text = (
        "# Approval Policy\n\nApprove only with evidence.\n\n"
        "# Workflow Runtime\n\nWorkflow stops without an approval gate.\n"
    )
    mission = MissionRepository(index_mission("docs/foundation/MISSION.md", mission_text))
    gov = index_governance("docs/governance.md", gov_text)
    policy = PolicyRepository(gov)
    runtime = RuntimeRepository(gov)
    evidence = EvidenceRepository(load_index("evidence", "docs/foundation/MISSION.md", "evidence", mission_text))
    adr = ADRRepository(index_governance("docs/architecture/", "# ADR-approval-gate\n\nApproval gating architecture.\n"))
    return mission, policy, runtime, evidence, adr


class TestEvidenceNavigation:
    def test_navigation_tree_built(self):
        mission, policy, runtime, evidence, adr = _build()
        engine = EvidenceNavigationEngine(mission, runtime, policy, evidence, adr, runtime)
        tree = engine.build()
        assert tree.root.layer == "Mission"
        assert tree.depth >= 2
        # at least one navigation path has a Policy child
        layers = [c.layer for c in tree.root.children]
        assert "Policy" in layers or "Workflow" in layers or "Runtime" in layers

    def test_navigation_public_dict_deterministic(self):
        mission, policy, runtime, evidence, adr = _build()
        engine = EvidenceNavigationEngine(mission, runtime, policy, evidence, adr, runtime)
        d1 = engine.build().public_dict()
        d2 = engine.build().public_dict()
        assert d1 == d2


class TestGovernanceRelationship:
    def test_graph_contains_expected_kinds(self):
        mission, policy, runtime, evidence, adr = _build()
        engine = GovernanceRelationshipEngine(mission, runtime, policy, runtime, evidence, adr)
        graph = engine.build()
        kinds = {n.kind for n in graph.nodes}
        # Mission, Workflow, Policy, Runtime, ADR should be present with seed data
        assert "Mission" in kinds
        assert "Policy" in kinds
        assert graph.edges  # at least some relationships

    def test_graph_is_model_dto(self):
        # Relationship Explorer emits a graph DTO, never a UI
        mission, policy, runtime, evidence, adr = _build()
        engine = GovernanceRelationshipEngine(mission, runtime, policy, runtime, evidence, adr)
        dto = engine.build()
        assert "nodes" in dto.public_dict()
        assert "edges" in dto.public_dict()
