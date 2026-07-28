"""
Failure Recovery — menangani kegagalan eksekusi.

Ketika eksekusi gagal:
  1. Catat audit failure
  2. Jika rollback tersedia → execute rollback
  3. Jika tidak ada rollback → catat sebagai permanent failure
  4. Berikan penjelasan evidence-based ke Conversation
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from .execution_plan import ExecutionPlan, ExecutionPlanBuilder
from .audit import AuditEventType, get_audit_trail
from .sandbox import ExecutionSandbox
from .real_executor import FilesystemExecutor, CommandExecutor, ProcessExecutor, WorkspaceExecutor


@dataclass
class RecoveryResult:
    """Hasil recovery — lengkap dengan timeline dan evidence."""
    plan_id: str
    plan_title: str

    # Failure info
    failure_reason: str
    failure_action: str = ""
    failure_at: str = ""

    # Rollback
    rollback_available: bool = False
    rollback_executed: bool = False
    rollback_success: bool = False

    # Recovery
    recovered: bool = False
    recovery_actions: List[str] = field(default_factory=list)

    # Audit
    audit_entry_ids: List[str] = field(default_factory=list)

    # Human notification
    requires_human_intervention: bool = False
    human_instruction: str = ""

    def to_text(self) -> str:
        lines = [
            "=== Failure Recovery: {} ===".format(self.plan_title),
            "Failure: {}".format(self.failure_reason),
        ]
        if self.rollback_executed:
            lines.append("Rollback: {} (success={})".format(
                "EXECUTED" if self.rollback_executed else "NOT EXECUTED",
                self.rollback_success,
            ))
        lines.append("Recovered: {}".format(self.recovered))
        if self.requires_human_intervention:
            lines.append("Human intervention REQUIRED: {}".format(self.human_instruction))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "failure_reason": self.failure_reason,
            "rollback_executed": self.rollback_executed,
            "rollback_success": self.rollback_success,
            "recovered": self.recovered,
            "requires_human_intervention": self.requires_human_intervention,
        }


class RecoveryEngine:
    """Engine untuk failure recovery.

    Method utama: recover(plan, failure_reason, failed_action) -> RecoveryResult

    Recovery bukan otomatis — hanya framework.
    Semua recovery dicatat di audit trail.
    Jika tidak bisa recover otomatis → butuh human intervention.
    """

    def __init__(self, sandbox: Optional[ExecutionSandbox] = None):
        self._sandbox = sandbox or ExecutionSandbox()
        self._audit = get_audit_trail()
        self._executors = {
            'filesystem': FilesystemExecutor(self._sandbox),
            'command': CommandExecutor(self._sandbox),
            'process': ProcessExecutor(self._sandbox),
            'workspace': WorkspaceExecutor(self._sandbox),
        }

    def recover(self, plan: ExecutionPlan, failure_reason: str,
                failed_action_index: int = -1) -> RecoveryResult:
        """Recover dari kegagalan.

        Args:
            plan: ExecutionPlan yang gagal
            failure_reason: Penyebab kegagalan
            failed_action_index: Index action yang gagal

        Returns:
            RecoveryResult
        """
        result = RecoveryResult(
            plan_id=plan.plan_id,
            plan_title=plan.source_decision_title or plan.plan_id,
            failure_reason=failure_reason,
            failure_action=plan.actions[failed_action_index].title if 0 <= failed_action_index < len(plan.actions) else "unknown",
            failure_at=datetime.now().isoformat(),
        )

        # Audit failure
        self._audit.record(
            AuditEventType.EXECUTION_FAILED,
            plan.plan_id, "recovery_engine",
            "Execution failed: {}".format(failure_reason),
            description="Failed at action index: {}".format(failed_action_index),
            actor="RecoveryEngine",
        )

        # Check rollback availability
        result.rollback_available = len(plan.rollback_steps) > 0

        if result.rollback_available:
            # Execute each rollback step
            all_rollback_ok = True
            for step in plan.rollback_steps:
                try:
                    # Simulate rollback via appropriate executor
                    executor = self._get_executor_by_category(plan)
                    ok = executor.rollback(plan, failure_reason)
                    result.recovery_actions.append("Rollback step for action [{}]: {}".format(
                        step.action_index, step.inverse_title))
                    if not ok:
                        all_rollback_ok = False
                except Exception as e:
                    all_rollback_ok = False
                    result.recovery_actions.append("Rollback failed: {}".format(str(e)))

            result.rollback_executed = True
            result.rollback_success = all_rollback_ok

            if all_rollback_ok:
                result.recovered = True
                self._audit.record(
                    AuditEventType.ROLLBACK_COMPLETED,
                    plan.plan_id, "recovery_engine",
                    "Rollback completed successfully",
                    actor="RecoveryEngine",
                )
            else:
                result.recovered = False
                result.requires_human_intervention = True
                result.human_instruction = "Rollback partially failed. Manual inspection required."
                self._audit.record(
                    AuditEventType.ROLLBACK_FAILED,
                    plan.plan_id, "recovery_engine",
                    "Rollback failed — human intervention required",
                    actor="RecoveryEngine",
                )
        else:
            # No rollback available — permanent failure
            result.recovered = False
            result.requires_human_intervention = True

            if "disk" in failure_reason.lower():
                result.human_instruction = "Disk operation failed. Files may be partially deleted. Check file system manually."
            elif "connection" in failure_reason.lower() or "database" in failure_reason.lower():
                result.human_instruction = "Database connection failed. Check database service status and logs manually."
            elif "permission" in failure_reason.lower():
                result.human_instruction = "Permission denied. Check file/directory permissions manually."
            else:
                result.human_instruction = "Execution failed without rollback option. Manual investigation required."

            self._audit.record(
                AuditEventType.COMPENSATION_TRIGGERED,
                plan.plan_id, "recovery_engine",
                "No rollback available. Manual intervention required.",
                description="Human instruction: {}".format(result.human_instruction),
                actor="RecoveryEngine",
            )

        return result

    def _get_executor_by_category(self, plan: ExecutionPlan):
        """Pilih executor berdasarkan kategori action pertama."""
        if not plan.actions:
            return list(self._executors.values())[0]
        category = getattr(plan.actions[0], 'category', 'general').lower()
        for cat, executor in self._executors.items():
            if cat in category:
                return executor
        return self._executors['command']
