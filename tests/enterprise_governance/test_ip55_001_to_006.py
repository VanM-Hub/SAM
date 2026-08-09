"""Test MISSION-5.5 - Enterprise Governance (IP-5.5-001..006).

Coverage: WP-01..WP-60 - organization foundation, multi-tenant, policy &
delegation, audit & intelligence, workspace, certification.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.enterprise_governance import (
    AuditTrail,
    DelegationRegistry,
    DelegationRule,
    EnterpriseCertification,
    EnterpriseCertStatus,
    EnterprisePolicy,
    EnterpriseWorkspace,
    GovernanceEntity,
    GovernanceIntelligence,
    GovEntityKind,
    MultiTenantComplianceChecker,
    OrgComplianceChecker,
    OrganizationRegistry,
    PolicyComplianceChecker,
    PolicyConflictResolver,
    PolicyEffect,
    PolicyVersioning,
    TenantRegistry,
    AuditComplianceChecker,
    WorkspaceComplianceChecker,
)


def _org():
    return GovernanceEntity(entity_id="org-1", name="Acme", kind=GovEntityKind.ORGANIZATION)


class TestOrgFoundation:
    def test_register_context(self):
        registry = OrganizationRegistry()
        registry.register(_org())
        ctx = registry.context("org-1")
        assert ctx.preserves_local_authority is True
        assert registry.validate_registry() is True

    def test_org_compliance(self):
        registry = OrganizationRegistry()
        registry.register(_org())
        assert OrgComplianceChecker().check(registry)["certified"] is True
        assert OrgComplianceChecker().check(registry, sovereignty=False)["certified"] is False


class TestMultitenant:
    def test_tenancy(self):
        registry = OrganizationRegistry()
        registry.register(_org())
        tenants = TenantRegistry()
        tenant = tenants.register(_org(), "t1", "Tenant A")
        assert tenant.is_isolated is True
        assert tenants.validate_isolation() is True

    def test_tenant_compliance(self):
        registry = OrganizationRegistry()
        registry.register(_org())
        tenants = TenantRegistry()
        tenants.register(_org(), "t1", "Tenant A")
        assert MultiTenantComplianceChecker().check(tenants)["certified"] is True


class TestPolicyDelegation:
    def test_versioning_precedence(self):
        v = PolicyVersioning()
        v.register(EnterprisePolicy("p1", "policy", effect=PolicyEffect.ALLOW, version=1))
        v.register(EnterprisePolicy("p1", "policy", effect=PolicyEffect.DENY, version=2))
        assert len(v.history("p1")) == 2
        assert PolicyConflictResolver().resolve(v.history("p1")) == PolicyEffect.DENY

    def test_delegation_boundary(self):
        reg = DelegationRegistry()
        reg.grant(DelegationRule("d1", "alice", "scope:read", authority_limited=True, revocable=True))
        assert len(reg.valid_delegations()) == 1

    def test_policy_compliance(self):
        assert PolicyComplianceChecker().check()["certified"] is True
        assert PolicyComplianceChecker().check(revocable=False)["certified"] is False


class TestAuditIntelligence:
    def test_audit_trail(self):
        trail = AuditTrail()
        trail.record("org-1", "policy.created")
        assert len(trail.events()) == 1
        assert len(trail.for_entity("org-1")) == 1

    def test_intelligence_observation(self):
        trail = AuditTrail()
        trail.record("org-1", "drift")
        intelligence = GovernanceIntelligence(trail)
        status = intelligence.observed_status("org-1", policy_count=2)
        assert status.drift is True
        assert intelligence.observe_only() is True

    def test_audit_compliance(self):
        assert AuditComplianceChecker().check()["certified"] is True


class TestWorkspace:
    def test_workspace(self):
        orgs = OrganizationRegistry()
        orgs.register(_org())
        tenants = TenantRegistry()
        tenants.register(_org(), "t1", "Tenant A")
        trail = AuditTrail()
        intelligence = GovernanceIntelligence(trail)
        ws = EnterpriseWorkspace(orgs, tenants, trail, intelligence)
        assert len(ws.list_entities()) == 1
        assert len(ws.tenant_overview()) == 1
        assert ws.governance_status("t1").entity_id == "t1"
        assert WorkspaceComplianceChecker().check()["certified"] is True


class TestCertification:
    def test_full_certified(self):
        cert = EnterpriseCertification()
        cert.foundation_certification()
        cert.multitenant_certification()
        cert.policy_certification()
        cert.audit_certification()
        cert.workspace_certification()
        cert.governance_certification()
        cert.isolation_certification()
        cert.regression_compliance()
        cert.mission_certification()
        result = cert.certify()
        assert result["certified"] is True
        assert result["status"] == EnterpriseCertStatus.CERTIFIED.value

    def test_not_certified(self):
        cert = EnterpriseCertification()
        cert.isolation_certification(isolated=False, no_cross_tenant=False)
        cert.governance_certification(no_execution_authority=False, authority_boundary=False)
        assert cert.certify()["status"] == EnterpriseCertStatus.NOT_CERTIFIED.value
