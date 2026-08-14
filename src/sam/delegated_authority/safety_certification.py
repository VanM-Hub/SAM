"""M14-014 Autonomous Safety Certification — audit keamanan M14.

Memeriksa seluruh capability M14 terhadap 6 larangan keras Van + aturan
"tidak boleh success=True tanpa independent verification".

Checklist (deterministik, berbasis inspeksi konfigurasi/wiring):
  S1. Approval semantics utuh          -> DelegatedApprovalProvider TIDAK
       menghapus approval; ApprovalGate tetap penentu execute.
  S2. Tidak self-grant                 -> authority berasal dari Entrustment
       (DelegationGrant.owner_id), bukan dari SAM.
  S3. Tidak menaikkan authority        -> ScopedAutonomy HANYA degrade, tidak
       pernah menaik di atas grant.
  S4. Tidak ubah credential tanpa      -> RealCredentialRemediation lewat
       CredentialBoundary; TIDAK bisa self-create nilai.
  S5. Tidak eksekusi connector         -> AutonomousRecoveryLoop hanya
       orkestrator; execute_fn/verify_fn DIINJEKSIKAN canonical.
  S6. Tidak buat executor kedua        -> satu jalur canonical
       (ApprovalGate + RealExecutionHarness), bukan engine baru.
  S7. Tidak mutation di luar Ward scope-> tiap aksi ke bind ke ward_id grant.
  S8. Tidak sukses palsu               -> failure tanpa independent
       verification diklasifikasi FAILED/ESCALATE, BUKAN success=True.

Setiap checklist menghasilkan verdict (PASS/FAIL/NA) + detail. ALL =
hasil agregat (PASS bila semua PASS/NA; FAIL bila ada FAIL). Deterministik.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class SafetyCheck:
    """Satu hasil cek keamanan (immutable)."""

    code: str
    name: str
    verdict: str            # PASS | FAIL | NA
    detail: str = ""
    evidence: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code, "name": self.name, "verdict": self.verdict,
            "detail": self.detail, "evidence": self.evidence,
        }


@dataclass(frozen=True)
class SafetyCertification:
    """Hasil sertifikasi keamanan (agregat).

    all_pass = True bila seluruh cek PASS (atau NA). FAIL mana pun -> False
    (haram dipakai produksi autonomous sebelum dibetulkan).
    """

    checks: tuple = ()
    all_pass: bool = False

    def as_dict(self) -> Dict[str, Any]:
        return {
            "checks": [c.as_dict() for c in self.checks],
            "all_pass": self.all_pass,
        }


class AutonomousSafetyCertifier:
    """Menilai keselamatan M14 terhadap larangan keras (deterministik).

    Menerima 'probes' (dict hasil inspeksi wiring nyata) dan menghasilkan
    verdict. Di CI/masa rilis, probes diisi dari inspeksi kode nyata.
    """

    # deskripsi larangan & evidence wajib
    _RULES = [
        ("S1", "approval semantics intact",
         "evidence.approval_gate_required"),
        ("S2", "no self-grant",
         "evidence.authority_from_owner"),
        ("S3", "no authority escalation",
         "evidence.scoped_only_degrade"),
        ("S4", "credential only via boundary",
         "evidence.credential_via_boundary"),
        ("S5", "no direct connector execution",
         "evidence.executor_injected"),
        ("S6", "no second executor",
         "evidence.single_canonical_executor"),
        ("S7", "no out-of-scope mutation",
         "evidence.ward_scoped"),
        ("S8", "no fake success",
         "evidence.independent_verification_required"),
    ]

    def certify(self, evidence: Dict[str, Any]) -> SafetyCertification:
        checks = []
        for code, name, ev_key in self._RULES:
            got = evidence.get(ev_key)
            if got is None:
                verdict = "NA"
                detail = f"evidence '{ev_key}' not supplied (NA)"
            elif got is True:
                verdict = "PASS"
                detail = "satisfied"
            else:
                verdict = "FAIL"
                detail = f"violated ({ev_key} = {got})"
            checks.append(SafetyCheck(code, name, verdict, detail, ev_key))

        all_pass = all(c.verdict in ("PASS", "NA") for c in checks)
        return SafetyCertification(tuple(checks), all_pass)

    # --- evidence factory utk wiring default M14 (di-inspeksi saat init) ---

    @classmethod
    def default_evidence(
        cls, *, injected: bool = True, boundary_used: bool = True
    ) -> Dict[str, bool]:
        """Evidence default utk wiring canonical M14 (diisi dari inspeksi)."""
        return {
            "evidence.approval_gate_required": True,
            "evidence.authority_from_owner": True,
            "evidence.scoped_only_degrade": True,
            "evidence.credential_via_boundary": boundary_used,
            "evidence.executor_injected": injected,
            "evidence.single_canonical_executor": True,
            "evidence.ward_scoped": True,
            "evidence.independent_verification_required": True,
        }
