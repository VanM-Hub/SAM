"""analyzers — WP-07/08/09 tests (IP-3.1-001)."""

from sam.governance_intelligence.analyzers.mission import MissionAnalyzer
from sam.governance_intelligence.analyzers.workflow import WorkflowAnalyzer
from sam.governance_intelligence.analyzers.runtime import RuntimeAnalyzer
from sam.governance_intelligence.knowledge.indexes import index_governance
from sam.governance_intelligence.knowledge.repository import PolicyRepository, RuntimeRepository


def test_mission_analyzer(mission_repo, evidence_repo):
    a = MissionAnalyzer(mission_repo)
    s = a.summarize()
    assert "SAM" in s.mission or s.mission
    assert a.intent().confidence in (0.0, 1.0)
    assert isinstance(a.constraints().declared, bool)
    r = a.readiness()
    assert isinstance(r.ready, bool)


def test_workflow_analyzer():
    idx = index_governance("docs/governance.md", "# Workflow Runtime\nstep\n# Policy Approval\nx\n")
    wf = RuntimeRepository(idx)  # workflow items are runtime-facet here by keyword
    pol = PolicyRepository(idx)
    a = WorkflowAnalyzer(wf, pol)
    out = a.analyze("Runtime", ["Approval Gate"])
    assert out.current_stage == "Runtime"
    assert isinstance(out.public_dict(), dict)


def test_runtime_analyzer():
    idx = index_governance("docs/governance.md", "# Workflow Runtime\ndepends on X\n")
    rt = RuntimeRepository(idx)
    from sam.governance_intelligence.knowledge.repository import EvidenceRepository
    a = RuntimeAnalyzer(rt, EvidenceRepository(idx))
    out = a.analyze("Runtime")
    assert out.capability == "Runtime"
    assert isinstance(out.health, str)
