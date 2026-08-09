"""Governed Tool Invocation + Execution Context - WP-23/WP-24 (MISSION-5.2 / IP-5.2-003).

Invocation Tool hanya boleh melalui jalur Governance:
Tool Request -> Capability Resolution -> Policy Validation -> Approval -> Execution.
Tidak ada execution di luar jalur ini.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


class ExecutionStage(str, Enum):
    """Tahapan jalur governed execution."""

    REQUEST = "request"
    CAPABILITY_RESOLUTION = "capability_resolution"
    POLICY_VALIDATION = "policy_validation"
    APPROVAL = "approval"
    EXECUTION = "execution"


@dataclass(frozen=True)
class GovernanceDecision:
    """Keputusan governance di sekitar execution tool."""

    stage: ExecutionStage
    passed: bool
    reason: str = ""

    def as_dict(self) -> dict:
        return {"stage": self.stage.value, "passed": self.passed, "reason": self.reason}


@dataclass(frozen=True)
class ToolExecutionContext:
    """Context execution tool (auditable)."""

    request_id: str
    tool_id: str
    connector_id: str
    capability: str
    decisions: Tuple[GovernanceDecision, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=_now_utc)

    @property
    def approved(self) -> bool:
        approved = [d for d in self.decisions if d.stage == ExecutionStage.APPROVAL]
        return bool(approved) and approved[-1].passed

    @property
    def all_passed(self) -> bool:
        return all(d.passed for d in self.decisions)

    def as_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "tool_id": self.tool_id,
            "connector_id": self.connector_id,
            "capability": self.capability,
            "decisions": [d.as_dict() for d in self.decisions],
            "approved": self.approved,
            "all_passed": self.all_passed,
            "created_at": self.created_at,
        }


class GovernedToolInvoker:
    """Invoker yang menegakkan jalur governance sebelum execution."""

    def __init__(
        self,
        capability_check=None,
        policy_check=None,
        approval_check=None,
    ) -> None:
        self._capability_check = capability_check
        self._policy_check = policy_check
        self._approval_check = approval_check

    def execute(
        self,
        *,
        request_id: str,
        tool_id: str,
        connector_id: str,
        capability: str,
        require_approval: bool = True,
        approved: bool = True,
    ) -> ToolExecutionContext:
        decisions = [
            GovernanceDecision(ExecutionStage.REQUEST, True),
            GovernanceDecision(
                ExecutionStage.CAPABILITY_RESOLUTION,
                self._capability_check(tool_id, capability) if self._capability_check else True,
            ),
            GovernanceDecision(
                ExecutionStage.POLICY_VALIDATION,
                self._policy_check(request_id) if self._policy_check else True,
            ),
            GovernanceDecision(
                ExecutionStage.APPROVAL,
                (not require_approval) or approved,
                reason="" if ((not require_approval) or approved) else "approval required",
            ),
        ]
        # Execution hanya berlangsung bila seluruh keputusan governance lulus
        can_execute = all(d.passed for d in decisions)
        if can_execute:
            decisions.append(GovernanceDecision(ExecutionStage.EXECUTION, True))
        else:
            decisions.append(GovernanceDecision(ExecutionStage.EXECUTION, False, reason="blocked by governance"))

        return ToolExecutionContext(
            request_id=request_id,
            tool_id=tool_id,
            connector_id=connector_id,
            capability=capability,
            decisions=tuple(decisions),
        )
