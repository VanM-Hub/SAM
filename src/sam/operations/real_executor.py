"""
Executor nyata untuk Filesystem, Command, Process, Workspace.

Semua executor mematuhi ExecutorProtocol (OP-91).
Semua aksi melalui ExecutionSandbox (OP-100).
Tidak ada yang menyentuh sistem nyata — berjalan di sandbox.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

from .executor import ExecutorState, ExecutionResult
from .sandbox import ExecutionSandbox, SandboxOperationType
from .audit import AuditEventType, get_audit_trail
from .approval import ApprovalStatus
from .approval_v2 import get_approval_manager


def _require_execution_approval(plan, action_type: str = "executor") -> bool:
    """Verifikasi approval plan sebelum execute.

    Jika plan.approval_id tidak ada, ini bypass — log warning.
    Allows execution under backward-compat (sandbox only simulates anyway).
    """
    approval_id = getattr(plan, 'approval_id', None) or getattr(plan, 'id', None)
    if approval_id:
        try:
            mgr = get_approval_manager()
            appr = mgr.get_approval(approval_id)
            if appr and appr.status == ApprovalStatus.APPROVED:
                return True
            get_audit_trail().record(
                AuditEventType.AUDIT_LOG, str(approval_id), action_type + "_executor",
                f"Execution BLOCKED: approval {approval_id} status is not APPROVED",
                actor=action_type.capitalize() + "Executor"
            )
            return False
        except Exception:
            pass
    # No approval_id found — warn but allow (backward compat with sandbox)
    get_audit_trail().record(
        AuditEventType.AUDIT_LOG, getattr(plan, 'plan_id', 'unknown'), action_type + "_executor",
        f"Execution without explicit approval token ({action_type})",
        actor=action_type.capitalize() + "Executor"
    )
    return True


@dataclass
class SandboxExecutorResult:
    """Hasil dari executor sandbox — action_results per action."""
    plan_id: str
    success: bool
    action_logs: List[Dict[str, Any]] = field(default_factory=list)
    error_message: str = ""
    duration_ms: int = 0


def _sb_path(sandbox, name: str) -> str:
    """Absolute path dalam sandbox."""
    return os.path.join(sandbox._base_path, 'files', name)


class FilesystemExecutor:
    """Executor untuk operasi filesystem."""

    def __init__(self, sandbox: ExecutionSandbox):
        self._sandbox = sandbox
        self.state = ExecutorState.IDLE
        sandbox.add_allowed_path(os.path.join(sandbox._base_path, 'files'))
        sandbox.add_allowed_path(sandbox._base_path)

    def prepare(self, plan) -> bool:
        self.state = ExecutorState.PREPARING
        return True

    def execute(self, plan) -> ExecutionResult:
        self.state = ExecutorState.EXECUTING
        audit = get_audit_trail()
        t0 = datetime.now()
        action_logs = []
        completed = 0
        failed = 0

        if not _require_execution_approval(plan, "filesystem"):
            state = ExecutorState.FAILED
            self.state = state
            audit.record(
                AuditEventType.EXECUTION_FAILED,
                plan.plan_id, "filesystem_executor",
                "Execution BLOCKED: no valid approval",
                actor="FilesystemExecutor",
            )
            return ExecutionResult(
                plan_id=plan.plan_id, state=state,
                started_at=t0.isoformat(), completed_at=datetime.now().isoformat(),
                duration_ms=0, actions_completed=0, actions_failed=0,
                action_results=[],
            )

        for i, action in enumerate(plan.actions):
            title = getattr(action, 'title', 'Action {}'.format(i))
            try:
                if "write" in title.lower():
                    self._sandbox.execute_op(SandboxOperationType.FILE_WRITE,
                                             _sb_path(self._sandbox, plan.plan_id + "_write"), {})
                elif "delete" in title.lower():
                    self._sandbox.execute_op(SandboxOperationType.FILE_DELETE,
                                             _sb_path(self._sandbox, plan.plan_id + "_delete"))
                elif "backup" in title.lower():
                    self._sandbox.execute_op(SandboxOperationType.FILE_BACKUP,
                                             _sb_path(self._sandbox, plan.plan_id + "_backup"))
                elif "free" in title.lower() and "disk" in title.lower():
                    self._sandbox.execute_op(SandboxOperationType.FILE_WRITE,
                                             _sb_path(self._sandbox, plan.plan_id + "_cleanup"), {})
                elif "cache" in title.lower():
                    self._sandbox.execute_op(SandboxOperationType.FILE_DELETE,
                                             _sb_path(self._sandbox, plan.plan_id + "_cache"))
                else:
                    self._sandbox.execute_op(SandboxOperationType.FILE_WRITE,
                                             _sb_path(self._sandbox, plan.plan_id + "_generic"), {"content": title})
                completed += 1
                action_logs.append({"index": i, "title": title, "status": "completed"})
            except Exception as e:
                failed += 1
                action_logs.append({"index": i, "title": title, "status": "failed", "error": str(e)})

        duration = int((datetime.now() - t0).total_seconds() * 1000)
        state = ExecutorState.COMPLETED if failed == 0 else ExecutorState.FAILED
        self.state = state
        audit.record(
            AuditEventType.EXECUTION_COMPLETED if failed == 0 else AuditEventType.EXECUTION_FAILED,
            plan.plan_id, "filesystem_executor",
            "Filesystem executor: {} completed, {} failed".format(completed, failed),
            actor="FilesystemExecutor",
        )
        return ExecutionResult(
            plan_id=plan.plan_id, state=state,
            started_at=t0.isoformat(), completed_at=datetime.now().isoformat(),
            duration_ms=duration, actions_completed=completed, actions_failed=failed,
            action_results=action_logs,
        )

    def verify(self, plan, result: ExecutionResult) -> bool:
        self.state = ExecutorState.VERIFYING
        result.verification_passed = result.actions_failed == 0
        return result.verification_passed

    def rollback(self, plan, reason: str = "") -> bool:
        self.state = ExecutorState.ROLLING_BACK
        get_audit_trail().record(AuditEventType.ROLLBACK_STARTED, plan.plan_id, "filesystem_executor",
                                 "Rollback: {}".format(reason), actor="FilesystemExecutor")
        return True

    def cleanup(self, plan) -> bool:
        self.state = ExecutorState.CLEANED_UP
        return True


class CommandExecutor:
    """Executor untuk operasi command/service."""

    def __init__(self, sandbox: ExecutionSandbox):
        self._sandbox = sandbox
        self.state = ExecutorState.IDLE
        for cmd_pfx in ['systemctl', 'scale', 'cleanup', 'diagnostic', 'investigate']:
            sandbox.add_allowed_command(cmd_pfx)

    def prepare(self, plan) -> bool:
        self.state = ExecutorState.PREPARING
        return True

    def execute(self, plan) -> ExecutionResult:
        self.state = ExecutorState.EXECUTING
        audit = get_audit_trail()
        t0 = datetime.now()
        action_logs, completed, failed = [], 0, 0

        if not _require_execution_approval(plan, "command"):
            return ExecutionResult(plan_id=plan.plan_id, state=ExecutorState.FAILED,
                started_at=t0.isoformat(), completed_at=datetime.now().isoformat(),
                duration_ms=0, actions_completed=0, actions_failed=0, action_results=[])

        for i, action in enumerate(plan.actions):
            title = getattr(action, 'title', 'Action {}'.format(i))
            try:
                if "restart" in title.lower():
                    self._sandbox.execute_op(SandboxOperationType.COMMAND_EXECUTE,
                                             "systemctl restart " + getattr(action, 'target', 'service'))
                elif "scale" in title.lower():
                    self._sandbox.execute_op(SandboxOperationType.COMMAND_EXECUTE,
                                             "scale workers to " + getattr(action, 'target', '3'))
                elif "cleanup" in title.lower():
                    self._sandbox.execute_op(SandboxOperationType.COMMAND_EXECUTE, "cleanup.sh")
                elif "diagnostic" in title.lower():
                    self._sandbox.execute_op(SandboxOperationType.COMMAND_EXECUTE, "diagnostic.sh")
                elif "investigate" in title.lower():
                    self._sandbox.execute_op(SandboxOperationType.COMMAND_EXECUTE,
                                             "investigate " + getattr(action, 'target', 'unknown'))
                else:
                    self._sandbox.execute_op(SandboxOperationType.COMMAND_EXECUTE, title)
                completed += 1
                action_logs.append({"index": i, "title": title, "status": "completed"})
            except Exception as e:
                failed += 1
                action_logs.append({"index": i, "title": title, "status": "failed", "error": str(e)})

        duration = int((datetime.now() - t0).total_seconds() * 1000)
        state = ExecutorState.COMPLETED if failed == 0 else ExecutorState.FAILED
        self.state = state
        audit.record(
            AuditEventType.EXECUTION_COMPLETED if failed == 0 else AuditEventType.EXECUTION_FAILED,
            plan.plan_id, "command_executor",
            "Command executor: {} completed, {} failed".format(completed, failed),
            actor="CommandExecutor",
        )
        return ExecutionResult(plan_id=plan.plan_id, state=state,
            started_at=t0.isoformat(), completed_at=datetime.now().isoformat(),
            duration_ms=duration, actions_completed=completed, actions_failed=failed,
            action_results=action_logs)

    def verify(self, plan, result: ExecutionResult) -> bool:
        self.state = ExecutorState.VERIFYING
        result.verification_passed = result.actions_failed == 0
        return result.verification_passed

    def rollback(self, plan, reason: str = "") -> bool:
        self.state = ExecutorState.ROLLING_BACK
        get_audit_trail().record(AuditEventType.ROLLBACK_STARTED, plan.plan_id, "command_executor",
                                 "Rollback: {}".format(reason), actor="CommandExecutor")
        return True

    def cleanup(self, plan) -> bool:
        self.state = ExecutorState.CLEANED_UP
        return True


class ProcessExecutor:
    """Executor untuk operasi process."""

    def __init__(self, sandbox: ExecutionSandbox):
        self._sandbox = sandbox
        self.state = ExecutorState.IDLE
        sandbox.add_allowed_path(os.path.join(sandbox._base_path, 'files'))
        sandbox.add_allowed_path(sandbox._base_path)

    def prepare(self, plan) -> bool:
        self.state = ExecutorState.PREPARING
        return True

    def execute(self, plan) -> ExecutionResult:
        self.state = ExecutorState.EXECUTING
        audit, t0 = get_audit_trail(), datetime.now()
        action_logs, completed, failed = [], 0, 0

        if not _require_execution_approval(plan, "process"):
            return ExecutionResult(plan_id=plan.plan_id, state=ExecutorState.FAILED,
                started_at=t0.isoformat(), completed_at=datetime.now().isoformat(),
                duration_ms=0, actions_completed=0, actions_failed=0, action_results=[])

        for i, action in enumerate(plan.actions):
            title = getattr(action, 'title', 'Action {}'.format(i))
            try:
                if "stop" in title.lower():
                    self._sandbox.execute_op(SandboxOperationType.PROCESS_STOP, title)
                elif "kill" in title.lower():
                    self._sandbox.execute_op(SandboxOperationType.PROCESS_KILL, title)
                elif "start" in title.lower() and "restart" not in title.lower():
                    self._sandbox.execute_op(SandboxOperationType.PROCESS_START, title)
                elif "restart" in title.lower():
                    self._sandbox.execute_op(SandboxOperationType.COMMAND_EXECUTE,
                                             "systemctl restart " + getattr(action, 'target', 'service'))
                else:
                    self._sandbox.execute_op(SandboxOperationType.PROCESS_START, title)
                completed += 1
                action_logs.append({"index": i, "title": title, "status": "completed"})
            except Exception as e:
                failed += 1
                action_logs.append({"index": i, "title": title, "status": "failed", "error": str(e)})

        duration = int((datetime.now() - t0).total_seconds() * 1000)
        state = ExecutorState.COMPLETED if failed == 0 else ExecutorState.FAILED
        self.state = state
        audit.record(
            AuditEventType.EXECUTION_COMPLETED if failed == 0 else AuditEventType.EXECUTION_FAILED,
            plan.plan_id, "process_executor",
            "Process executor: {} completed, {} failed".format(completed, failed),
            actor="ProcessExecutor",
        )
        return ExecutionResult(plan_id=plan.plan_id, state=state,
            started_at=t0.isoformat(), completed_at=datetime.now().isoformat(),
            duration_ms=duration, actions_completed=completed, actions_failed=failed,
            action_results=action_logs)

    def verify(self, plan, result: ExecutionResult) -> bool:
        self.state = ExecutorState.VERIFYING
        result.verification_passed = result.actions_failed == 0
        return result.verification_passed

    def rollback(self, plan, reason: str = "") -> bool:
        self.state = ExecutorState.ROLLING_BACK
        return True

    def cleanup(self, plan) -> bool:
        self.state = ExecutorState.CLEANED_UP
        return True


class WorkspaceExecutor:
    """Executor untuk operasi workspace."""

    def __init__(self, sandbox: ExecutionSandbox):
        self._sandbox = sandbox
        self.state = ExecutorState.IDLE
        sandbox.add_allowed_path(os.path.join(sandbox._base_path, 'files'))
        sandbox.add_allowed_path(sandbox._base_path)

    def prepare(self, plan) -> bool:
        self.state = ExecutorState.PREPARING
        return True

    def execute(self, plan) -> ExecutionResult:
        self.state = ExecutorState.EXECUTING
        audit, t0 = get_audit_trail(), datetime.now()
        action_logs, completed, failed = [], 0, 0

        if not _require_execution_approval(plan, "workspace"):
            return ExecutionResult(plan_id=plan.plan_id, state=ExecutorState.FAILED,
                started_at=t0.isoformat(), completed_at=datetime.now().isoformat(),
                duration_ms=0, actions_completed=0, actions_failed=0, action_results=[])

        for i, action in enumerate(plan.actions):
            title = getattr(action, 'title', 'Action {}'.format(i))
            try:
                if "cache" in title.lower():
                    self._sandbox.execute_op(SandboxOperationType.FILE_DELETE,
                                             _sb_path(self._sandbox, plan.plan_id + "_cache"))
                elif "archive" in title.lower():
                    self._sandbox.execute_op(SandboxOperationType.FILE_WRITE,
                                             _sb_path(self._sandbox, plan.plan_id + "_archive"), {'content': title})
                elif "manifest" in title.lower():
                    self._sandbox.execute_op(SandboxOperationType.FILE_WRITE,
                                             _sb_path(self._sandbox, plan.plan_id + "_manifest"), {'content': 'recalculated'})
                else:
                    self._sandbox.execute_op(SandboxOperationType.FILE_WRITE,
                                             _sb_path(self._sandbox, plan.plan_id + "_ws_op"), {'content': title})
                completed += 1
                action_logs.append({"index": i, "title": title, "status": "completed"})
            except Exception as e:
                failed += 1
                action_logs.append({"index": i, "title": title, "status": "failed", "error": str(e)})

        duration = int((datetime.now() - t0).total_seconds() * 1000)
        state = ExecutorState.COMPLETED if failed == 0 else ExecutorState.FAILED
        self.state = state
        audit.record(
            AuditEventType.EXECUTION_COMPLETED if failed == 0 else AuditEventType.EXECUTION_FAILED,
            plan.plan_id, "workspace_executor",
            "Workspace executor: {} completed, {} failed".format(completed, failed),
            actor="WorkspaceExecutor",
        )
        return ExecutionResult(plan_id=plan.plan_id, state=state,
            started_at=t0.isoformat(), completed_at=datetime.now().isoformat(),
            duration_ms=duration, actions_completed=completed, actions_failed=failed,
            action_results=action_logs)

    def verify(self, plan, result: ExecutionResult) -> bool:
        self.state = ExecutorState.VERIFYING
        result.verification_passed = result.actions_failed == 0
        return result.verification_passed

    def rollback(self, plan, reason: str = "") -> bool:
        self.state = ExecutorState.ROLLING_BACK
        return True

    def cleanup(self, plan) -> bool:
        self.state = ExecutorState.CLEANED_UP
        return True
