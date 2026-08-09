"""Execution Context - IP-4.1-001 WP-05.

Provider Execution Foundation.
Menyediakan konteks lengkap sebelum execution dilakukan.

Scope (Foundation immutable):
- Seluruh execution memiliki context.
- Context immutable (Article VI).
- Context dapat ditelusuri kembali (traceable, Article XI).
- Context meliputi: Governance, Mission, Workflow, Runtime, Provider.

Tidak ada network, tidak ada authority. Hanya representasi konteks deterministik.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Tuple


@dataclass(frozen=True)
class GovernanceContext:
    """Konteks governance (immutable)."""

    policy_id: str = ""
    approval_required: bool = True
    approval_id: str = ""
    approver: str = ""
    governance_flow: str = "approval_before_execution"

    def as_dict(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "approval_required": self.approval_required,
            "approval_id": self.approval_id,
            "approver": self.approver,
            "governance_flow": self.governance_flow,
        }


@dataclass(frozen=True)
class MissionContext:
    """Konteks misi (immutable)."""

    mission_id: str = ""
    objective_id: str = ""
    phase: str = ""

    def as_dict(self) -> dict:
        return {"mission_id": self.mission_id, "objective_id": self.objective_id,
                "phase": self.phase}


@dataclass(frozen=True)
class WorkflowContext:
    """Konteks workflow (immutable)."""

    workflow_id: str = ""
    step_id: str = ""
    run_id: str = ""

    def as_dict(self) -> dict:
        return {"workflow_id": self.workflow_id, "step_id": self.step_id,
                "run_id": self.run_id}


@dataclass(frozen=True)
class RuntimeContext:
    """Konteks runtime (immutable)."""

    runtime_id: str = ""
    execution_runtime_id: str = ""

    def as_dict(self) -> dict:
        return {"runtime_id": self.runtime_id, "execution_runtime_id": self.execution_runtime_id}


@dataclass(frozen=True)
class ProviderContext:
    """Konteks provider (immutable)."""

    provider_id: str = ""
    operation: str = ""
    mode: str = "preview"

    def as_dict(self) -> dict:
        return {"provider_id": self.provider_id, "operation": self.operation,
                "mode": self.mode}


@dataclass(frozen=True)
class ExecutionContext:
    """Konteks eksekusi lengkap (immutable, traceable)."""

    context_id: str
    governance: GovernanceContext
    mission: MissionContext
    workflow: WorkflowContext
    runtime: RuntimeContext
    provider: ProviderContext
    created_at: str = ""
    source: str = "internal"
    trace_ref: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "context_id": self.context_id,
            "governance": self.governance.as_dict(),
            "mission": self.mission.as_dict(),
            "workflow": self.workflow.as_dict(),
            "runtime": self.runtime.as_dict(),
            "provider": self.provider.as_dict(),
            "created_at": self.created_at,
            "source": self.source,
            "trace_ref": list(self.trace_ref),
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutionContextBuilder:
    """Builder konteks eksekusi (immutable output, input-driven)."""

    def build(
        self,
        context_id: str,
        governance: GovernanceContext = GovernanceContext(),
        mission: MissionContext = MissionContext(),
        workflow: WorkflowContext = WorkflowContext(),
        runtime: RuntimeContext = RuntimeContext(),
        provider: ProviderContext = ProviderContext(),
        source: str = "internal",
        trace_ref: Tuple[str, ...] = (),
    ) -> ExecutionContext:
        return ExecutionContext(
            context_id=context_id or "ctx-{}".format(_now()),
            governance=governance,
            mission=mission,
            workflow=workflow,
            runtime=runtime,
            provider=provider,
            created_at=_now(),
            source=source,
            trace_ref=trace_ref,
        )

    def from_request(self, request, context_id: str = "",
                     approval_id: str = "", approver: str = "") -> ExecutionContext:
        """Bangun konteks dari ExecutionRequest (poros utama).

        Setiap execution punya provider/operation/mode dari request;
        governance approval direfleksikan untuk auditability.
        """
        req = request
        return self.build(
            context_id=context_id or "ctx-{}".format(req.execution_id),
            governance=GovernanceContext(
                approval_required=True,
                approval_id=approval_id,
                approver=approver or req.approver,
            ),
            provider=ProviderContext(
                provider_id=req.provider_id,
                operation=req.operation,
                mode=req.mode,
            ),
            source="execution_request",
            trace_ref=(req.execution_id,),
        )
