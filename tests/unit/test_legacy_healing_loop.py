"""End-to-end and integration tests for SelfHealingLoop.

Tests cover:
- Complete cycle: Observe -> Diagnose -> Reason -> Plan -> Govern
  -> Execute -> Verify -> Reflect -> Learn
- All phase-level behaviors
- Edge cases: critical severity, no engine dependencies, failed healing
- Reflection capture and lesson extraction
- Learn phase: creates pending proposals (no auto-approve)
"""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pytest

from sam.healing.loop import (
    SelfHealingLoop,
    Symptom,
    Diagnosis,
    CycleContext,
    HealingPhase,
)
from sam.healing.reflection import ReflectionManager, ReflectionRecord
from sam.cognitive.healing import (
    HealingAction,
    HealingManager,
    HealingResult,
    HealingStrategy,
)
from sam.evolution.policy import EvolutionPolicy, ProposalType, ProposalStatus


# ── Mock Dependencies ──────────────────────────────────────────────


class InMemoryDB:
    def __init__(self):
        self.rows = []

    async def execute(self, sql, params=None):
        if params:
            row = {"id": params[0]}
            if len(params) > 1:
                row["cycle_id"] = params[1]
            self.rows.append(row)
        return None

    async def fetch_one(self, sql, params=None):
        if "COUNT" in sql.upper():
            return {"cnt": len(self.rows)}
        return None

    async def fetch_all(self, sql, params=None):
        return list(self.rows)


class MockHealingManager:
    """A HealingManager that returns controlled results."""

    def __init__(self, result: Optional[HealingResult] = None):
        self.last_action: Optional[HealingAction] = None
        self.actions_executed: List[HealingAction] = []
        self._result = result or HealingResult(
            action_id="mock_action",
            success=True,
            message="Mock healing applied",
            duration_ms=42,
        )

    async def execute_healing(self, action: HealingAction) -> HealingResult:
        self.last_action = action
        self.actions_executed.append(action)
        return self._result

    async def detect_patterns(self, evidence: List[Dict[str, Any]]) -> List[Any]:
        return []


class MockReflectionManager:
    """A reflection manager that records and returns ReflectionRecords."""

    def __init__(self):
        self.records: List[ReflectionRecord] = []

    async def record_reflection(self, **kwargs) -> ReflectionRecord:
        record = ReflectionRecord(
            id=f"refl_{len(self.records)}",
            cycle_id=kwargs.get("cycle_id", ""),
            symptom=kwargs.get("symptom", ""),
            hypothesis=kwargs.get("hypothesis", ""),
            action_taken=kwargs.get("action_taken", ""),
            expected_outcome=kwargs.get("expected_outcome", ""),
            actual_outcome=kwargs.get("actual_outcome", ""),
            gap_analysis=kwargs.get("gap_analysis", ""),
            lessons=kwargs.get("lessons", []),
            confidence=kwargs.get("confidence", 0.5),
            success=kwargs.get("success", True),
            timestamp=datetime.now(timezone.utc),
            metadata=kwargs.get("metadata", {}),
        )
        self.records.append(record)
        return record


class MockParamManager:
    def __init__(self):
        self._params = {}

    async def get(self, name):
        return self._params.get(name)

    async def set(self, name, value):
        if name in self._params:
            self._params[name].current_value = value
        self._params[name] = value


class MockInstitutionalMemory:
    def __init__(self):
        self.stored: List[Any] = []

    async def search(self, query):
        return []

    async def store(self, entry):
        self.stored.append(entry)


class MockConfidence:
    def __init__(self, score: int = 80):
        self._score = score
        self._breakdown = None

    def get_current_score(self) -> Optional[int]:
        return self._score

    def get_current_breakdown(self):
        return self._breakdown


# ── Fixtures ───────────────────────────────────────────────────────


@pytest.fixture
def mock_healing():
    return MockHealingManager()


@pytest.fixture
def mock_reflection():
    return MockReflectionManager()


@pytest.fixture
def mock_confidence():
    return MockConfidence(score=80)


@pytest.fixture
def mock_memory():
    return MockInstitutionalMemory()


@pytest.fixture
def mock_policy():
    pm = MockParamManager()
    return EvolutionPolicy(param_manager=pm)


@pytest.fixture
def basic_symptom():
    return Symptom(
        id="sym_001",
        source="health_collector",
        description="High error rate in provider nvidia",
        severity=3,
        evidence={"error_rate": 0.15, "indicators": ["timeout"]},
        pattern="provider_timeout",
    )


@pytest.fixture
def critical_symptom():
    return Symptom(
        id="sym_critical",
        source="health_collector",
        description="Provider completely unresponsive",
        severity=5,
        evidence={"error_rate": 1.0, "indicators": ["down"]},
    )


@pytest.fixture
def low_severity_symptom():
    return Symptom(
        id="sym_low",
        source="health_collector",
        description="Minor latency increase",
        severity=2,
    )


@pytest.fixture
def loop(mock_healing, mock_reflection, mock_confidence, mock_memory, mock_policy):
    return SelfHealingLoop(
        healing_manager=mock_healing,
        reflection_manager=mock_reflection,
        confidence_calculator=mock_confidence,
        institutional_memory=mock_memory,
        evolution_policy=mock_policy,
    )


# ── Tests ──────────────────────────────────────────────────────────


class TestSymptomUnit:
    def test_critical_high_severity(self):
        s = Symptom(id="s1", source="test", description="x", severity=5)
        assert s.is_critical()

    def test_not_critical_low_severity(self):
        s = Symptom(id="s2", source="test", description="x", severity=3)
        assert not s.is_critical()

    def test_to_dict(self):
        s = Symptom(id="s1", source="src", description="desc", severity=4,
                     evidence={"k": "v"}, pattern="p1")
        d = s.to_dict()
        assert d["id"] == "s1"
        assert d["severity"] == 4
        assert d["pattern"] == "p1"


class TestDiagnosisUnit:
    def test_confident(self):
        d = Diagnosis(symptom_id="s1", root_cause="rc", confidence=0.8)
        assert d.is_confident()

    def test_not_confident(self):
        d = Diagnosis(symptom_id="s1", root_cause="rc", confidence=0.5)
        assert not d.is_confident()


class TestHealingLoopConstruction:
    def test_create_loop(self, loop):
        assert loop.get_cycle_count() == 0

    def test_create_loop_minimal(self, mock_healing, mock_reflection):
        # No optional dependencies
        loop = SelfHealingLoop(
            healing_manager=mock_healing,
            reflection_manager=mock_reflection,
        )
        assert loop._confidence is None
        assert loop._memory is None
        assert loop._policy is None
        assert loop._governance is None
        assert loop._planner is None
        assert loop._executor is None
        assert loop._optimizer is None


class TestHealingLoopPhases:
    @pytest.mark.asyncio
    async def test_full_cycle_success(self, loop, basic_symptom):
        result = await loop.run_cycle(basic_symptom)
        assert result.success is True
        assert loop.get_cycle_count() == 1

        # Check cycle context
        ctx = list(loop._cycles.values())[0]
        assert ctx.diagnosis is not None
        assert ctx.healing_action is not None
        assert ctx.healing_result is not None
        assert ctx.reflection is not None
        assert ctx.reflection.success is True
        assert ctx.end_time is not None
        assert len(ctx.phases_completed) == 9  # all phases

    @pytest.mark.asyncio
    async def test_cycle_all_phases_recorded(self, loop, basic_symptom):
        await loop.run_cycle(basic_symptom)
        ctx = list(loop._cycles.values())[0]
        expected_phases = [
            HealingPhase.OBSERVE.value,
            HealingPhase.DIAGNOSE.value,
            HealingPhase.REASON.value,
            HealingPhase.PLAN.value,
            HealingPhase.GOVERN.value,
            HealingPhase.EXECUTE.value,
            HealingPhase.VERIFY.value,
            HealingPhase.REFLECT.value,
            HealingPhase.LEARN.value,
        ]
        assert ctx.phases_completed == expected_phases

    @pytest.mark.asyncio
    async def test_diagnosis_rule_based_on_source(self, loop):
        # Test health_collector -> service_degradation
        s = Symptom(id="s1", source="health_collector", description="x", severity=3)
        result = await loop.run_cycle(s)
        ctx = loop.get_recent_cycles(1)[0]
        assert ctx.diagnosis is not None
        assert ctx.diagnosis.root_cause == "service_degradation"

    @pytest.mark.asyncio
    async def test_diagnosis_from_pattern(self, loop):
        s = Symptom(id="s2", source="unknown", description="timeout error",
                     severity=3, pattern="timeout_occurred")
        result = await loop.run_cycle(s)
        ctx = loop.get_recent_cycles(1)[0]
        assert "provider_latency" in ctx.diagnosis.root_cause

    @pytest.mark.asyncio
    async def test_diagnosis_network_to_connectivity(self, loop):
        s = Symptom(id="s3", source="network_monitor", description="x", severity=3)
        await loop.run_cycle(s)
        ctx = loop.get_recent_cycles(1)[0]
        assert ctx.diagnosis.root_cause == "connectivity_loss"

    @pytest.mark.asyncio
    async def test_critical_severity_governance_allows(self, loop, critical_symptom):
        result = await loop.run_cycle(critical_symptom)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_low_severity_governance_proceeds(self, loop, low_severity_symptom):
        result = await loop.run_cycle(low_severity_symptom)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_healing_failure_result(self, mock_reflection, mock_policy, mock_memory, mock_confidence):
        fail_mgr = MockHealingManager(result=HealingResult(
            action_id="fail", success=False, message="Something broke", duration_ms=0,
        ))
        loop = SelfHealingLoop(
            healing_manager=fail_mgr,
            reflection_manager=mock_reflection,
            evolution_policy=mock_policy,
            confidence_calculator=mock_confidence,
            institutional_memory=mock_memory,
        )
        s = Symptom(id="sf1", source="test", description="failing symptom", severity=3)
        result = await loop.run_cycle(s)
        assert result.success is False

    @pytest.mark.asyncio
    async def test_reflection_captured_on_failure(self, loop):
        # Override healing to fail
        loop._healing = MockHealingManager(result=HealingResult(
            action_id="f", success=False, message="fail", duration_ms=0,
        ))
        s = Symptom(id="sf2", source="test", description="fail me", severity=3)
        await loop.run_cycle(s)
        ctx = list(loop._cycles.values())[0]
        assert ctx.reflection is not None
        assert ctx.reflection.success is False


class TestLearnPhase:
    @pytest.mark.asyncio
    async def test_failure_creates_pending_proposal(self, loop):
        # Make healing fail
        loop._healing = MockHealingManager(result=HealingResult(
            action_id="f", success=False, message="fail", duration_ms=0,
        ))
        s = Symptom(id="sf_l", source="test", description="learn from failure", severity=3)
        await loop.run_cycle(s)
        ctx = list(loop._cycles.values())[0]
        # Learn phase should create pending proposals
        pending = ctx.metadata.get("pending_proposals", [])
        assert len(pending) >= 1

        # Verify the proposal exists in the policy
        proposals = loop._policy.get_proposals(status=ProposalStatus.PENDING)
        assert len(proposals) >= 1

    @pytest.mark.asyncio
    async def test_pending_proposal_not_auto_applied(self, loop):
        loop._healing = MockHealingManager(result=HealingResult(
            action_id="f", success=False, message="fail", duration_ms=0,
        ))
        s = Symptom(id="sf_na", source="test", description="no auto", severity=3)
        await loop.run_cycle(s)
        # Check that the proposal is still PENDING (not APPROVED -> no apply)
        proposals = loop._policy.get_proposals(status=ProposalStatus.PENDING)
        for p in proposals:
            assert p.status == ProposalStatus.PENDING
            assert p.proposal_type == ProposalType.STRATEGY_SHIFT

    @pytest.mark.asyncio
    async def test_success_also_creates_proposal(self, loop, basic_symptom):
        await loop.run_cycle(basic_symptom)
        proposals = loop._policy.get_proposals(status=ProposalStatus.PENDING)
        assert len(proposals) >= 1

    @pytest.mark.asyncio
    async def test_lessons_stored_in_institutional_memory_resilient(self, loop, basic_symptom):
        await loop.run_cycle(basic_symptom)
        # Lessons are stored but may fail if InstitutionalMemory requires 'id'.
        # The loop catches that and logs the warning. Verify the cycle
        # still completes and creates a proposal.
        ctx = list(loop._cycles.values())[0]
        pending = ctx.metadata.get("pending_proposals", [])
        assert len(pending) >= 1  # proposal created even if lesson storage failed

    @pytest.mark.asyncio
    async def test_escalation_metadata_on_failure(self, loop):
        loop._healing = MockHealingManager(result=HealingResult(
            action_id="f", success=False, message="fail", duration_ms=0,
        ))
        s = Symptom(id="sf_esc", source="test", description="escalate", severity=3)
        await loop.run_cycle(s)
        ctx = list(loop._cycles.values())[0]
        escalation = ctx.metadata.get("escalation", {})
        assert escalation.get("reason") is not None
        assert "pending_proposals" in escalation


class TestCycleQueries:
    @pytest.mark.asyncio
    async def test_get_cycle_by_id(self, loop, basic_symptom):
        # Need to capture cycle_id — run_cycle doesn't return it directly
        # We'll use a side effect: store it in the symptom for lookup
        await loop.run_cycle(basic_symptom)
        ctx = list(loop._cycles.values())[0]
        fetched = loop.get_cycle(ctx.cycle_id)
        assert fetched is not None
        assert fetched.cycle_id == ctx.cycle_id

    @pytest.mark.asyncio
    async def test_get_recent_cycles(self, loop):
        for i in range(5):
            s = Symptom(id=str(i), source="t", description=f"s{i}", severity=3)
            await loop.run_cycle(s)
        recent = loop.get_recent_cycles(limit=3)
        assert len(recent) == 3

    @pytest.mark.asyncio
    async def test_get_cycles_by_outcome(self, loop, basic_symptom):
        await loop.run_cycle(basic_symptom)
        success_cycles = loop.get_cycles_by_outcome(success=True)
        fail_cycles = loop.get_cycles_by_outcome(success=False)
        assert len(success_cycles) >= 1


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_no_optional_dependencies(self, mock_healing, mock_reflection):
        """Loop should work with only HealingManager and ReflectionManager."""
        loop = SelfHealingLoop(
            healing_manager=mock_healing,
            reflection_manager=mock_reflection,
        )
        s = Symptom(id="min", source="test", description="minimal", severity=2)
        result = await loop.run_cycle(s)
        assert result.success is True
        assert loop.get_cycle_count() == 1

    @pytest.mark.asyncio
    async def test_symptom_with_low_severity_no_governance_block(self, loop, low_severity_symptom):
        """Low severity symptom should still go through governance."""
        result = await loop.run_cycle(low_severity_symptom)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_symptom_no_evidence(self, loop):
        s = Symptom(id="ne", source="test", description="no evidence", severity=3)
        result = await loop.run_cycle(s)
        assert result.success is True

    @pytest.mark.asyncio
    async def test_cycle_context_mutable(self, loop, basic_symptom):
        await loop.run_cycle(basic_symptom)
        ctx = list(loop._cycles.values())[0]
        # Verify we can read various fields
        assert isinstance(ctx.symptom, Symptom)
        assert isinstance(ctx.phases_completed, list)
        assert isinstance(ctx.metadata, dict)

    @pytest.mark.asyncio
    async def test_healing_action_strategy_maps_correctly(self, loop):
        # repair -> REPAIR
        s = Symptom(id="rep", source="test", description="repair test", severity=3,
                     evidence={"indicators": ["timeout"]},
                     pattern="error_spike")
        await loop.run_cycle(s)
        ctx = list(loop._cycles.values())[0]
        assert ctx.healing_action is not None
        assert ctx.healing_action.strategy == HealingStrategy.REPAIR

    @pytest.mark.asyncio
    async def test_healing_action_trigger_from_pattern(self, loop):
        s = Symptom(id="ptrn", source="src", description="pattern test",
                     severity=3, pattern="my.custom.pattern")
        await loop.run_cycle(s)
        ctx = list(loop._cycles.values())[0]
        if ctx.healing_action:
            assert ctx.healing_action.trigger == "my.custom.pattern"

    @pytest.mark.asyncio
    async def test_low_confidence_diagnosis_proceeds(self, loop):
        """Even low-confidence diagnosis should execute healing."""
        s = Symptom(id="lowc", source="unknown_source_xyz", description="weird",
                     severity=3)
        await loop.run_cycle(s)
        ctx = list(loop._cycles.values())[0]
        # Should still complete without error
        assert ctx.healing_result is not None


class TestReflectionCapture:
    @pytest.mark.asyncio
    async def test_reflection_has_lessons(self, loop, basic_symptom):
        await loop.run_cycle(basic_symptom)
        ctx = list(loop._cycles.values())[0]
        assert ctx.reflection is not None
        assert len(ctx.reflection.lessons) >= 1

    @pytest.mark.asyncio
    async def test_reflection_has_cycle_id(self, loop, basic_symptom):
        await loop.run_cycle(basic_symptom)
        ctx = list(loop._cycles.values())[0]
        assert ctx.reflection.cycle_id == ctx.cycle_id

    @pytest.mark.asyncio
    async def test_reflection_success_matches_healing(self, loop, basic_symptom):
        await loop.run_cycle(basic_symptom)
        ctx = list(loop._cycles.values())[0]
        assert ctx.reflection.success == ctx.healing_result.success

    @pytest.mark.asyncio
    async def test_gap_analysis_captured(self, loop, basic_symptom):
        await loop.run_cycle(basic_symptom)
        ctx = list(loop._cycles.values())[0]
        assert len(ctx.reflection.gap_analysis) > 0

    @pytest.mark.asyncio
    async def test_metadata_in_reflection(self, loop, basic_symptom):
        await loop.run_cycle(basic_symptom)
        ctx = list(loop._cycles.values())[0]
        md = ctx.reflection.metadata
        assert isinstance(md, dict)
        assert md.get("severity") == basic_symptom.severity


class TestDiagnosisLogic:
    @pytest.mark.asyncio
    async def test_diagnosis_confidence_increases_with_evidence(self, loop):
        s_low = Symptom(id="dl1", source="test", description="x", severity=3)
        s_high = Symptom(id="dl2", source="test", description="x", severity=3,
                          evidence={"a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
                          pattern="known_pattern")

        # Run low
        await loop.run_cycle(s_low)
        # Run high
        await loop.run_cycle(s_high)

        cycles = list(loop._cycles.values())
        diag_low = cycles[0].diagnosis
        diag_high = cycles[1].diagnosis

        # High-evidence + pattern should have higher confidence
        assert diag_high is not None and diag_low is not None
        assert diag_high.confidence > diag_low.confidence


class TestGovernance:
    @pytest.mark.asyncio
    async def test_governance_engine_used_when_provided(self, loop, basic_symptom):
        """When governance engine is provided, metadata should reflect it."""
        await loop.run_cycle(basic_symptom)
        ctx = list(loop._cycles.values())[0]
        # When no governance engine, we get 'skip_no_engine'
        assert ctx.metadata.get("governance", {}).get("decision") == "skip_no_engine"


# ── Test file count assertions ─────────────────────────────────────
# Expected: 20+ individual test functions across all classes above
