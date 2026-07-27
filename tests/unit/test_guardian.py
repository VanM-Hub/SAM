"""
Unit tests — Guardian Kernel (Phase 0)
"""

import pytest
from sam.guardian.observer import ObserverEngine
from sam.guardian.analyzer import AnalyzerEngine
from sam.guardian.decision import DecisionEngine, GuardianDecision
from sam.guardian.policy import PolicyEngine
from sam.guardian.action import ActionEngine
from sam.guardian.verification import VerificationEngine
from sam.guardian.pipeline import GuardianPipeline
from sam.runtime.coordinator import RuntimeCoordinator
from sam.contracts import DesiredOperationalState


# ─── Observer Engine ───────────────────────────────────────────────

class TestObserverEngine:
    @pytest.mark.asyncio
    async def test_observe_returns_dict(self):
        coord = RuntimeCoordinator()
        observer = ObserverEngine(coord)
        obs = await observer.observe()
        assert isinstance(obs, dict)
        assert "runtime_state" in obs
        assert "health_score" in obs
        assert "timestamp" in obs

    @pytest.mark.asyncio
    async def test_observe_has_expected_keys(self):
        coord = RuntimeCoordinator()
        observer = ObserverEngine(coord)
        obs = await observer.observe()
        expected = ["runtime_state", "session", "plugins", "knowledge", "memory", "workflow", "health_score", "timestamp"]
        for key in expected:
            assert key in obs, f"Missing key: {key}"


# ─── Analyzer Engine ───────────────────────────────────────────────

class TestAnalyzerEngine:
    @pytest.mark.asyncio
    async def test_no_drift_when_healthy(self):
        dos = DesiredOperationalState(runtime_state="RUNNING")
        analyzer = AnalyzerEngine(dos)
        obs = {
            "runtime_state": "running",
            "plugins": {"loaded": 14, "expected": 14},
            "knowledge": {"loaded": True},
            "memory": {"healthy": True},
            "health_score": 100.0,
        }
        drifts = await analyzer.analyze(obs)
        assert len(drifts) == 0

    @pytest.mark.asyncio
    async def test_drift_runtime_state(self):
        dos = DesiredOperationalState(runtime_state="RUNNING")
        analyzer = AnalyzerEngine(dos)
        obs = {
            "runtime_state": "safe_mode",
            "plugins": {"loaded": 14},
            "knowledge": {"loaded": True},
            "memory": {"healthy": True},
            "health_score": 100.0,
        }
        drifts = await analyzer.analyze(obs)
        assert any(d["type"] == "runtime_state" for d in drifts)

    @pytest.mark.asyncio
    async def test_drift_plugins(self):
        dos = DesiredOperationalState(plugins_expected=14)
        analyzer = AnalyzerEngine(dos)
        obs = {
            "runtime_state": "running",
            "plugins": {"loaded": 5},
            "knowledge": {"loaded": True},
            "memory": {"healthy": True},
            "health_score": 100.0,
        }
        drifts = await analyzer.analyze(obs)
        assert any(d["type"] == "plugins" for d in drifts)

    @pytest.mark.asyncio
    async def test_drift_health(self):
        dos = DesiredOperationalState(min_health_score=95.0)
        analyzer = AnalyzerEngine(dos)
        obs = {
            "runtime_state": "running",
            "plugins": {"loaded": 14},
            "knowledge": {"loaded": True},
            "memory": {"healthy": True},
            "health_score": 50.0,
        }
        drifts = await analyzer.analyze(obs)
        assert any(d["type"] == "health" for d in drifts)

    @pytest.mark.asyncio
    async def test_multiple_drifts(self):
        dos = DesiredOperationalState(runtime_state="RUNNING", plugins_expected=10)
        analyzer = AnalyzerEngine(dos)
        obs = {
            "runtime_state": "crashed",
            "plugins": {"loaded": 2},
            "knowledge": {"loaded": False},
            "memory": {"healthy": False},
            "health_score": 30.0,
        }
        drifts = await analyzer.analyze(obs)
        assert len(drifts) >= 3


# ─── Policy Engine ─────────────────────────────────────────────────

class TestPolicyEngine:
    @pytest.mark.asyncio
    async def test_policy_allows_by_default(self):
        policy = PolicyEngine()
        result = await policy.check([], "minor")
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_policy_returns_reason(self):
        policy = PolicyEngine()
        result = await policy.check([], "minor")
        assert "reason" in result
        assert "details" in result
        assert "mission" in result["details"]


# ─── Action Engine ─────────────────────────────────────────────────

class TestActionEngine:
    @pytest.mark.asyncio
    async def test_execute_empty_plan_returns_false(self):
        action = ActionEngine()
        result = await action.execute([])
        assert result is False

    @pytest.mark.asyncio
    async def test_execute_returns_true(self):
        action = ActionEngine()
        result = await action.execute(["restart_runtime"])
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_returns_true(self):
        action = ActionEngine()
        result = await action.verify(["restart_runtime"])
        assert result is True


# ─── Verification Engine ───────────────────────────────────────────

class TestVerificationEngine:
    @pytest.mark.asyncio
    async def test_verify_empty_plan_false(self):
        verifier = VerificationEngine()
        result = await verifier.verify([])
        assert result is False

    @pytest.mark.asyncio
    async def test_verify_returns_true(self):
        verifier = VerificationEngine()
        result = await verifier.verify(["restart_runtime"])
        assert result is True


# ─── Decision Engine ───────────────────────────────────────────────

class TestDecisionEngine:
    @pytest.mark.asyncio
    async def test_make_decision_with_drifts(self):
        policy = PolicyEngine()
        action = ActionEngine()
        decision = DecisionEngine(policy, action)

        drifts = [
            {"type": "runtime_state", "expected": "RUNNING", "actual": "safe_mode", "severity": "critical"},
        ]
        result = await decision.make_decision(drifts)
        assert isinstance(result, GuardianDecision)
        assert result.severity == "critical"
        assert result.risk == "high"

    @pytest.mark.asyncio
    async def test_make_decision_low_risk_auto_approved(self):
        policy = PolicyEngine()
        action = ActionEngine()
        decision = DecisionEngine(policy, action)

        drifts = [
            {"type": "health", "expected": 95.0, "actual": 92.0, "severity": "moderate"},
        ]
        result = await decision.make_decision(drifts)
        assert result.approved is True
        assert result.executed is True
        assert result.verified is True

    @pytest.mark.asyncio
    async def test_high_risk_not_auto_approved(self):
        policy = PolicyEngine()
        action = ActionEngine()
        decision = DecisionEngine(policy, action)

        drifts = [
            {"type": "runtime_state", "expected": "RUNNING", "actual": "crashed", "severity": "critical"},
        ]
        result = await decision.make_decision(drifts)
        # High risk → butuh human approval
        assert result.approved is False

    @pytest.mark.asyncio
    async def test_decision_has_audit_fields(self):
        policy = PolicyEngine()
        action = ActionEngine()
        decision = DecisionEngine(policy, action)

        drifts = [{"type": "health", "expected": 95.0, "actual": 80.0, "severity": "moderate"}]
        result = await decision.make_decision(drifts)
        assert result.decision_id is not None
        assert result.created_at is not None
        assert result.duration_ms >= 0


# ─── Guardian Pipeline (Full Cycle) ────────────────────────────────

class TestGuardianPipeline:
    @pytest.mark.asyncio
    async def test_run_cycle_without_coordinator_start(self):
        coord = RuntimeCoordinator()
        dos = DesiredOperationalState()
        pipeline = GuardianPipeline(coord, dos)

        result = await pipeline.run_cycle()
        assert "status" in result
        assert "drifts" in result
        assert pipeline.cycle_count == 1

    @pytest.mark.asyncio
    async def test_run_cycle_healthy(self):
        coord = RuntimeCoordinator()
        # Set DOS to match initial state
        dos = DesiredOperationalState(runtime_state="INITIALIZING")
        pipeline = GuardianPipeline(coord, dos)

        result = await pipeline.run_cycle()
        assert result["status"] == "healthy"
        assert len(result["drifts"]) == 0

    @pytest.mark.asyncio
    async def test_run_cycle_detects_drift(self):
        coord = RuntimeCoordinator()
        dos = DesiredOperationalState(runtime_state="RUNNING")
        pipeline = GuardianPipeline(coord, dos)

        result = await pipeline.run_cycle()
        assert result["status"] == "completed"
        assert len(result["drifts"]) > 0

    @pytest.mark.asyncio
    async def test_multiple_cycles(self):
        coord = RuntimeCoordinator()
        dos = DesiredOperationalState()
        pipeline = GuardianPipeline(coord, dos)

        results = await pipeline.run_cycles(count=3, interval_sec=0.01)
        assert len(results) == 3
        assert pipeline.cycle_count == 3
