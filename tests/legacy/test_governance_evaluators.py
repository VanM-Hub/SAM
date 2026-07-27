"""
Test Governance Evaluators – Sprint 21 Fase 2

Covers all 7 evaluators:
- RiskEvaluator
- ApprovalEvaluator
- MaintenanceEvaluator
- ClusterEvaluator
- ResourceEvaluator
- CapabilityEvaluator
- PolicyEvaluator
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from src.sam.governance.models import GovernanceDecision, GovernanceResult, GovernanceRule
from src.sam.governance.evaluators.risk import RiskEvaluator
from src.sam.governance.evaluators.approval import ApprovalEvaluator
from src.sam.governance.evaluators.maintenance import MaintenanceEvaluator
from src.sam.governance.evaluators.cluster import ClusterEvaluator
from src.sam.governance.evaluators.resource import ResourceEvaluator
from src.sam.governance.evaluators.capability import CapabilityEvaluator
from src.sam.governance.evaluators.policy import PolicyEvaluator


# ── Test Helpers ─────────────────────────────────────────────────


class _Graph:
    """Minimal graph mock with metadata."""

    def __init__(self, id: str = "g-1", name: str = "test", metadata: Optional[Dict] = None):
        self.id = id
        self.name = name
        self.metadata = metadata or {}


class _Context:
    """Minimal execution context mock."""

    def __init__(self):
        self.execution_id = "exec-1"


def _g(metadata: Optional[Dict] = None) -> _Graph:
    return _Graph(metadata=metadata)


def _c() -> _Context:
    return _Context()


# ── 1. RiskEvaluator ─────────────────────────────────────────────


class TestRiskEvaluator:
    @pytest.mark.asyncio
    async def test_allow_low_risk(self):
        ev = RiskEvaluator()
        r = await ev.evaluate(_g({"risk_score": 0.2}), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_allow_no_risk_score(self):
        ev = RiskEvaluator()
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_allow_with_warning_moderate(self):
        ev = RiskEvaluator()
        r = await ev.evaluate(_g({"risk_score": 0.4}), _c())
        assert r.decision == GovernanceDecision.ALLOW_WITH_WARNING
        assert r.is_allowed()

    @pytest.mark.asyncio
    async def test_require_approval_high(self):
        ev = RiskEvaluator()
        r = await ev.evaluate(_g({"risk_score": 0.6}), _c())
        assert r.decision == GovernanceDecision.REQUIRE_APPROVAL
        assert r.is_blocked()

    @pytest.mark.asyncio
    async def test_reject_critical(self):
        ev = RiskEvaluator()
        r = await ev.evaluate(_g({"risk_score": 0.8}), _c())
        assert r.decision == GovernanceDecision.REJECT

    @pytest.mark.asyncio
    async def test_requires_approval_flag(self):
        ev = RiskEvaluator()
        r = await ev.evaluate(
            _g({"requires_approval": True, "approval_groups": ["security"]}), _c()
        )
        assert r.decision == GovernanceDecision.REQUIRE_APPROVAL
        assert "security" in r.required_approvals

    @pytest.mark.asyncio
    async def test_approval_overrides_risk(self):
        """requires_approval flag triggers even when risk_score is low."""
        ev = RiskEvaluator()
        r = await ev.evaluate(
            _g({"risk_score": 0.1, "requires_approval": True}), _c()
        )
        assert r.decision == GovernanceDecision.REQUIRE_APPROVAL


# ── 2. ApprovalEvaluator ─────────────────────────────────────────


class TestApprovalEvaluator:
    @pytest.mark.asyncio
    async def test_no_approval_required(self):
        ev = ApprovalEvaluator()
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_requires_approval(self):
        ev = ApprovalEvaluator()
        r = await ev.evaluate(
            _g({"requires_approval": True, "approval_groups": ["ops", "dev"]}), _c()
        )
        assert r.decision == GovernanceDecision.REQUIRE_APPROVAL
        assert r.required_approvals == ["ops", "dev"]

    @pytest.mark.asyncio
    async def test_requires_approval_default_group(self):
        ev = ApprovalEvaluator()
        r = await ev.evaluate(_g({"requires_approval": True}), _c())
        assert r.decision == GovernanceDecision.REQUIRE_APPROVAL
        assert "default-approvers" in r.required_approvals

    @pytest.mark.asyncio
    async def test_sensitive_targets(self):
        ev = ApprovalEvaluator()
        r = await ev.evaluate(
            _g({"sensitive_targets": ["production-db", "user-pii"]}), _c()
        )
        assert r.decision == GovernanceDecision.REQUIRE_APPROVAL
        assert "security-team" in r.required_approvals

    @pytest.mark.asyncio
    async def test_sensitive_and_approval(self):
        """When both requires_approval and sensitive_targets, takes first match."""
        ev = ApprovalEvaluator()
        r = await ev.evaluate(
            _g({
                "requires_approval": True,
                "approval_groups": ["custom-team"],
                "sensitive_targets": ["prod"],
            }),
            _c(),
        )
        # requires_approval is checked first
        assert r.decision == GovernanceDecision.REQUIRE_APPROVAL


# ── 3. MaintenanceEvaluator ──────────────────────────────────────


class TestMaintenanceEvaluator:

    @pytest.mark.asyncio
    async def test_no_maintenance(self):
        ev = MaintenanceEvaluator()
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_maintenance_ends_at_future(self):
        future = (datetime.utcnow() + timedelta(hours=2)).isoformat()
        ev = MaintenanceEvaluator()
        r = await ev.evaluate(_g({"maintenance_ends_at": future}), _c())
        assert r.decision == GovernanceDecision.WAIT
        assert r.suggested_delay and r.suggested_delay > 0

    @pytest.mark.asyncio
    async def test_maintenance_ends_at_past(self):
        past = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        ev = MaintenanceEvaluator()
        r = await ev.evaluate(_g({"maintenance_ends_at": past}), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_cluster_maintenance_windows_active(self):
        future = (datetime.utcnow() + timedelta(hours=2)).isoformat()
        past = (datetime.utcnow() - timedelta(hours=1)).isoformat()

        def windows():
            return [{"start": past, "end": future, "reason": "routine"}]

        ev = MaintenanceEvaluator(maintenance_windows=windows)
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.WAIT

    @pytest.mark.asyncio
    async def test_cluster_maintenance_windows_inactive(self):
        p1 = (datetime.utcnow() - timedelta(hours=3)).isoformat()
        p2 = (datetime.utcnow() - timedelta(hours=2)).isoformat()

        def windows():
            return [{"start": p1, "end": p2, "reason": "done"}]

        ev = MaintenanceEvaluator(maintenance_windows=windows)
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_maintenance_flag_active(self):
        ev = MaintenanceEvaluator(is_maintenance_active=lambda: True)
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.WAIT
        assert r.suggested_delay == 600

    @pytest.mark.asyncio
    async def test_maintenance_flag_inactive(self):
        ev = MaintenanceEvaluator(is_maintenance_active=lambda: False)
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_invalid_ends_at_does_not_crash(self):
        ev = MaintenanceEvaluator()
        r = await ev.evaluate(_g({"maintenance_ends_at": "not-a-date"}), _c())
        assert r.decision == GovernanceDecision.ALLOW


# ── 4. ClusterEvaluator ──────────────────────────────────────────


class TestClusterEvaluator:

    @pytest.mark.asyncio
    async def test_no_cluster_info_allows(self):
        ev = ClusterEvaluator()
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_insufficient_nodes(self):
        ev = ClusterEvaluator(
            get_online_node_count=lambda: 0,
            get_minimum_online_nodes=lambda: 1,
        )
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.WAIT

    @pytest.mark.asyncio
    async def test_sufficient_nodes(self):
        ev = ClusterEvaluator(
            get_online_node_count=lambda: 3,
            get_minimum_online_nodes=lambda: 1,
        )
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_load_reject(self):
        ev = ClusterEvaluator(
            get_cluster_load=lambda: 95.0,
        )
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.REJECT

    @pytest.mark.asyncio
    async def test_load_wait(self):
        ev = ClusterEvaluator(
            get_cluster_load=lambda: 75.0,
        )
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.WAIT

    @pytest.mark.asyncio
    async def test_load_ok(self):
        ev = ClusterEvaluator(
            get_cluster_load=lambda: 30.0,
        )
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_custom_thresholds(self):
        ev = ClusterEvaluator(
            get_cluster_load=lambda: 85.0,
            reject_load_threshold=95.0,
            wait_load_threshold=80.0,
        )
        # 85% > 80% wait, < 95% reject
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.WAIT

    @pytest.mark.asyncio
    async def test_graph_min_nodes_not_met(self):
        ev = ClusterEvaluator(
            get_online_node_count=lambda: 1,
        )
        r = await ev.evaluate(_g({"min_online_nodes": 3}), _c())
        assert r.decision == GovernanceDecision.WAIT


# ── 5. ResourceEvaluator ─────────────────────────────────────────


class TestResourceEvaluator:

    @pytest.mark.asyncio
    async def test_no_requirements(self):
        ev = ResourceEvaluator()
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_memory_sufficient(self):
        ev = ResourceEvaluator(get_available_memory_mb=lambda: 4096.0)
        r = await ev.evaluate(_g({"required_memory_mb": 2048}), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_memory_insufficient(self):
        ev = ResourceEvaluator(get_available_memory_mb=lambda: 512.0)
        r = await ev.evaluate(_g({"required_memory_mb": 2048}), _c())
        assert r.decision == GovernanceDecision.WAIT

    @pytest.mark.asyncio
    async def test_memory_unavailable(self):
        ev = ResourceEvaluator(get_available_memory_mb=lambda: -1.0)
        r = await ev.evaluate(_g({"required_memory_mb": 2048}), _c())
        assert r.decision == GovernanceDecision.REJECT

    @pytest.mark.asyncio
    async def test_cpu_sufficient(self):
        ev = ResourceEvaluator(get_available_cpu_cores=lambda: 8.0)
        r = await ev.evaluate(_g({"required_cpu_cores": 4}), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_cpu_insufficient(self):
        ev = ResourceEvaluator(get_available_cpu_cores=lambda: 1.0)
        r = await ev.evaluate(_g({"required_cpu_cores": 4}), _c())
        assert r.decision == GovernanceDecision.WAIT

    @pytest.mark.asyncio
    async def test_disk_sufficient(self):
        ev = ResourceEvaluator(get_available_disk_mb=lambda: 100000.0)
        r = await ev.evaluate(_g({"required_disk_mb": 50000}), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_disk_insufficient(self):
        ev = ResourceEvaluator(get_available_disk_mb=lambda: 1000.0)
        r = await ev.evaluate(_g({"required_disk_mb": 50000}), _c())
        assert r.decision == GovernanceDecision.WAIT

    @pytest.mark.asyncio
    async def test_multiple_resources_all_ok(self):
        ev = ResourceEvaluator(
            get_available_memory_mb=lambda: 8192.0,
            get_available_cpu_cores=lambda: 16.0,
            get_available_disk_mb=lambda: 500000.0,
        )
        r = await ev.evaluate(
            _g({"required_memory_mb": 4096, "required_cpu_cores": 8, "required_disk_mb": 100000}),
            _c(),
        )
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_multiple_resources_one_fails(self):
        ev = ResourceEvaluator(
            get_available_memory_mb=lambda: 512.0,
            get_available_cpu_cores=lambda: 16.0,
        )
        r = await ev.evaluate(
            _g({"required_memory_mb": 4096, "required_cpu_cores": 8}),
            _c(),
        )
        assert r.decision == GovernanceDecision.WAIT

    @pytest.mark.asyncio
    async def test_resource_status_fallback(self):
        def status():
            return {"memory": 1024.0, "cpu": 2.0, "disk": 50000.0}

        ev = ResourceEvaluator(get_resource_status=status)
        r = await ev.evaluate(
            _g({"required_memory_mb": 4096}),
            _c(),
        )
        assert r.decision == GovernanceDecision.WAIT


# ── 6. CapabilityEvaluator ───────────────────────────────────────


class TestCapabilityEvaluator:

    @pytest.mark.asyncio
    async def test_no_requirements(self):
        ev = CapabilityEvaluator()
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_all_healthy(self):
        def caps():
            return {"ocr": "healthy", "nlp": "healthy"}

        ev = CapabilityEvaluator(get_capabilities=caps)
        r = await ev.evaluate(_g({"required_capabilities": ["ocr", "nlp"]}), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_missing_capability(self):
        def caps():
            return {"ocr": "healthy"}

        ev = CapabilityEvaluator(get_capabilities=caps)
        r = await ev.evaluate(_g({"required_capabilities": ["ocr", "nlp"]}), _c())
        assert r.decision == GovernanceDecision.REJECT

    @pytest.mark.asyncio
    async def test_unhealthy_capability(self):
        def caps():
            return {"ocr": "unhealthy", "nlp": "healthy"}

        ev = CapabilityEvaluator(get_capabilities=caps)
        r = await ev.evaluate(_g({"required_capabilities": ["ocr", "nlp"]}), _c())
        assert r.decision == GovernanceDecision.REJECT

    @pytest.mark.asyncio
    async def test_degraded_capability(self):
        def caps():
            return {"ocr": "degraded", "nlp": "healthy"}

        ev = CapabilityEvaluator(get_capabilities=caps)
        r = await ev.evaluate(_g({"required_capabilities": ["ocr", "nlp"]}), _c())
        assert r.decision == GovernanceDecision.ALLOW_WITH_WARNING

    @pytest.mark.asyncio
    async def test_no_capability_source_allows(self):
        """If no get_capabilities provided, allow (defer to runtime)."""
        ev = CapabilityEvaluator()
        r = await ev.evaluate(_g({"required_capabilities": ["ocr"]}), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_custom_required_capabilities(self):
        def caps():
            return {"a": "healthy", "b": "healthy", "c": "healthy"}

        def required(_graph):
            return ["a", "b"]

        ev = CapabilityEvaluator(get_capabilities=caps, get_required_capabilities=required)
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.ALLOW


# ── 7. PolicyEvaluator ───────────────────────────────────────────


class TestPolicyEvaluator:

    @pytest.mark.asyncio
    async def test_no_rules_allows(self):
        ev = PolicyEvaluator()
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_no_policy_rules_allows(self):
        """Only non-POLICY rules, no match."""
        ev = PolicyEvaluator(
            get_rules=lambda: [
                GovernanceRule(id="r1", name="Risk Rule", evaluator_type="RISK"),
            ]
        )
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_disabled_rule_ignored(self):
        ev = PolicyEvaluator(
            get_rules=lambda: [
                GovernanceRule(
                    id="r1", name="Block", evaluator_type="POLICY",
                    condition="production=true", decision_override=GovernanceDecision.REJECT,
                    enabled=False,
                ),
            ]
        )
        r = await ev.evaluate(_g({"production": True}), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_condition_met_key_exists(self):
        ev = PolicyEvaluator(
            get_rules=lambda: [
                GovernanceRule(
                    id="r1", name="Test Rule", evaluator_type="POLICY",
                    condition="flag", decision_override=GovernanceDecision.WAIT,
                ),
            ]
        )
        r = await ev.evaluate(_g({"flag": True}), _c())
        assert r.decision == GovernanceDecision.WAIT

    @pytest.mark.asyncio
    async def test_condition_not_met(self):
        ev = PolicyEvaluator(
            get_rules=lambda: [
                GovernanceRule(
                    id="r1", name="Test Rule", evaluator_type="POLICY",
                    condition="flag", decision_override=GovernanceDecision.WAIT,
                ),
            ]
        )
        r = await ev.evaluate(_g({"flag": False}), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_condition_equals(self):
        ev = PolicyEvaluator(
            get_rules=lambda: [
                GovernanceRule(
                    id="r1", name="Env Check", evaluator_type="POLICY",
                    condition="environment=production",
                    decision_override=GovernanceDecision.REQUIRE_APPROVAL,
                ),
            ]
        )
        r = await ev.evaluate(_g({"environment": "production"}), _c())
        assert r.decision == GovernanceDecision.REQUIRE_APPROVAL

    @pytest.mark.asyncio
    async def test_condition_not_equals(self):
        ev = PolicyEvaluator(
            get_rules=lambda: [
                GovernanceRule(
                    id="r1", name="Env Check", evaluator_type="POLICY",
                    condition="environment!=production",
                    decision_override=GovernanceDecision.REJECT,
                ),
            ]
        )
        r = await ev.evaluate(_g({"environment": "production"}), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_condition_negation(self):
        ev = PolicyEvaluator(
            get_rules=lambda: [
                GovernanceRule(
                    id="r1", name="No Approval", evaluator_type="POLICY",
                    condition="!approved", decision_override=GovernanceDecision.REQUIRE_APPROVAL,
                ),
            ]
        )
        r = await ev.evaluate(_g({}), _c())
        assert r.decision == GovernanceDecision.REQUIRE_APPROVAL

    @pytest.mark.asyncio
    async def test_numeric_comparison(self):
        ev = PolicyEvaluator(
            get_rules=lambda: [
                GovernanceRule(
                    id="r1", name="Version Check", evaluator_type="POLICY",
                    condition="version=2.0",
                    decision_override=GovernanceDecision.ALLOW,
                ),
            ]
        )
        r = await ev.evaluate(_g({"version": 2.0}), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_boolean_true(self):
        ev = PolicyEvaluator(
            get_rules=lambda: [
                GovernanceRule(
                    id="r1", name="Bool True", evaluator_type="POLICY",
                    condition="dry_run=true",
                    decision_override=GovernanceDecision.WAIT,
                ),
            ]
        )
        r = await ev.evaluate(_g({"dry_run": True}), _c())
        assert r.decision == GovernanceDecision.WAIT

    @pytest.mark.asyncio
    async def test_boolean_false(self):
        ev = PolicyEvaluator(
            get_rules=lambda: [
                GovernanceRule(
                    id="r1", name="Bool False", evaluator_type="POLICY",
                    condition="dry_run=false",
                    decision_override=GovernanceDecision.WAIT,
                ),
            ]
        )
        r = await ev.evaluate(_g({"dry_run": True}), _c())
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_most_restrictive_wins(self):
        """Multiple rules match — most restrictive decision wins."""
        ev = PolicyEvaluator(
            get_rules=lambda: [
                GovernanceRule(
                    id="r1", name="Warn", evaluator_type="POLICY",
                    condition="flag", decision_override=GovernanceDecision.ALLOW_WITH_WARNING,
                ),
                GovernanceRule(
                    id="r2", name="Reject", evaluator_type="POLICY",
                    condition="flag", decision_override=GovernanceDecision.REJECT,
                ),
            ]
        )
        r = await ev.evaluate(_g({"flag": True}), _c())
        assert r.decision == GovernanceDecision.REJECT

    @pytest.mark.asyncio
    async def test_escalate_wins_over_reject(self):
        ev = PolicyEvaluator(
            get_rules=lambda: [
                GovernanceRule(
                    id="r1", name="Reject", evaluator_type="POLICY",
                    condition="flag", decision_override=GovernanceDecision.REJECT,
                ),
                GovernanceRule(
                    id="r2", name="Escalate", evaluator_type="POLICY",
                    condition="flag", decision_override=GovernanceDecision.ESCALATE,
                ),
            ]
        )
        r = await ev.evaluate(_g({"flag": True}), _c())
        assert r.decision == GovernanceDecision.ESCALATE

    @pytest.mark.asyncio
    async def test_no_decision_override_skips(self):
        """Rule with no decision_override that matches is logged but skipped."""
        ev = PolicyEvaluator(
            get_rules=lambda: [
                GovernanceRule(
                    id="r1", name="No Override", evaluator_type="POLICY",
                    condition="flag",
                    # no decision_override
                ),
            ]
        )
        r = await ev.evaluate(_g({"flag": True}), _c())
        # No matching rules with decision_override → ALLOW
        assert r.decision == GovernanceDecision.ALLOW

    @pytest.mark.asyncio
    async def test_condition_parser_error_logs_warning_continues(self):
        """Custom condition parser that raises — error is caught at rule level,
        rule is skipped, remaining rules still evaluated."""
        def raising_parser(condition: str, graph, context) -> bool:
            if "BROKEN" in condition:
                raise ValueError("simulated parser error")
            return PolicyEvaluator._default_condition_parser(condition, graph, context)

        ev = PolicyEvaluator(
            get_rules=lambda: [
                GovernanceRule(
                    id="r1", name="Broken Rule", evaluator_type="POLICY",
                    condition="BROKEN: bad syntax",
                    decision_override=GovernanceDecision.REJECT,
                ),
                GovernanceRule(
                    id="r2", name="Good Rule", evaluator_type="POLICY",
                    condition="flag", decision_override=GovernanceDecision.WAIT,
                ),
            ],
            condition_parser=raising_parser,
        )
        # r1 parser raises → skipped; r2 matches → WAIT
        r = await ev.evaluate(_g({"flag": True}), _c())
        assert r.decision == GovernanceDecision.WAIT

    @pytest.mark.asyncio
    async def test_empty_condition(self):
        ev = PolicyEvaluator(
            get_rules=lambda: [
                GovernanceRule(
                    id="r1", name="Empty", evaluator_type="POLICY",
                    condition="", decision_override=GovernanceDecision.REJECT,
                ),
            ]
        )
        r = await ev.evaluate(_g(), _c())
        assert r.decision == GovernanceDecision.ALLOW


# ── 8. Evaluator Names ───────────────────────────────────────────


class TestEvaluatorNames:
    """Verify each evaluator reports the correct name."""

    def test_risk_name(self):
        assert RiskEvaluator().name == "risk"

    def test_approval_name(self):
        assert ApprovalEvaluator().name == "approval"

    def test_maintenance_name(self):
        assert MaintenanceEvaluator().name == "maintenance"

    def test_cluster_name(self):
        assert ClusterEvaluator().name == "cluster"

    def test_resource_name(self):
        assert ResourceEvaluator().name == "resource"

    def test_capability_name(self):
        assert CapabilityEvaluator().name == "capability"

    def test_policy_name(self):
        assert PolicyEvaluator().name == "policy"
