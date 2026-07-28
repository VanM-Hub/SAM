"""
ExecutionPlan — rencana aksi dari DecisionProposal.

DecisionProposal → ExecutionPlan:
  actions: List[Action]
  verification_steps: List[VerificationStep]
  rollback_steps: List[Action]
  estimated_duration, risk_level, overall_confidence

Belum ada execute.
Conversation hanya membaca.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import enum


class PlanStatus(str, enum.Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"
    CLOSED = "closed"


@dataclass(frozen=True)
class VerificationStep:
    """Satu langkah verifikasi — apa yang harus diperiksa setelah action."""
    action_index: int                # index action yang diverifikasi
    expected_state: str              # "service running", "disk free", etc
    check_method: str = "status"     # status, metric, file, connection
    timeout_seconds: int = 30
    allowed_retries: int = 1
    severity: str = "information"


@dataclass(frozen=True)
class RollbackStep:
    """Satu langkah rollback — inverse dari action."""
    action_index: int                # index action yang di-rollback
    inverse_title: str               # "Start service" jika action = stop
    inverse_action_id: str = ""      # Action ID yang di-rollback
    critical: bool = False           # True = rollback wajib berhasil


@dataclass
class ExecutionPlan:
    """Rencana eksekusi — aggregate root untuk execution layer.

    Dari 1 DecisionProposal → 1 ExecutionPlan.
    Lifecycle: Draft → PendingApproval → Approved → Executing → Verifying → Completed
                                                         → Failed → RollingBack → RolledBack → Closed
    """

    plan_id: str
    source_decision_id: str = ""
    source_decision_title: str = ""

    # Actions
    actions: List[Any] = field(default_factory=list)           # List[Action]
    verification_steps: List[VerificationStep] = field(default_factory=list)
    rollback_steps: List[RollbackStep] = field(default_factory=list)

    # Metadata
    estimated_duration_seconds: int = 60
    risk_level: str = "low"           # low, medium, high, critical
    overall_confidence: float = 0.5

    # Lifecycle
    status: PlanStatus = PlanStatus.DRAFT
    status_history: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Audit
    failure_reason: str = ""
    rollback_reason: str = ""

    def to_text(self) -> str:
        lines = []
        lines.append("=== Execution Plan: {} ===".format(self.source_decision_title or self.plan_id))
        lines.append("Status: {} | Risk: {} | Confidence: {:.0f}%".format(
            self.status.value, self.risk_level, self.overall_confidence * 100
        ))
        lines.append("Duration: ~{}s | Actions: {} | Verifications: {} | Rollbacks: {}".format(
            self.estimated_duration_seconds,
            len(self.actions), len(self.verification_steps), len(self.rollback_steps),
        ))
        if self.actions:
            lines.append("")
            lines.append("Actions:")
            for i, a in enumerate(self.actions):
                title = getattr(a, 'title', str(a))
                lines.append("  [{0}] {1} ({2}s)".format(i, title, getattr(a, 'estimated_duration_seconds', '?')))
        if self.verification_steps:
            lines.append("")
            lines.append("Verification:")
            for v in self.verification_steps:
                lines.append("  → After action [{0}]: {1}".format(v.action_index, v.expected_state))
        if self.rollback_steps:
            lines.append("")
            lines.append("Rollback:")
            for r in self.rollback_steps:
                lines.append("  ↺ [{0}]: {1}".format(r.action_index, r.inverse_title))
        if self.failure_reason:
            lines.append("")
            lines.append("Failure: {}".format(self.failure_reason))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "source_decision_id": self.source_decision_id,
            "source_decision_title": self.source_decision_title,
            "actions": [getattr(a, 'to_dict', lambda: str(a))() for a in self.actions],
            "verification_steps": [
                {"action_index": v.action_index, "expected_state": v.expected_state,
                 "check_method": v.check_method}
                for v in self.verification_steps
            ],
            "rollback_steps": [
                {"action_index": r.action_index, "inverse_title": r.inverse_title, "critical": r.critical}
                for r in self.rollback_steps
            ],
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "risk_level": self.risk_level,
            "overall_confidence": self.overall_confidence,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "failure_reason": self.failure_reason,
        }

    def update_status(self, new_status: PlanStatus):
        self.status = new_status
        self.updated_at = datetime.now().isoformat()
        if not self.status_history or self.status_history[-1] != new_status.value:
            self.status_history.append(new_status.value)


class ExecutionPlanBuilder:
    """Membangun ExecutionPlan dari DecisionProposal.

    Untuk setiap decision, buat actions + verification_steps + rollback_steps.
    """

    @staticmethod
    def from_decision_proposal(proposal, plan_id: str = "") -> Optional[ExecutionPlan]:
        """Konversi DecisionProposal → ExecutionPlan.

        Args:
            proposal: DecisionProposal object (dari decision.py)
            plan_id: Optional custom ID

        Returns:
            ExecutionPlan atau None jika proposal invalid
        """
        if not proposal:
            return None

        from .action import ActionFactory

        decision_title = getattr(proposal, 'decision', '') or getattr(proposal, 'title', 'Unknown')
        decision_id = getattr(proposal, 'id', '') or plan_id

        actions = []
        verification_steps = []
        rollback_steps = []
        risk_level = "low"
        duration = 30

        title_lower = decision_title.lower()

        if "restart database" in title_lower or "database" in title_lower:
            actions.append(ActionFactory.restart_database())
            verification_steps.append(VerificationStep(
                action_index=0,
                expected_state="database connection active",
                check_method="connection",
                timeout_seconds=15,
            ))
            rollback_steps.append(RollbackStep(
                action_index=0,
                inverse_title="Verify database was not corrupted",
                critical=True,
            ))
            risk_level = "medium"
            duration = 15

        elif "disk" in title_lower or "free up" in title_lower or "cleanup" in title_lower:
            actions.append(ActionFactory.free_disk_space())
            actions.append(ActionFactory.clear_cache())
            verification_steps.append(VerificationStep(
                action_index=0,
                expected_state="disk usage decreased",
                check_method="metric",
                timeout_seconds=60,
            ))
            verification_steps.append(VerificationStep(
                action_index=1,
                expected_state="cache cleared successfully",
                check_method="status",
                timeout_seconds=15,
            ))
            risk_level = "medium"
            duration = 90

        elif "restart" in title_lower and "service" in title_lower:
            service = "web"
            actions.append(ActionFactory.restart_service(service))
            verification_steps.append(VerificationStep(
                action_index=0,
                expected_state="{} service running".format(service),
                check_method="status",
                timeout_seconds=30,
            ))
            rollback_steps.append(RollbackStep(
                action_index=0,
                inverse_title="Restart {} service (original)".format(service),
                critical=True,
            ))
            risk_level = "warning"
            duration = 35

        elif "scale" in title_lower or "worker" in title_lower:
            actions.append(ActionFactory.scale_workers(3))
            verification_steps.append(VerificationStep(
                action_index=0,
                expected_state="worker pool increased",
                check_method="status",
            ))
            rollback_steps.append(RollbackStep(
                action_index=0,
                inverse_title="Scale workers down to original count",
                critical=False,
            ))
            risk_level = "low"
            duration = 20

        elif "investigate" in title_lower:
            actions.append(ActionFactory.investigate_anomaly("unknown"))
            risk_level = "low"
            duration = 120

        else:
            # Generic — 1 action tanpa verification
            actions.append(ActionFactory.investigate_anomaly(title_lower))
            risk_level = "medium"
            duration = 60

        if not plan_id:
            import uuid
            plan_id = "plan-" + uuid.uuid4().hex[:8]

        confidence = getattr(proposal, 'confidence', 0.5)

        return ExecutionPlan(
            plan_id=plan_id,
            source_decision_id=decision_id,
            source_decision_title=decision_title,
            actions=actions,
            verification_steps=verification_steps,
            rollback_steps=rollback_steps,
            estimated_duration_seconds=duration,
            risk_level=risk_level,
            overall_confidence=confidence,
        )

    @staticmethod
    def from_decision_package(package, prefix: str = "plan") -> List[ExecutionPlan]:
        """Konversi DecisionPackage → List[ExecutionPlan]."""
        plans = []
        if not package or not hasattr(package, 'proposals'):
            return plans

        for i, proposal in enumerate(package.proposals):
            plan = ExecutionPlanBuilder.from_decision_proposal(
                proposal, plan_id="{}-{:03d}".format(prefix, i)
            )
            if plan:
                plans.append(plan)
        return plans
