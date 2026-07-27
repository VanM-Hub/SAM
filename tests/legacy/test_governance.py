"""
Test Governance Models & Evaluator Interface – Sprint 21 Fase 1

Covers:
- GovernanceDecision enum
- GovernanceResult creation, shorthand factories, utility methods
- GovernanceRule model validation
- Evaluator interface compliance
- BaseEvaluator error handling
"""

import pytest
from typing import Optional

from src.sam.governance.models import (
    GovernanceDecision,
    GovernanceResult,
    GovernanceRule,
)
from src.sam.governance.evaluator import Evaluator, BaseEvaluator


# ── Test Data ────────────────────────────────────────────────────


class _MinimalGraph:
    """Minimal mock of ExecutionGraph for tests."""

    def __init__(self, id: str = "g-1"):
        self.id = id
        self.name = "test-graph"


class _MinimalContext:
    """Minimal mock of ExecutionContext for tests."""

    def __init__(self):
        self.execution_id = "exec-1"
        self.workflow_id = ""
        self.inputs = {}


# ── 1. GovernanceDecision Enum ───────────────────────────────────


class TestGovernanceDecision:
    """Test GovernanceDecision enum values."""

    def test_all_values(self):
        expected = {
            "ALLOW",
            "ALLOW_WITH_WARNING",
            "WAIT",
            "REQUIRE_APPROVAL",
            "REJECT",
            "ESCALATE",
        }
        actual = {d.value for d in GovernanceDecision}
        assert actual == expected

    def test_ordering_is_not_implied(self):
        """Enum does not define ordering — just verify values are distinct."""
        values = [d.value for d in GovernanceDecision]
        assert len(values) == len(set(values))


# ── 2. GovernanceResult ──────────────────────────────────────────


class TestGovernanceResult:
    """Test GovernanceResult model and shorthand factories."""

    def test_defaults(self):
        r = GovernanceResult(decision=GovernanceDecision.ALLOW)
        assert r.decision == GovernanceDecision.ALLOW
        assert r.reason == ""
        assert r.warnings == []
        assert r.required_approvals == []
        assert r.suggested_delay is None
        assert r.evaluator_results == {}
        assert r.metadata == {}

    def test_shorthand_allowed(self):
        r = GovernanceResult.allowed(reason="looks good")
        assert r.decision == GovernanceDecision.ALLOW
        assert r.reason == "looks good"

    def test_shorthand_allowed_with_warning(self):
        r = GovernanceResult.allowed_with_warning(
            reason="minor risk",
            warnings=["high latency expected"],
        )
        assert r.decision == GovernanceDecision.ALLOW_WITH_WARNING
        assert r.reason == "minor risk"
        assert r.warnings == ["high latency expected"]

    def test_shorthand_wait(self):
        r = GovernanceResult.wait(
            reason="maintenance window active",
            suggested_delay=300,
        )
        assert r.decision == GovernanceDecision.WAIT
        assert r.reason == "maintenance window active"
        assert r.suggested_delay == 300

    def test_shorthand_wait_no_delay(self):
        r = GovernanceResult.wait(reason="cluster unstable")
        assert r.decision == GovernanceDecision.WAIT
        assert r.suggested_delay is None

    def test_shorthand_require_approval(self):
        r = GovernanceResult.require_approval(
            reason="touching production DB",
            approvals=["dba-team", "ops-lead"],
        )
        assert r.decision == GovernanceDecision.REQUIRE_APPROVAL
        assert r.reason == "touching production DB"
        assert r.required_approvals == ["dba-team", "ops-lead"]

    def test_shorthand_require_approval_no_approvals(self):
        r = GovernanceResult.require_approval(reason="needs review")
        assert r.decision == GovernanceDecision.REQUIRE_APPROVAL
        assert r.required_approvals == []

    def test_shorthand_rejected(self):
        r = GovernanceResult.rejected(reason="risk too high")
        assert r.decision == GovernanceDecision.REJECT
        assert r.reason == "risk too high"

    def test_shorthand_escalated(self):
        r = GovernanceResult.escalated(reason="unusual pattern detected")
        assert r.decision == GovernanceDecision.ESCALATE
        assert r.reason == "unusual pattern detected"

    def test_is_blocked_true_for_require_approval(self):
        r = GovernanceResult(decision=GovernanceDecision.REQUIRE_APPROVAL)
        assert r.is_blocked()

    def test_is_blocked_true_for_reject(self):
        r = GovernanceResult(decision=GovernanceDecision.REJECT)
        assert r.is_blocked()

    def test_is_blocked_true_for_escalate(self):
        r = GovernanceResult(decision=GovernanceDecision.ESCALATE)
        assert r.is_blocked()

    def test_is_blocked_false_for_allow(self):
        r = GovernanceResult(decision=GovernanceDecision.ALLOW)
        assert not r.is_blocked()

    def test_is_blocked_false_for_wait(self):
        r = GovernanceResult(decision=GovernanceDecision.WAIT)
        assert not r.is_blocked()

    def test_is_blocked_false_for_allow_with_warning(self):
        r = GovernanceResult(decision=GovernanceDecision.ALLOW_WITH_WARNING)
        assert not r.is_blocked()

    def test_needs_approval_true(self):
        r = GovernanceResult(
            decision=GovernanceDecision.REQUIRE_APPROVAL,
            required_approvals=["ops"],
        )
        assert r.needs_approval()

    def test_needs_approval_false_no_approvals(self):
        r = GovernanceResult(
            decision=GovernanceDecision.REQUIRE_APPROVAL,
            required_approvals=[],
        )
        assert not r.needs_approval()

    def test_needs_approval_false_wrong_decision(self):
        r = GovernanceResult(
            decision=GovernanceDecision.ALLOW,
            required_approvals=["ops"],
        )
        assert not r.needs_approval()

    def test_is_allowed_true(self):
        assert GovernanceResult(decision=GovernanceDecision.ALLOW).is_allowed()
        assert GovernanceResult(
            decision=GovernanceDecision.ALLOW_WITH_WARNING
        ).is_allowed()

    def test_is_allowed_false(self):
        assert not GovernanceResult(decision=GovernanceDecision.REJECT).is_allowed()
        assert not GovernanceResult(decision=GovernanceDecision.WAIT).is_allowed()

    def test_extra_field_forbidden(self):
        with pytest.raises(Exception):
            GovernanceResult(decision=GovernanceDecision.ALLOW, unknown_field=42)

    def test_serialize_to_dict(self):
        r = GovernanceResult(
            decision=GovernanceDecision.ALLOW_WITH_WARNING,
            reason="low risk",
            warnings=["w1"],
            suggested_delay=60,
            evaluator_results={
                "risk": GovernanceResult(decision=GovernanceDecision.ALLOW),
            },
            metadata={"score": 0.3},
        )
        d = r.model_dump()
        assert d["decision"] == "ALLOW_WITH_WARNING"
        assert d["reason"] == "low risk"
        assert d["warnings"] == ["w1"]
        assert d["suggested_delay"] == 60
        assert d["metadata"]["score"] == 0.3
        # Nested evaluator_results should serialize recursively
        assert d["evaluator_results"]["risk"]["decision"] == "ALLOW"


# ── 3. GovernanceRule ────────────────────────────────────────────


class TestGovernanceRule:
    """Test GovernanceRule model validation."""

    def test_minimal_rule(self):
        r = GovernanceRule(
            id="rule-1",
            name="Production DB Access Control",
            evaluator_type="RISK",
        )
        assert r.id == "rule-1"
        assert r.name == "Production DB Access Control"
        assert r.evaluator_type == "RISK"
        assert r.condition == ""
        assert r.decision_override is None
        assert r.enabled is True
        assert r.metadata == {}

    def test_full_rule(self):
        r = GovernanceRule(
            id="rule-2",
            name="Maintenance Window Checker",
            evaluator_type="MAINTENANCE",
            condition="maintenance.active == true",
            decision_override=GovernanceDecision.WAIT,
            enabled=True,
            metadata={"window_type": "weekly"},
        )
        assert r.id == "rule-2"
        assert r.condition == "maintenance.active == true"
        assert r.decision_override == GovernanceDecision.WAIT
        assert r.metadata["window_type"] == "weekly"

    def test_disabled_rule(self):
        r = GovernanceRule(
            id="rule-3",
            name="Disabled Rule",
            evaluator_type="POLICY",
            enabled=False,
        )
        assert r.enabled is False

    def test_extra_field_forbidden(self):
        with pytest.raises(Exception):
            GovernanceRule(
                id="rule-x",
                name="Bad",
                evaluator_type="POLICY",
                extra_thing=123,
            )

    def test_all_evaluator_types_accepted(self):
        for etype in [
            "RISK",
            "APPROVAL",
            "MAINTENANCE",
            "CLUSTER",
            "RESOURCE",
            "CAPABILITY",
            "POLICY",
        ]:
            r = GovernanceRule(id=f"r-{etype}", name=etype, evaluator_type=etype)
            assert r.evaluator_type == etype


# ── 4. Evaluator Interface ───────────────────────────────────────


class _TestEvaluator(BaseEvaluator):
    """Minimal concrete evaluator for interface testing."""

    def __init__(self, result: Optional[GovernanceResult] = None,
                 name: str = "test_evaluator",
                 should_raise: bool = False):
        super().__init__()
        self._name = name
        self._result = result
        self._should_raise = should_raise

    @property
    def name(self) -> str:
        return self._name

    async def _do_evaluate(self, graph, context) -> GovernanceResult:
        if self._should_raise:
            raise RuntimeError("simulated evaluator crash")
        if self._result:
            return self._result
        return GovernanceResult.allowed(reason="default")


class TestEvaluatorInterface:
    """Test evaluator interface compliance."""

    @pytest.mark.asyncio
    async def test_evaluator_must_define_name(self):
        ev = _TestEvaluator(name="risk")
        assert ev.name == "risk"

    @pytest.mark.asyncio
    async def test_evaluate_returns_result(self):
        ev = _TestEvaluator(result=GovernanceResult.allowed(reason="ok"))
        graph = _MinimalGraph()
        ctx = _MinimalContext()
        result = await ev.evaluate(graph, ctx)
        assert result.decision == GovernanceDecision.ALLOW
        assert result.reason == "ok"

    @pytest.mark.asyncio
    async def test_evaluate_with_warnings(self):
        ev = _TestEvaluator(
            result=GovernanceResult.allowed_with_warning(
                reason="ok-ish",
                warnings=["deprecated API used"],
            )
        )
        result = await ev.evaluate(_MinimalGraph(), _MinimalContext())
        assert result.decision == GovernanceDecision.ALLOW_WITH_WARNING
        assert "deprecated API used" in result.warnings

    @pytest.mark.asyncio
    async def test_evaluate_reject(self):
        ev = _TestEvaluator(
            result=GovernanceResult.rejected(reason="policy violation")
        )
        result = await ev.evaluate(_MinimalGraph(), _MinimalContext())
        assert result.decision == GovernanceDecision.REJECT
        assert result.is_blocked()

    @pytest.mark.asyncio
    async def test_evaluator_error_returns_reject(self):
        """Error inside _do_evaluate should be caught and return REJECT."""
        ev = _TestEvaluator(should_raise=True, name="crashy")
        result = await ev.evaluate(_MinimalGraph(), _MinimalContext())
        assert result.decision == GovernanceDecision.REJECT
        assert "simulated evaluator crash" in result.reason
        assert not result.is_allowed()

    @pytest.mark.asyncio
    async def test_evaluator_error_includes_name(self):
        ev = _TestEvaluator(should_raise=True, name="validation-checker")
        result = await ev.evaluate(_MinimalGraph(), _MinimalContext())
        assert "validation-checker" in result.reason

    @pytest.mark.asyncio
    async def test_evaluator_interface_cannot_be_instantiated(self):
        """Abstract Evaluator should not be directly instantiable."""
        with pytest.raises(TypeError):
            Evaluator()  # type: ignore[abstract]


# ── 5. GovernanceDecision comparison helpers ─────────────────────


class TestDecisionBoundaries:
    """Test edge cases and boundary conditions."""

    def test_allowed_with_warning_is_not_blocked(self):
        r = GovernanceResult.allowed_with_warning(reason="risky", warnings=["w"])
        assert not r.is_blocked()
        assert r.is_allowed()

    def test_wait_is_not_blocked_but_not_allowed(self):
        r = GovernanceResult.wait(reason="later")
        assert not r.is_blocked()
        assert not r.is_allowed()

    def test_full_roundtrip(self):
        """Create every decision type via shorthand and verify properties."""
        tests = [
            (GovernanceResult.allowed("all good"), True, False, False),
            (GovernanceResult.allowed_with_warning("warn"), True, False, False),
            (GovernanceResult.wait("later"), False, False, False),
            (GovernanceResult.require_approval("need ok", ["a"]), False, True, True),
            (GovernanceResult.rejected("nope"), False, True, False),
            (GovernanceResult.escalated("help"), False, True, False),
        ]
        for r, is_allowed, is_blocked, needs_approval in tests:
            assert r.is_allowed() == is_allowed, f"{r.decision}: is_allowed"
            assert r.is_blocked() == is_blocked, f"{r.decision}: is_blocked"
            assert r.needs_approval() == needs_approval, f"{r.decision}: needs_approval"
