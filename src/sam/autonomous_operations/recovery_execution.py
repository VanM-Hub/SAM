"""Recovery Execution - WP-13 (MISSION-4.5 / IP-4.5-002).

Mengeksekusi rencana pemulihan MELALUI Governance. Recovery execution wajib
approval (Article V); tanpa approval tidak dapat dieksekusi. Setiap eksekusi
menghasilkan audit.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional, Tuple

from .recovery_planning import RecoveryPlan
from .recovery_planning import RecoveryStep


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class RecoveryExecutionResult:
    """Hasil eksekusi satu langkah pemulihan."""

    step_id: str
    action: str
    status: str = "executed"  # executed | skipped | failed
    detail: str = ""

    def as_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "action": self.action,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class RecoverySession:
    """Sesi eksekusi pemulihan (auditable)."""

    session_id: str
    plan_id: str
    status: str = "created"  # created | approved | executing | completed | rejected
    executed: Tuple[RecoveryExecutionResult, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "plan_id": self.plan_id,
            "status": self.status,
            "executed": [e.as_dict() for e in self.executed],
            "created_at": self.created_at,
        }


class RecoveryExecutor:
    """Eksekutor pemulihan yang di-govern (approval-gated)."""

    def __init__(self, step_runner: Optional[Callable[[RecoveryStep], str]] = None) -> None:
        self._runner = step_runner or (lambda step: f"applied {step.action}")
        self._sessions: Dict[str, RecoverySession] = {}

    def create_session(self, plan: RecoveryPlan) -> RecoverySession:
        session = RecoverySession(
            session_id=uuid.uuid4().hex, plan_id=plan.plan_id
        )
        self._sessions[session.session_id] = session
        return session

    def execute(
        self,
        session: RecoverySession,
        plan: RecoveryPlan,
        *,
        approved: bool = False,
    ) -> RecoverySession:
        # Article V: recovery execution wajib approval
        if not approved:
            raise PermissionError("recovery execution requires approval (Article V)")

        self._sessions[session.session_id] = RecoverySession(
            session_id=session.session_id,
            plan_id=session.plan_id,
            status="executing",
        )
        results = []
        for step in plan.steps:
            try:
                detail = self._runner(step)
                results.append(
                    RecoveryExecutionResult(
                        step.step_id, step.action, "executed", detail
                    )
                )
            except Exception as exc:
                results.append(
                    RecoveryExecutionResult(step.step_id, step.action, "failed", str(exc))
                )
        completed = RecoverySession(
            session_id=session.session_id,
            plan_id=session.plan_id,
            status="completed",
            executed=tuple(results),
        )
        self._sessions[session.session_id] = completed
        return completed

    def get(self, session_id: str) -> Optional[RecoverySession]:
        return self._sessions.get(session_id)

    def all(self) -> Tuple[RecoverySession, ...]:
        return tuple(self._sessions.values())

    def audit(self) -> Dict[str, Any]:
        return {
            "session_count": len(self._sessions),
            "sessions": [s.as_dict() for s in self._sessions.values()],
        }
