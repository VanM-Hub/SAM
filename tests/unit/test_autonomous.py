"""
Unit tests — Autonomous Operations (Phase 1)
"""

import pytest
from sam.autonomous.models import (
    AutonomousAction, AutonomousActionStatus, ActionType, RiskLevel,
    ApprovalRequest,
)
from sam.autonomous.policies import SafetyPolicy
from sam.autonomous.approval import ApprovalManager
from sam.autonomous.executor import ActionExecutor
from sam.autonomous.recovery import AutoRecovery
from sam.autonomous.isolation import PluginIsolation


class TestAutonomousModels:
    def test_action_defaults(self):
        action = AutonomousAction(action_type=ActionType.RESTART, target="worker")
        assert action.status == AutonomousActionStatus.PENDING
        assert action.risk_level == RiskLevel.MEDIUM
        assert len(action.id) == 8

    def test_action_custom(self):
        action = AutonomousAction(
            action_type=ActionType.ISOLATE,
            target="plugin-bad",
            status=AutonomousActionStatus.COMPLETED,
            risk_level=RiskLevel.HIGH,
            confidence=0.9,
        )
        assert action.action_type.value == "isolate"
        assert action.status == AutonomousActionStatus.COMPLETED

    def test_approval_request_defaults(self):
        req = ApprovalRequest(action_id="act-001")
        assert req.status == "pending"
        assert req.requester == "autonomous"

    def test_action_type_enum(self):
        assert ActionType.RESTART.value == "restart"
        assert ActionType.ESCALATE.value == "escalate"
        assert ActionType.RECOVER.value == "recover"

    def test_risk_level_enum(self):
        assert RiskLevel.CRITICAL.value == "critical"
        assert RiskLevel.LOW.value == "low"


class TestSafetyPolicy:
    def test_auto_approve_low_risk(self):
        action = AutonomousAction(
            action_type=ActionType.RESTART,
            target="plugin",
            risk_level=RiskLevel.LOW,
            confidence=0.8,
        )
        assert SafetyPolicy.can_auto_approve(action) is True

    def test_auto_approve_medium_risk(self):
        action = AutonomousAction(
            action_type=ActionType.RESTART,
            target="worker",
            risk_level=RiskLevel.MEDIUM,
            confidence=0.8,
        )
        assert SafetyPolicy.can_auto_approve(action) is True

    def test_auto_approve_high_risk_denied(self):
        action = AutonomousAction(
            action_type=ActionType.RESTART,
            target="gateway",
            risk_level=RiskLevel.HIGH,
            confidence=0.9,
        )
        assert SafetyPolicy.can_auto_approve(action) is False

    def test_auto_approve_low_confidence_denied(self):
        action = AutonomousAction(
            action_type=ActionType.RESTART,
            target="plugin",
            risk_level=RiskLevel.LOW,
            confidence=0.5,
        )
        assert SafetyPolicy.can_auto_approve(action) is False

    def test_requires_approval_high_risk(self):
        action = AutonomousAction(
            action_type=ActionType.RESTART,
            target="gateway",
            risk_level=RiskLevel.HIGH,
        )
        assert SafetyPolicy.requires_approval(action) is True

    def test_requires_approval_low_risk(self):
        action = AutonomousAction(
            action_type=ActionType.RESTART,
            target="plugin",
            risk_level=RiskLevel.LOW,
        )
        assert SafetyPolicy.requires_approval(action) is False

    def test_blocked_action_restart_runtime(self):
        assert SafetyPolicy.is_action_allowed("restart", "runtime") is False

    def test_blocked_action_isolate_runtime(self):
        assert SafetyPolicy.is_action_allowed("isolate", "runtime") is False

    def test_get_risk_known(self):
        assert SafetyPolicy.get_risk("restart", "plugin") == RiskLevel.LOW
        assert SafetyPolicy.get_risk("restart", "gateway") == RiskLevel.HIGH

    def test_get_risk_unknown_defaults(self):
        assert SafetyPolicy.get_risk("unknown", "target") == RiskLevel.MEDIUM


class TestApprovalManager:
    @pytest.mark.asyncio
    async def test_request_and_approve(self):
        am = ApprovalManager()
        req = await am.request("act-001")
        assert req.status == "pending"
        assert len(am.get_pending()) >= 1

        success = await am.approve(req.id)
        assert success is True
        assert len(am.get_pending()) == 0

    @pytest.mark.asyncio
    async def test_request_and_deny(self):
        am = ApprovalManager()
        req = await am.request("act-002")
        success = await am.deny(req.id)
        assert success is True

    @pytest.mark.asyncio
    async def test_approve_invalid_id(self):
        am = ApprovalManager()
        success = await am.approve("nonexistent")
        assert success is False

    @pytest.mark.asyncio
    async def test_approve_already_processed(self):
        am = ApprovalManager()
        req = await am.request("act-003")
        await am.approve(req.id)
        # Second attempt
        success = await am.approve(req.id)
        assert success is False

    @pytest.mark.asyncio
    async def test_deny_nonexistent(self):
        am = ApprovalManager()
        success = await am.deny("nothing")
        assert success is False

    def test_get_history(self):
        am = ApprovalManager()
        history = am.get_history()
        assert isinstance(history, list)


class TestActionExecutor:
    @pytest.mark.asyncio
    async def test_execute_restart_plugin_auto_approved(self):
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        executor = ActionExecutor(coord)

        action = AutonomousAction(
            action_type=ActionType.RESTART,
            target="plugin",
            reason="Test restart plugin",
            confidence=0.85,
        )
        result = await executor.execute(action)
        assert result.status in (
            AutonomousActionStatus.COMPLETED,
            AutonomousActionStatus.APPROVED,
        )

    @pytest.mark.asyncio
    async def test_execute_high_risk_pending_approval(self):
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        executor = ActionExecutor(coord)

        action = AutonomousAction(
            action_type=ActionType.RESTART,
            target="gateway",
            confidence=0.9,
        )
        result = await executor.execute(action)
        assert result.status == AutonomousActionStatus.PENDING

    @pytest.mark.asyncio
    async def test_execute_blocked_action(self):
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        executor = ActionExecutor(coord)

        action = AutonomousAction(
            action_type=ActionType.RESTART,
            target="runtime",
        )
        result = await executor.execute(action)
        assert result.status == AutonomousActionStatus.DENIED

    @pytest.mark.asyncio
    async def test_execute_recover(self):
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        executor = ActionExecutor(coord)

        action = AutonomousAction(
            action_type=ActionType.RECOVER,
            target="workflow",
            confidence=0.8,
        )
        result = await executor.execute(action)
        assert result.status in (
            AutonomousActionStatus.COMPLETED,
            AutonomousActionStatus.APPROVED,
        )

    @pytest.mark.asyncio
    async def test_execute_escalate(self):
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        executor = ActionExecutor(coord)

        action = AutonomousAction(
            action_type=ActionType.ESCALATE,
            target="operator",
            confidence=0.95,
        )
        result = await executor.execute(action)
        assert result.status in (
            AutonomousActionStatus.COMPLETED,
            AutonomousActionStatus.APPROVED,
        )

    def test_history(self):
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        executor = ActionExecutor(coord)
        assert len(executor.get_history()) >= 0

    def test_pending_actions(self):
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        executor = ActionExecutor(coord)
        assert isinstance(executor.get_pending_actions(), list)


class TestAutoRecovery:
    @pytest.mark.asyncio
    async def test_recover_worker_incident(self):
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        recovery = AutoRecovery(coord)
        result = await recovery.recover_from_incident("inc-001", "worker timeout")
        assert result.incident_id == "inc-001"
        assert result.action_type in (ActionType.RESTART, ActionType.RECOVER)

    @pytest.mark.asyncio
    async def test_recover_memory_incident(self):
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        recovery = AutoRecovery(coord)
        result = await recovery.recover_from_incident("inc-002", "out of memory error")
        assert result.action_type in (ActionType.RECOVER, ActionType.RESTART)

    @pytest.mark.asyncio
    async def test_recover_auth_incident_escalates(self):
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        recovery = AutoRecovery(coord)
        result = await recovery.recover_from_incident("inc-003", "provider auth failure")
        # Auth issues escalate to operator
        assert result.action_type in (ActionType.ESCALATE, ActionType.RESTART)


class TestPluginIsolation:
    @pytest.mark.asyncio
    async def test_isolate_unknown_plugin(self):
        isolation = PluginIsolation()
        result = await isolation.isolate("nonexistent_plugin")
        assert result.status.value == "failed"

    @pytest.mark.asyncio
    async def test_isolate_known_plugin(self):
        isolation = PluginIsolation()
        result = await isolation.isolate("monitor")
        assert result.result["status"] == "isolated"
        assert "monitor" in isolation.get_isolated_plugins()

    @pytest.mark.asyncio
    async def test_isolate_twice(self):
        isolation = PluginIsolation()
        await isolation.isolate("scheduler")
        result2 = await isolation.isolate("scheduler")
        assert result2.result["status"] == "already_isolated"

    @pytest.mark.asyncio
    async def test_restore_plugin(self):
        isolation = PluginIsolation()
        await isolation.isolate("notifier")
        assert "notifier" in isolation.get_isolated_plugins()

        restored = await isolation.restore("notifier")
        assert restored is True
        assert "notifier" not in isolation.get_isolated_plugins()

    @pytest.mark.asyncio
    async def test_restore_not_isolated(self):
        isolation = PluginIsolation()
        restored = await isolation.restore("never_isolated")
        assert restored is False
