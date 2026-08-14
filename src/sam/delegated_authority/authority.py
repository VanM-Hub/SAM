"""M14-001 AutonomousAuthority — model delegated authority.

Inti M14: authority untuk auto-approval BERASAL dari Owner (lewat
Entrustment), BUKAN dari SAM. SAM tidak pernah memberi dirinya sendiri
authority, dan authority tidak pernah naik lewat learning/confidence.

Objek di sini adalah DTO deterministik (immutable semantic), konsisten
dengan pola M13 (Entrustment) dan autonomy/models.py (AutonomyLevel).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from sam.autonomy.models import AutonomyLevel


class AuthoritySource(str, Enum):
    """Dari mana authority untuk tindakan ini berasal.

    OWNER       — keputusan orang/owner (manual approval).
    ENTRUSTMENT — authority didelegasikan Owner ke SAM via Entrustment aktif.
    NONE        — tidak ada authority (tindakan dilarang / perlu eskalasi).
    """
    OWNER = "owner"
    ENTRUSTMENT = "entrustment"
    NONE = "none"


class AuthorityVerdict(str, Enum):
    """Keputusan authority atas sebuah tindakan (deterministik)."""

    AUTO_APPROVE = "auto_approve"      # delegated authority cukup -> boleh auto-approve
    ESCALATE = "escalate"              # authority/evidence tak cukup -> ke manusia
    BLOCKED = "blocked"                # tidak berwenang sama sekali (haram dieksekusi)
    NO_AUTHORITY = "no_authority"      # tidak ada entrustment -> fail-closed


class DelegationGrant:
    """Mandat terbatas Owner atas sebuah Ward (ringkasan Entrustment utk M14).

    Grant ini TIDAK menyimpan credential apa pun dan TIDAK bisa diubah oleh
    SAM. Ia hanya proyeksi read-only dari Entrustment + ApprovalPolicy M13:
      - ward_id: subject yang dipercayakan
      - owner_id: pemberi mandat
      - autonomy_level: batas atas OTONOMI yang diizinkan owner untuk Ward ini
      - allowed_mutations: capability mutation yang boleh (mutation tetap
        lewat approval canonical; grant menentukan apakah approval BISA otomatis)
      - requires_human_approval: bila True, mutation pada Ward ini WAJIB
        keputusan manusia (tidak pernah auto-approve)
    """

    def __init__(
        self,
        ward_id: str = "",
        owner_id: str = "",
        autonomy_level: AutonomyLevel = AutonomyLevel.OBSERVE,
        allowed_mutations: tuple = (),
        requires_human_approval: bool = True,
        scope_note: str = "",
    ) -> None:
        self.ward_id = ward_id
        self.owner_id = owner_id
        self.autonomy_level = autonomy_level
        self.allowed_mutations = tuple(m.strip().lower() for m in allowed_mutations if m and m.strip())
        self.requires_human_approval = requires_human_approval
        self.scope_note = scope_note

    def allows_auto_approve(self, capability: str, risk: str = "low") -> bool:
        """Apakah mandat ini mengizinkan AUTO-APPROVE untuk mutation ini?

        aturan (fail-closed):
          - requires_human_approval True  -> TIDAK PERNAH auto-approve.
          - capability tidak di allowed_  -> TIDAK auto-approve.
          - autonomy_level tidak bisa     -> TIDAK auto-approve (via can_execute).
          - yang lain -> Auto-approve HANYA bila owner mandat mengizinkan
            (deterministik, bukan keputusan SAM).
        """
        cap = capability.strip().lower()
        if self.requires_human_approval:
            return False
        if cap not in self.allowed_mutations:
            return False
        if not self.autonomy_level.can_execute(risk):
            return False
        return True

    def as_dict(self) -> Dict[str, Any]:
        return {
            "ward_id": self.ward_id,
            "owner_id": self.owner_id,
            "autonomy_level": self.autonomy_level.value,
            "allowed_mutations": list(self.allowed_mutations),
            "requires_human_approval": self.requires_human_approval,
            "scope_note": self.scope_note,
        }


@dataclass(frozen=True)
class AutonomousAuthority:
    """Keputusan authority final untuk sebuah tindakan (immutable, auditable).

    - source: dari mana authority (owner/entrustment/none).
    - verdict: apa yang harus dilakukan (auto_approve/escalate/blocked/no_authority).
    - grant: mandat yang mendasari keputusan (nullable bila tidak ada).
    - reason: alasan manusia-bisa-baca untuk audit.
    - evidence_refs: acuan evidence yang menopang keputusan.
    """

    authority_id: str
    ward_id: str
    capability: str
    source: AuthoritySource = AuthoritySource.NONE
    verdict: AuthorityVerdict = AuthorityVerdict.NO_AUTHORITY
    grant: Optional[Dict[str, Any]] = None
    reason: str = ""
    evidence_refs: tuple = ()
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        if not self.authority_id:
            object.__setattr__(self, "authority_id", f"aut_{uuid.uuid4().hex[:12]}")

    @property
    def auto_approve_allowed(self) -> bool:
        return self.verdict == AuthorityVerdict.AUTO_APPROVE

    @property
    def escalate(self) -> bool:
        return self.verdict == AuthorityVerdict.ESCALATE

    def as_dict(self) -> Dict[str, Any]:
        return {
            "authority_id": self.authority_id,
            "ward_id": self.ward_id,
            "capability": self.capability,
            "source": self.source.value,
            "verdict": self.verdict.value,
            "grant": self.grant,
            "reason": self.reason,
            "evidence_refs": list(self.evidence_refs),
            "timestamp": self.timestamp,
        }

    @staticmethod
    def new_id() -> str:
        return f"aut_{uuid.uuid4().hex[:12]}"
