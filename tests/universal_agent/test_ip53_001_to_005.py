"""Test MISSION-5.3 - Universal Agent Integration (IP-5.3-001..005).

Coverage: WP-01..WP-50 - foundation, contract framework, collaboration,
workspace, certification.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.universal_agent import (
    AgentAPI,
    AgentCapability,
    AgentCapabilityKind,
    AgentCapabilityResolver,
    AgentCertification,
    AgentCertStatus,
    AgentComplianceChecker,
    AgentContractComplianceChecker,
    AgentDescriptor,
    AgentDiscovery,
    AgentHealthCheck,
    AgentIdentity,
    AgentInteractionContract,
    AgentLifecycleState,
    AgentRegistry,
    AgentResponse,
    AgentResultState,
    AgentWorkspace,
    CollaborationComplianceChecker,
    CollaborationManager,
    InteroperabilityChecker,
    InteroperabilityState,
)


def _agent(aid="agent-1", name="Researcher"):
    return AgentIdentity(agent_id=aid, name=name)


class TestFoundation:
    def test_identity_registry(self):
        registry = AgentRegistry()
        registry.register(_agent(), availability=True)
        assert registry.lookup("agent-1") is not None
        assert registry.size() == 1
        assert registry.validate_registry() is True

    def test_descriptor_capability(self):
        desc = AgentDescriptor(identity=_agent(), capabilities=(AgentCapability(AgentCapabilityKind.ANALYZE),))
        assert desc.capability(AgentCapabilityKind.ANALYZE) is not None

    def test_discovery(self):
        registry = AgentRegistry()
        registry.register(_agent())
        discovery = AgentDiscovery(registry, (AgentDescriptor(identity=_agent(), capabilities=(AgentCapability(AgentCapabilityKind.RESEARCH),)),))
        assert len(discovery.discover_by_capability(AgentCapabilityKind.RESEARCH)) == 1

    def test_health(self):
        assert AgentHealthCheck().assess("agent-1").healthy is True

    def test_api(self):
        api = AgentAPI()
        api.register(_agent())
        assert api.lookup("agent-1") is not None
        assert api.activate("agent-1").state == AgentLifecycleState.ACTIVE
        assert api.health("agent-1").healthy is True

    def test_compliance(self):
        registry = AgentRegistry()
        registry.register(_agent())
        assert AgentComplianceChecker().certify(registry)["certified"] is True
        assert AgentComplianceChecker().certify(registry, no_authority=False)["certified"] is False


class TestContractFramework:
    def test_capability_resolution(self):
        contract = AgentInteractionContract(agent_id="agent-1", contract_id="c1", capabilities=(AgentCapabilityKind.ANALYZE,))
        resolver = AgentCapabilityResolver((contract,))
        assert resolver.resolve("agent-1", AgentCapabilityKind.ANALYZE).resolved is True
        assert resolver.resolve("agent-1", AgentCapabilityKind.EXECUTE).resolved is False

    def test_interoperability(self):
        a = AgentInteractionContract(agent_id="a", contract_id="c1", capabilities=(AgentCapabilityKind.ANALYZE,))
        b = AgentInteractionContract(agent_id="b", contract_id="c2", capabilities=(AgentCapabilityKind.ANALYZE,))
        c = AgentInteractionContract(agent_id="c", contract_id="c3", capabilities=(AgentCapabilityKind.EXECUTE,))
        checker = InteroperabilityChecker()
        assert checker.check(a, b).state == InteroperabilityState.COMPATIBLE
        assert checker.check(a, c).state == InteroperabilityState.INCOMPATIBLE

    def test_contract_compliance(self):
        assert AgentContractComplianceChecker().certify()["certified"] is True


class TestCollaboration:
    def test_full_governed_collaboration(self):
        mgr = CollaborationManager()
        proposal = mgr.propose("agent-1", "agent-2", AgentCapabilityKind.COORDINATE)
        mgr.negotiate(proposal.collaboration_id, accepted=True)
        record = mgr.approve(proposal.collaboration_id, evidence_refs=("e1",))
        assert record.approved is True
        assert record.governed is True
        record = mgr.complete(
            proposal.collaboration_id,
            (AgentResponse(request_id="r1", agent_id="agent-2", state=AgentResultState.SUCCESS),),
        )
        assert len(record.responses) == 1
        cert = CollaborationComplianceChecker().certify(record)
        assert cert["certified"] is True

    def test_collaboration_requires_approval(self):
        mgr = CollaborationManager()
        proposal = mgr.propose("agent-1", "agent-2", AgentCapabilityKind.COORDINATE)
        mgr.negotiate(proposal.collaboration_id)
        # tidak approve -> governed false saat ada response
        record = mgr._records[proposal.collaboration_id]
        # simulasi response tanpa approval

        bad = mgr.complete(proposal.collaboration_id, (AgentResponse(request_id="r", agent_id="a"),))
        # approve tidak pernah -> approved False tapi complete memungkinkan -> compliance harus menangkap
        cert = CollaborationComplianceChecker().certify(bad)
        assert cert["checks"][1]["passed"] is False  # APPROVED_BEFORE_EXECUTION


class TestWorkspaceAndCert:
    def test_workspace(self):
        from sam.universal_agent import AgentLifecycleManager

        registry = AgentRegistry()
        registry.register(_agent())
        discovery = AgentDiscovery(registry)
        workspace = AgentWorkspace(
            registry, discovery, AgentHealthCheck(), AgentLifecycleManager(), CollaborationManager()
        )
        assert workspace.investigate("agent-1").summary != ""

    def test_certification(self):
        cert = AgentCertification()
        cert.identity_certification()
        cert.contract_certification()
        cert.capability_certification()
        cert.collaboration_certification()
        cert.execution_certification()
        cert.security_verification()
        cert.governance_verification()
        cert.audit_verification()
        cert.regression_production()
        cert.mission_certification()
        result = cert.certify()
        assert result["certified"] is True
        assert result["status"] == AgentCertStatus.CERTIFIED.value
