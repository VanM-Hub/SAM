"""Tests for Autonomous Runtime & Operational Safety — Sprint 32.

Coverage:
  - AutonomyLevel enum (5 levels, numeric, can_execute)
  - AutonomyController: get/set/adjust/history
  - SafetyEnvelope: boundaries, check violations
  - Guardrails: rules, evaluation, conditions
  - Escalation: create, resolve, pending, expiry
  - GracefulDegradation: degrade, upgrade, history
  - SelfAssessment: before/after, recommendations
  - CLI smoke tests
"""

import time

import pytest

from sam.autonomy.models import AutonomyLevel, AutonomyConfig
from sam.autonomy.controller import AutonomyController
from sam.autonomy.safety import SafetyEnvelope, SafetyBoundary
from sam.autonomy.guardrails import (
    Guardrails,
    GuardrailRule,
    GuardrailResult,
    DECISION_ALLOW,
    DECISION_BLOCK,
    DECISION_WARN,
    DECISION_ESCALATE,
)
from sam.autonomy.escalation import (
    EscalationManager,
    EscalationRequest,
    STATUS_PENDING,
    STATUS_RESOLVED,
    DECISION_APPROVE,
    DECISION_REJECT,
)
from sam.autonomy.degradation import GracefulDegradation
from sam.autonomy.assessment import SelfAssessment, AssessmentResult


# ═══════════════════════════════════════════════════════════════════
# AutonomyLevel
# ═══════════════════════════════════════════════════════════════════


class TestAutonomyLevel:
    def test_five_levels(self):
        assert len(AutonomyLevel) == 5

    def test_enum_values(self):
        assert AutonomyLevel.OBSERVE.value == "observe"
        assert AutonomyLevel.RECOMMEND.value == "recommend"
        assert AutonomyLevel.ASSIST.value == "assist"
        assert AutonomyLevel.SUPERVISE.value == "supervise"
        assert AutonomyLevel.AUTONOMOUS.value == "autonomous"

    def test_numeric(self):
        assert AutonomyLevel.OBSERVE.numeric == 1
        assert AutonomyLevel.AUTONOMOUS.numeric == 5

    def test_from_numeric(self):
        assert AutonomyLevel.from_numeric(3) == AutonomyLevel.ASSIST
        assert AutonomyLevel.from_numeric(99) == AutonomyLevel.OBSERVE

    def test_can_execute_observe(self):
        assert AutonomyLevel.OBSERVE.can_execute() is False
        assert AutonomyLevel.OBSERVE.can_execute("low") is False

    def test_can_execute_recommend(self):
        assert AutonomyLevel.RECOMMEND.can_execute() is False

    def test_can_execute_assist(self):
        assert AutonomyLevel.ASSIST.can_execute("low") is True
        assert AutonomyLevel.ASSIST.can_execute("high") is False
        assert AutonomyLevel.ASSIST.can_execute("critical") is False

    def test_can_execute_supervise(self):
        assert AutonomyLevel.SUPERVISE.can_execute("high") is True
        assert AutonomyLevel.SUPERVISE.can_execute("critical") is False

    def test_can_execute_autonomous(self):
        assert AutonomyLevel.AUTONOMOUS.can_execute("critical") is True


# ═══════════════════════════════════════════════════════════════════
# AutonomyController
# ═══════════════════════════════════════════════════════════════════


class TestAutonomyController:
    @pytest.fixture
    def ctrl(self):
        return AutonomyController()

    async def test_default_level(self, ctrl):
        assert await ctrl.get_current_level() == AutonomyLevel.SUPERVISE

    async def test_set_level(self, ctrl):
        await ctrl.set_level(AutonomyLevel.AUTONOMOUS, "testing")
        assert await ctrl.get_current_level() == AutonomyLevel.AUTONOMOUS

    async def test_adjust_up(self, ctrl):
        await ctrl.set_level(AutonomyLevel.ASSIST, "baseline")
        new_level = await ctrl.adjust_level(confidence=90.0, risk=0.1)
        assert new_level == AutonomyLevel.SUPERVISE

    async def test_adjust_down(self, ctrl):
        await ctrl.set_level(AutonomyLevel.SUPERVISE, "baseline")
        new_level = await ctrl.adjust_level(confidence=40.0, risk=0.8)
        assert new_level == AutonomyLevel.ASSIST

    async def test_adjust_no_change(self, ctrl):
        new_level = await ctrl.adjust_level(confidence=60.0, risk=0.5)
        assert new_level == AutonomyLevel.SUPERVISE  # unchanged

    async def test_cannot_go_below_observe(self, ctrl):
        await ctrl.set_level(AutonomyLevel.OBSERVE, "min")
        new_level = await ctrl.adjust_level(confidence=10.0, risk=0.9)
        assert new_level == AutonomyLevel.OBSERVE

    async def test_cannot_go_above_autonomous(self, ctrl):
        await ctrl.set_level(AutonomyLevel.AUTONOMOUS, "max")
        new_level = await ctrl.adjust_level(confidence=100.0, risk=0.0)
        assert new_level == AutonomyLevel.AUTONOMOUS

    async def test_history(self, ctrl):
        await ctrl.set_level(AutonomyLevel.AUTONOMOUS, "test1")
        await ctrl.set_level(AutonomyLevel.SUPERVISE, "test2")
        history = await ctrl.get_autonomy_history(limit=10)
        assert len(history) == 2

    async def test_reset_to_default(self, ctrl):
        await ctrl.set_level(AutonomyLevel.OBSERVE, "test")
        await ctrl.reset_to_default()
        assert await ctrl.get_current_level() == AutonomyLevel.SUPERVISE

    async def test_get_config(self, ctrl):
        config = await ctrl.get_config()
        assert isinstance(config, AutonomyConfig)


# ═══════════════════════════════════════════════════════════════════
# SafetyEnvelope
# ═══════════════════════════════════════════════════════════════════


class TestSafetyEnvelope:
    @pytest.fixture
    def env(self):
        return SafetyEnvelope()

    async def test_safe_action(self, env):
        result = await env.check({"cpu_usage": 50, "memory_usage": 50})
        assert result is True

    async def test_block_cpu_over_limit(self, env):
        result = await env.check({"cpu_usage": 99})
        assert result is False

    async def test_block_memory_over_limit(self, env):
        result = await env.check({"memory_usage": 99})
        assert result is False

    async def test_warn_confidence(self, env):
        result = await env.check({"operational_confidence": 20})
        assert result is True  # warn = still safe

    async def test_unknown_metric_ignored(self, env):
        result = await env.check({"unknown_metric": 999})
        assert result is True

    async def test_get_boundaries(self, env):
        bounds = await env.get_boundaries()
        assert "max_cpu" in bounds
        assert "max_memory" in bounds

    async def test_update_boundary(self, env):
        nb = SafetyBoundary(name="max_cpu", metric="cpu_usage", max_value=50)
        await env.update_boundary(nb)
        result = await env.check({"cpu_usage": 60})
        assert result is False  # Now 50 is the limit

    async def test_remove_boundary(self, env):
        await env.remove_boundary("max_cpu")
        bounds = await env.get_boundaries()
        assert "max_cpu" not in bounds

    async def test_disabled_boundary(self, env):
        nb = SafetyBoundary(name="max_cpu", metric="cpu_usage", max_value=50, enabled=False)
        await env.update_boundary(nb)
        result = await env.check({"cpu_usage": 99})
        assert result is True  # Disabled = no check

    async def test_clear(self, env):
        await env.clear()
        assert await env.get_boundaries() == {}


# ═══════════════════════════════════════════════════════════════════
# Guardrails
# ═══════════════════════════════════════════════════════════════════


class TestGuardrails:
    @pytest.fixture
    def gr(self):
        g = Guardrails()
        g._rules = {
            "gr1": GuardrailRule(
                id="gr1", name="cpu_limit",
                condition={"metric": "cpu_usage", "op": "<=", "value": 90},
                on_violation=DECISION_BLOCK,
            ),
            "gr2": GuardrailRule(
                id="gr2", name="cost_warn",
                condition={"metric": "cost", "op": "<=", "value": 100},
                on_violation=DECISION_WARN,
            ),
        }
        return g

    async def test_all_pass(self, gr):
        result = await gr.evaluate({"cpu_usage": 50, "cost": 50})
        assert result.decision == DECISION_ALLOW
        assert result.is_safe is True

    async def test_block_violation(self, gr):
        result = await gr.evaluate({"cpu_usage": 95, "cost": 50})
        assert result.decision == DECISION_BLOCK
        assert result.is_safe is False

    async def test_warn_violation(self, gr):
        result = await gr.evaluate({"cpu_usage": 50, "cost": 200})
        assert result.decision == DECISION_WARN
        assert result.is_safe is True

    async def test_multiple_violations(self, gr):
        result = await gr.evaluate({"cpu_usage": 95, "cost": 200})
        assert len(result.violations) == 2
        assert result.decision == DECISION_BLOCK  # block > warn

    async def test_add_rule(self, gr):
        rule = GuardrailRule(name="test", condition={"metric": "x", "op": "<=", "value": 10})
        await gr.add_rule(rule)
        assert await gr.count() == 3

    async def test_remove_rule(self, gr):
        await gr.remove_rule("gr1")
        assert await gr.count() == 1

    async def test_get_active(self, gr):
        rules = await gr.get_active_guardrails()
        assert len(rules) == 2

    async def test_disabled_rule_skipped(self, gr):
        gr._rules["gr1"].enabled = False
        result = await gr.evaluate({"cpu_usage": 95})
        # gr1 disabled, gr2 passes (cost not in action), so ALLOW
        assert result.decision in (DECISION_ALLOW, DECISION_WARN)

    async def test_clear(self, gr):
        await gr.clear()
        assert await gr.count() == 0

    async def test_escalate_decision(self, gr):
        gr._rules["gr1"].on_violation = DECISION_ESCALATE
        result = await gr.evaluate({"cpu_usage": 95})
        assert result.decision == DECISION_ESCALATE


# ═══════════════════════════════════════════════════════════════════
# Escalation
# ═══════════════════════════════════════════════════════════════════


class TestEscalationManager:
    @pytest.fixture
    def esc(self):
        return EscalationManager()

    async def test_escalate(self, esc):
        req = await esc.escalate("High CPU", "Needs human review")
        assert req.id.startswith("esc_")
        assert req.status == STATUS_PENDING

    async def test_get_pending(self, esc):
        await esc.escalate("Issue A", "Reason A")
        await esc.escalate("Issue B", "Reason B")
        pending = await esc.get_pending_escalations()
        assert len(pending) == 2

    async def test_resolve_approve(self, esc):
        req = await esc.escalate("Test", "Reason")
        resolved = await esc.resolve_escalation(req.id, DECISION_APPROVE)
        assert resolved.status == STATUS_RESOLVED
        assert resolved.decision == DECISION_APPROVE

    async def test_resolve_reject(self, esc):
        req = await esc.escalate("Test", "Reason")
        resolved = await esc.resolve_escalation(req.id, DECISION_REJECT)
        assert resolved.status == STATUS_RESOLVED
        assert resolved.decision == DECISION_REJECT

    async def test_resolve_nonexistent(self, esc):
        assert await esc.resolve_escalation("ghost", "approve") is None

    async def test_expire_after_ttl(self, esc):
        req = await esc.escalate("Old", "Stale")
        req.ttl = -1  # Negative = already expired
        # Need to wait briefly or set created_at to past
        import datetime
        req.created_at = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
        pending = await esc.get_pending_escalations()
        assert len(pending) == 0  # Expired

    async def test_get_all(self, esc):
        await esc.escalate("A", "R1")
        await esc.escalate("B", "R2")
        all_esc = await esc.get_all_escalations()
        assert len(all_esc) == 2

    async def test_get_escalation_by_id(self, esc):
        req = await esc.escalate("Test", "Reason")
        found = await esc.get_escalation(req.id)
        assert found is not None
        assert await esc.get_escalation("ghost") is None

    async def test_clear(self, esc):
        await esc.escalate("A", "R")
        await esc.clear()
        assert len(await esc.get_all_escalations()) == 0


# ═══════════════════════════════════════════════════════════════════
# GracefulDegradation
# ═══════════════════════════════════════════════════════════════════


class TestGracefulDegradation:
    @pytest.fixture
    def dg(self):
        return GracefulDegradation()

    async def test_degrade_one_level(self, dg):
        result = await dg.degrade(AutonomyLevel.AUTONOMOUS, "high risk")
        assert result == AutonomyLevel.SUPERVISE
        assert await dg.is_degraded() is True

    async def test_degrade_two_levels(self, dg):
        result = await dg.degrade(AutonomyLevel.AUTONOMOUS, "risk", steps=2)
        assert result == AutonomyLevel.ASSIST

    async def test_degrade_to_min(self, dg):
        result = await dg.degrade(AutonomyLevel.OBSERVE, "already min")
        assert result == AutonomyLevel.OBSERVE

    async def test_upgrade_one_level(self, dg):
        result = await dg.upgrade(AutonomyLevel.ASSIST, "confidence restored")
        assert result == AutonomyLevel.SUPERVISE

    async def test_upgrade_to_max(self, dg):
        result = await dg.upgrade(AutonomyLevel.AUTONOMOUS, "already max")
        assert result == AutonomyLevel.AUTONOMOUS

    async def test_degrade_then_upgrade(self, dg):
        await dg.degrade(AutonomyLevel.AUTONOMOUS, "issue")
        await dg.upgrade(AutonomyLevel.SUPERVISE, "recovered")
        assert await dg.is_degraded() is False  # Upgraded to ASSIST+

    async def test_history(self, dg):
        await dg.degrade(AutonomyLevel.AUTONOMOUS, "first")
        await dg.upgrade(AutonomyLevel.SUPERVISE, "second")
        history = await dg.get_degradation_history()
        assert len(history) == 2

    async def test_get_recovery_attempts(self, dg):
        await dg.degrade(AutonomyLevel.AUTONOMOUS, "issue")
        await dg.upgrade(AutonomyLevel.SUPERVISE, "try1")
        await dg.upgrade(AutonomyLevel.ASSIST, "try2")
        assert await dg.get_recovery_attempts() == 2

    async def test_reset(self, dg):
        await dg.degrade(AutonomyLevel.AUTONOMOUS, "issue")
        await dg.reset()
        assert await dg.is_degraded() is False
        assert await dg.get_recovery_attempts() == 0


# ═══════════════════════════════════════════════════════════════════
# SelfAssessment
# ═══════════════════════════════════════════════════════════════════


class TestSelfAssessment:
    @pytest.fixture
    def sa(self):
        return SelfAssessment()

    async def test_assess_before_low_risk(self, sa):
        result = await sa.assess_before({"id": "a1", "risk": 0.1, "type": "scale"})
        assert result.phase == "before"
        assert result.recommendation == "proceed"
        assert result.should_proceed is True

    async def test_assess_before_high_risk(self, sa):
        result = await sa.assess_before({"id": "a2", "risk": 0.9, "type": "deploy"})
        assert result.recommendation == "abort"
        assert result.should_proceed is False

    async def test_assess_before_destructive_action(self, sa):
        result = await sa.assess_before({"id": "a3", "risk": 0.3, "type": "destroy"})
        # Risk 0.3 is low so still proceed; issue is flagged but recommendation stays proceed
        assert len(result.issues) >= 1
        assert "destroy" in result.issues[0].lower()

    async def test_assess_after_success(self, sa):
        result = await sa.assess_after(
            {"id": "a1", "expected_duration_ms": 100},
            {"success": True, "duration_ms": 80},
        )
        assert result.phase == "after"
        assert result.confidence > 80

    async def test_assess_after_failure(self, sa):
        result = await sa.assess_after(
            {"id": "a1", "expected_duration_ms": 100},
            {"success": False, "duration_ms": 0},
        )
        assert "failed" in result.issues[0]
        assert result.confidence < 100

    async def test_assess_after_slow_execution(self, sa):
        result = await sa.assess_after(
            {"id": "a1", "expected_duration_ms": 100},
            {"success": True, "duration_ms": 500},
        )
        assert len(result.issues) > 0

    async def test_history(self, sa):
        await sa.assess_before({"id": "a1", "risk": 0.1})
        await sa.assess_before({"id": "a2", "risk": 0.8})
        history = await sa.get_assessment_history()
        assert len(history) == 2

    async def test_clear(self, sa):
        await sa.assess_before({"id": "a1", "risk": 0.1})
        await sa.clear()
        assert len(await sa.get_assessment_history()) == 0


# ═══════════════════════════════════════════════════════════════════
# CLI Smoke
# ═══════════════════════════════════════════════════════════════════


class TestCLI:
    def test_autonomy_app_importable(self):
        from sam.cli.autonomy_app import autonomy_app
        assert autonomy_app.info.name == "autonomy"

    def test_autonomy_has_commands(self):
        from sam.cli.autonomy_app import autonomy_app
        names = [c.name for c in autonomy_app.registered_commands]
        for cmd in ("status", "set", "history", "guardrails", "escalate", "degrade", "upgrade"):
            assert cmd in names, f"Missing command: {cmd}"

    def test_main_registers_autonomy(self):
        from sam.cli.main import app
        registered = [g.name for g in app.registered_groups]
        assert "autonomy" in registered
