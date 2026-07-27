"""
Action Executor — Phase 1

Menjalankan tindakan autonomous: restart, recover, resume, isolate, escalate.
Terintegrasi dengan SafetyPolicy, ApprovalManager, dan RuntimeCoordinator.
"""

import asyncio
import structlog
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from .models import (
    AutonomousAction, AutonomousActionStatus, ActionType, RiskLevel,
)
from .policies import SafetyPolicy
from .approval import ApprovalManager

logger = structlog.get_logger()


class ActionExecutor:
    """Executor untuk tindakan autonomous — safety-first execution pipeline."""

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.approval_manager = ApprovalManager()
        self._actions: Dict[str, AutonomousAction] = {}

    async def execute(self, action: AutonomousAction) -> AutonomousAction:
        """Eksekusi tindakan autonomous dengan safety pipeline.

        Pipeline:
          1. Validate action (allowed?)
          2. Assign risk level
          3. Check if needs human approval
          4. Auto-approve or wait for approval
          5. Execute
          6. Verify result
        """
        # 1. Validate
        if not SafetyPolicy.is_action_allowed(action.action_type.value, action.target):
            action.status = AutonomousActionStatus.DENIED
            action.error = "Action blocked by safety policy"
            self._actions[action.id] = action
            logger.warning("action_blocked", action_id=action.id, target=action.target)
            return action

        # 2. Assign risk
        action.risk_level = SafetyPolicy.get_risk(action.action_type.value, action.target)

        # Store before execution
        self._actions[action.id] = action

        # 3. Human approval check
        if SafetyPolicy.requires_approval(action):
            approval = await self.approval_manager.request(
                action.id,
                reason="Action {0} on {1} has risk level {2} (confidence: {3:.0%})".format(
                    action.action_type.value, action.target,
                    action.risk_level.value, action.confidence,
                ),
            )
            # Wait for approval (simulasi — in production, polling or event-driven)
            action.status = AutonomousActionStatus.PENDING
            logger.info(
                "action_awaiting_approval",
                action_id=action.id,
                request_id=approval.id,
                risk=action.risk_level.value,
            )
            # Return pending — caller handles waiting
            return action

        # 4. Auto-approve
        if SafetyPolicy.can_auto_approve(action):
            action.status = AutonomousActionStatus.APPROVED
            logger.info("action_auto_approved", action_id=action.id, risk=action.risk_level.value)
        else:
            # Needs manual approval (low confidence)
            approval = await self.approval_manager.request(
                action.id,
                reason="Low confidence ({0:.0%}) for action on {1}".format(
                    action.confidence, action.target,
                ),
            )
            action.status = AutonomousActionStatus.PENDING
            logger.info("action_low_confidence_awaiting_approval", action_id=action.id)
            return action

        # 5. Execute
        return await self._do_execute(action)

    async def _do_execute(self, action: AutonomousAction) -> AutonomousAction:
        """Internal execution — eksekusi action yang sudah approved."""
        action.status = AutonomousActionStatus.EXECUTING
        logger.info("action_executing", action_id=action.id, action_type=action.action_type.value)

        try:
            result = await self._execute_action(action)
            action.status = AutonomousActionStatus.COMPLETED
            action.result = result
            action.completed_at = datetime.utcnow()
            logger.info("action_completed", action_id=action.id, result=result)
        except Exception as e:
            action.status = AutonomousActionStatus.FAILED
            action.error = str(e)
            logger.error("action_failed", action_id=action.id, error=str(e))

        return action

    async def _execute_action(self, action: AutonomousAction) -> Dict[str, Any]:
        """Implementasi aktual dari action."""
        if action.action_type == ActionType.RESTART:
            return await self._restart(action.target)
        elif action.action_type == ActionType.RECOVER:
            return await self._recover()
        elif action.action_type == ActionType.RESUME:
            return await self._resume()
        elif action.action_type == ActionType.ISOLATE:
            return await self._isolate(action.target)
        elif action.action_type == ActionType.ESCALATE:
            return await self._escalate(action.target)
        return {"status": "unknown_action", "action_type": action.action_type.value}

    async def _restart(self, target: str) -> Dict[str, Any]:
        """Restart komponen target."""
        logger.info("restarting", target=target)
        await asyncio.sleep(0.3)  # simulasi
        return {"status": "restarted", "target": target}

    async def _recover(self) -> Dict[str, Any]:
        """Recovery runtime."""
        logger.info("recovering_runtime")
        if hasattr(self.coordinator, "recovery_manager"):
            await self.coordinator.recovery_manager.recover()
        return {"status": "recovered"}

    async def _resume(self) -> Dict[str, Any]:
        """Resume workflow."""
        logger.info("resuming_workflow")
        await asyncio.sleep(0.3)
        return {"status": "resumed"}

    async def _isolate(self, target: str) -> Dict[str, Any]:
        """Isolasi plugin atau komponen yang bermasalah."""
        logger.info("isolating", target=target)
        await asyncio.sleep(0.3)
        return {"status": "isolated", "target": target}

    async def _escalate(self, target: str) -> Dict[str, Any]:
        """Eskalasi ke manusia."""
        logger.info("escalating_to", target=target)
        return {"status": "escalated", "target": target}

    # ── Query methods ──────────────────────────────────────────────────

    def get_action(self, action_id: str) -> Optional[AutonomousAction]:
        return self._actions.get(action_id)

    def get_pending_actions(self) -> List[AutonomousAction]:
        return [a for a in self._actions.values() if a.status == AutonomousActionStatus.PENDING]

    def get_history(self, limit: int = 50) -> List[AutonomousAction]:
        all_actions = list(self._actions.values())
        return all_actions[-limit:] if limit else all_actions

    def get_actions_by_status(self, status: AutonomousActionStatus) -> List[AutonomousAction]:
        return [a for a in self._actions.values() if a.status == status]
