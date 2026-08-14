"""M14-015 Real Operational Certification — status operasional jujur M14.

Menilai setiap capability M14 dengan level bukti yang JUJUR (aturan Van:
"Jangan klaim PROVEN sebelum real E2E").

Level bukti:
  UNVERIFIED     - belum ada test.
  UNIT           - logic teruji unit (deterministik, stub).
  INTEGRATION    - lintas komponen teruji (mis. autonomous loop + boundary).
  REAL           - E2E nyata ke sistem eksternal (OpenClaw/PC/provider/GitHub
                  hidup) + verification independen.
  BLOCKED        - memerlukan env/credential/live yang belum tersedia (jujur).

Sertifikasi AGREGAT: operational_ready = True bila ada minimal 1 capability
REAL dan tidak ada yang UNVERIFIED. Tidak menaikkan klaim; hanya mencatat
status aktual.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class CapabilityStatus:
    """Status bukti satu capability (immutable)."""

    milestone: str
    name: str
    level: str                 # unverified|unit|integration|real|blocked
    note: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "milestone": self.milestone, "name": self.name,
            "level": self.level, "note": self.note,
        }


@dataclass(frozen=True)
class OperationalCertification:
    """Hasil sertifikasi operasional (agregat)."""

    capabilities: tuple = ()
    real_count: int = 0
    blocked_count: int = 0
    unverified_count: int = 0
    operational_ready: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "capabilities": [c.as_dict() for c in self.capabilities],
            "real_count": self.real_count,
            "blocked_count": self.blocked_count,
            "unverified_count": self.unverified_count,
            "operational_ready": self.operational_ready,
        }


class OperationalCertifier:
    """Menilai status operasional M14 secara jujur (deterministik)."""

    @classmethod
    def certify(cls, capabilities: List[CapabilityStatus]) -> OperationalCertification:
        caps = tuple(capabilities)
        real = sum(1 for c in caps if c.level == "real")
        blocked = sum(1 for c in caps if c.level == "blocked")
        unver = sum(1 for c in caps if c.level in ("unverified",))
        ready = (real >= 1) and (unver == 0)
        return OperationalCertification(
            capabilities=caps, real_count=real, blocked_count=blocked,
            unverified_count=unver, operational_ready=ready,
        )

    @classmethod
    def m14_known_status(cls, real_targets: Dict[str, str]) -> OperationalCertification:
        """Status bawaan utk milestone M14 (level nyata per inspeksi).

        `real_targets` = milestone -> level ('real'/'blocked'/dst) berdasarkan
        bukti aktual (diisi saat rilis/certification, bukan tebakan).
        """
        base = [
            CapabilityStatus("M14-001", "AutonomousAuthority", "unit",
                             "DTO + DelegationGrant fail-closed teruji"),
            CapabilityStatus("M14-002", "DelegatedApprovalProvider", "unit",
                             "approval otomatis + ApprovalGate defense-in-depth"),
            CapabilityStatus("M14-003", "AuthorityEvaluation", "unit",
                             "guardrail+assessment+entrustment deterministik"),
            CapabilityStatus("M14-004", "ScopedAutonomy", "unit",
                             "hanya degrade, tidak self-grant"),
            CapabilityStatus("M14-005", "AutomaticEscalation", "unit",
                             "escalation via EscalationManager"),
            CapabilityStatus("M14-006", "AutonomousRecoveryLoop", "unit",
                             "orkestrator; tanpa injeksi -> no fake success"),
            CapabilityStatus("M14-007", "Provider Recovery", "unit",
                             "failover logic teruji (stub executor)"),
            CapabilityStatus("M14-008", "Credential Remediation", "unit",
                             "lewat boundary; tanpa self-create"),
            CapabilityStatus("M14-009", "OpenClaw Ward", "unit",
                             "diagnose health/log teruji file-based"),
            CapabilityStatus("M14-010", "Windows PC Ward", "unit",
                             "observe+diagnose Word/PDF teruji"),
            CapabilityStatus("M14-011", "Word Investigation", "unit",
                             "struktur .docx read-only"),
            CapabilityStatus("M14-012", "PDF Performance", "unit",
                             "metrik performa PDF read-only"),
            CapabilityStatus("M14-013", "Project Guardian", "unit",
                             "detect+repair local/github"),
        ]
        caps = list(base)
        for milestone, level in real_targets.items():
            name = next((c.name for c in caps if c.milestone == milestone), milestone)
            note = "real E2E verified" if level == "real" else \
                   ("blocked pending env/live" if level == "blocked" else level)
            caps.append(CapabilityStatus(milestone, name, level, note))
        return cls.certify(caps)
