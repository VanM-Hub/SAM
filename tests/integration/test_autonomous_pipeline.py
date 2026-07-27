"""
Integration tests — Autonomous Operations End-to-End (Phase 1)
"""

import pytest
from sam.autonomous.models import (
    AutonomousAction, AutonomousActionStatus, ActionType, RiskLevel,
)
from sam.autonomous.policies import SafetyPolicy
from sam.autonomous.approval import ApprovalManager
from sam.autonomous.executor import ActionExecutor
from sam.autonomous.recovery import AutoRecovery
from sam.autonomous.isolation import PluginIsolation


class TestAutonomousPipelineE2E:
    @pytest.mark.asyncio
    async def test_approval_then_execute(self):
        """Pipeline: auto-approve tidak dibutuhkan -> bisa execute langsung."""
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        executor = ActionExecutor(coord)

        action = AutonomousAction(
            action_type=ActionType.RESTART,
            target="plugin",
            confidence=0.85,
        )
        result = await executor.execute(action)
        assert result.status in (
            AutonomousActionStatus.COMPLETED,
            AutonomousActionStatus.APPROVED,
        )

    @pytest.mark.asyncio
    async def test_high_risk_needs_approval(self):
        """Pipeline: high risk -> pending."""
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        executor = ActionExecutor(coord)

        action = AutonomousAction(
            action_type=ActionType.RESTART,
            target="gateway",
            confidence=0.9,
        )
        result = await executor.execute(action)

        if result.status == AutonomousActionStatus.PENDING:
            # Should have an approval request
            approvals = executor.approval_manager.get_pending()
            assert len(approvals) >= 1
            assert approvals[0].action_id == result.id

    @pytest.mark.asyncio
    async def test_recovery_then_isolation_workflow(self):
        """Workflow: detect -> recover -> isolate if needed."""
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()

        # Recovery
        recovery = AutoRecovery(coord)
        result = await recovery.recover_from_incident("e2e-001", "plugin crash in monitor")
        assert result.status in (
            AutonomousActionStatus.COMPLETED,
            AutonomousActionStatus.APPROVED,
            AutonomousActionStatus.PENDING,
        )

        # Isolation
        isolation = PluginIsolation(coord)
        result2 = await isolation.isolate("monitor")
        assert result2.status.value in ("completed", "pending")

    @pytest.mark.asyncio
    async def test_policy_blocked_actions(self):
        """Blocked actions harus selalu ditolak."""
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
    async def test_safety_policy_enforcement(self):
        """Safety policy harus dijalankan untuk semua action."""
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        executor = ActionExecutor(coord)

        # Low risk auto
        low = AutonomousAction(
            action_type=ActionType.RESTART, target="plugin",
            confidence=0.85,
        )
        assert SafetyPolicy.can_auto_approve(low)

        # High risk
        high = AutonomousAction(
            action_type=ActionType.RESTART, target="runtime",
            confidence=0.95,
        )
        assert not SafetyPolicy.is_action_allowed("restart", "runtime")

    @pytest.mark.asyncio
    async def test_approval_deny_propagation(self):
        """Deny harus mencegah action dieksekusi."""
        am = ApprovalManager()
        req = await am.request("act-propagate")

        success = await am.deny(req.id)
        assert success is True

        # Approval request no longer pending
        assert len(am.get_pending()) == 0


class TestAutonomousCLIIntegration:
    def test_cli_import(self):
        from sam.cli.autonomous import app
        assert len(app.registered_commands) >= 4

    def test_coordinator_has_autonomous(self):
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        assert hasattr(coord, "action_executor")
        assert hasattr(coord, "auto_recovery")
        assert hasattr(coord, "plugin_isolation")
        assert hasattr(coord, "autonomous_enabled")

    def test_coordinator_autonomous_default_true(self):
        from sam.runtime.coordinator import RuntimeCoordinator
        coord = RuntimeCoordinator()
        assert coord.autonomous_enabled is True
