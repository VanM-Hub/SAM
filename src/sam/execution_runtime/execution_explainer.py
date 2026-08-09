"""Execution Explainability - IP-4.1-002 WP-14.

Governed Execution.
Menyediakan penjelasan untuk seluruh execution (Kenapa? Kapan? Dengan policy
apa? Pada provider apa? Approver siapa? Article XI - Audit Everything).

Scope (Foundation immutable):
- Seluruh execution dapat dijelaskan.
- Explainability berbasis evidence (Article XIV - Explainability before Opt).
- Deterministik (Article VII).

Tidak ada network, tidak ada authority. Representasi penjelasan read-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Tuple


@dataclass(frozen=True)
class RationaleStep:
    """Satu langkah alasan (immutable)."""

    label: str
    value: str

    def as_dict(self) -> dict:
        return {"label": self.label, "value": self.value}


@dataclass(frozen=True)
class ExecutionExplanation:
    """Penjelasan eksekusi (immutable)."""

    explanation_id: str
    execution_id: str
    provider_id: str
    operation: str
    mode: str
    status: str
    rationale: Tuple[RationaleStep, ...] = field(default_factory=tuple)
    approver: str = ""
    policy_id: str = ""
    created_at: str = ""

    def as_dict(self) -> dict:
        return {
            "explanation_id": self.explanation_id,
            "execution_id": self.execution_id,
            "provider_id": self.provider_id,
            "operation": self.operation,
            "mode": self.mode,
            "status": self.status,
            "rationale": [r.as_dict() for r in self.rationale],
            "approver": self.approver,
            "policy_id": self.policy_id,
            "created_at": self.created_at,
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutionExplainer:
    """Menjelaskan sebuah execution secara deterministik & evidence-based."""

    def explain(
        self,
        request,
        response,
        approved: bool,
        rationale_extra: Optional[Tuple[RationaleStep, ...]] = None,
        policy_id: str = "",
    ) -> ExecutionExplanation:
        """Bangun penjelasan dari request+response+approval state."""
        rationale: list = []

        # Kenapa bisa/tidak dieksekusi (approval, Article V)
        mode = getattr(request, "mode", "preview")
        approved_flag = bool(getattr(request, "approved", False)) and approved
        if mode == "execute":
            if approved_flag:
                rationale.append(RationaleStep(
                    "approval", "Disetujui oleh '{}'".format(getattr(request, "approver", "") or "unknown")))
            else:
                rationale.append(RationaleStep(
                    "approval", "Tidak disetujui - approval wajib sebelum execute (Article V)"))
        else:
            rationale.append(RationaleStep(
                "mode", "Mode '{}' tidak memerlukan approval eksekusi".format(mode)))

        # Provider & operation (Article VIII / capability)
        rationale.append(RationaleStep(
            "provider", "Provider '{}' operasi '{}'".format(
                getattr(request, "provider_id", ""), getattr(request, "operation", ""))))

        # Status hasil (Article XI)
        response_status = getattr(response, "status", "unknown")
        rationale.append(RationaleStep("result", "Status: '{}'".format(response_status)))

        # Ekstra (dari caller, mis. evidence/verification)
        if rationale_extra:
            rationale.extend(rationale_extra)

        return ExecutionExplanation(
            explanation_id="xp-{}-{}".format(getattr(request, "execution_id", "?"), "1"),
            execution_id=getattr(request, "execution_id", ""),
            provider_id=getattr(request, "provider_id", ""),
            operation=getattr(request, "operation", ""),
            mode=mode,
            status=response_status,
            rationale=tuple(rationale),
            approver=getattr(request, "approver", "") or "",
            policy_id=policy_id,
            created_at=_now(),
        )
