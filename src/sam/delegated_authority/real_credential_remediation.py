"""M14-008 Real Credential Remediation — detect + fix credential via boundary.

Aturan M14: "TIDAK mengubah credential tanpa CredentialBoundary."

Design (jembatan authority, bukan bypass):
  - Deteksi: pakai CredentialBoundary.resolve (M8-005) -> MISSING/INVALID jujur.
  - Remediasi: SAM TIDAK pernah menciptakan/menebak secret. Ia:
      1. deteksi credential bermasalah (boundary),
      2. bila delegated authority mengizinkan -> minta/menunggu credential
         baru VALID (dari store/owner), lalu
      3. VERIFIKASI credential baru via boundary; bila valid -> remediated.
    Dengan begitu SAM TIDAK pernah menyentuh nilai secret langsung di luar
    boundary, dan TIDAK pernah self-grant.
  - Semua nilai secret yang keluar boundary SELALU di-mask (SecretScrubber).

Sifat real: verifikasi memakai CredentialBoundary nyata; bila credential valid
baru diset oleh pemanggil (owner/store) -> remediated. Tanpa itu -> BLOCKED
(no fake success). Ini memenuhi "jangan klaim PROVEN sebelum real E2E."
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sam.delegated_authority.authority import DelegationGrant
from sam.delegated_authority.recovery import RecoveryPhase
from sam.execution_runtime.credential_boundary import (
    BoundaryResult, BoundaryStatus, CredentialBoundary, CredentialRequirement,
)


@dataclass(frozen=True)
class CredentialRemediationResult:
    """Hasil remediasi credential (auditable)."""

    provider_id: str
    env_var: str
    detected_status: str          # missing | invalid | available
    remediated: bool
    verified_status: str = ""      # status setelah remediasi (available utk sukses)
    reason: str = ""
    masked: str = ""               # HANYA masked, tidak pernah raw
    phase: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "env_var": self.env_var,
            "detected_status": self.detected_status,
            "remediated": self.remediated,
            "verified_status": self.verified_status,
            "reason": self.reason,
            "masked": self.masked,
            "phase": self.phase,
        }


class RealCredentialRemediation:
    """Mendeteksi & meng-verifikasi remediasi credential (via boundary)."""

    def __init__(
        self, boundary: Optional[CredentialBoundary] = None
    ) -> None:
        self._boundary = boundary or CredentialBoundary()
        self._history: List[CredentialRemediationResult] = []

    # --- 1) deteksi ---

    def detect(
        self, req: CredentialRequirement
    ) -> BoundaryResult:
        """Deteksi status credential via boundary (jujur, tanpa raw)."""
        result = self._boundary.resolve(req)
        return result

    # --- 2) remediasi (hanya saat authority mengizinkan + credential baru valid) ---

    async def remediate(
        self,
        *,
        req: CredentialRequirement,
        grant: Optional[DelegationGrant] = None,
        new_value: Optional[str] = None,       # credential baru VALID (dari store/owner)
        owner_supplied: bool = False,          # penanda nilai disuplai otoritas pemilik
    ) -> CredentialRemediationResult:
        """Coba remediasi credential.

        HANYA remediated bila:
          - authority (grant) mengizinkan remediasi (capability 'protect',
            autonomy level, bukan human-required), ATAU owner_supplied=True
            (nilai datang dari pemilik — keputusan manusia, bukan SAM).
          - nilai baru valid (bukan placeholder, cukup panjang).
        Verifikasi final selalu lewat boundary.resolve -> AVAILABLE.
        """
        # 1) deteksi status awal
        initial = self._boundary.resolve(req)

        # 2) authority gate (fail-closed)
        authorized = bool(
            grant and (owner_supplied or not grant.requires_human_approval)
            and grant.allows_auto_approve("protect", "low")
        )
        # owner_supplied selalu dianggap otorisasi sah (keputusan pemilik)
        if owner_supplied:
            authorized = True

        if initial.status == BoundaryStatus.AVAILABLE:
            self._history.append(CredentialRemediationResult(
                provider_id=req.provider_id, env_var=req.env_var,
                detected_status="available", remediated=False,
                verified_status="available", reason="credential already valid",
                masked=initial.masked, phase=RecoveryPhase.COMPLETED,
            ))
            return self._history[-1]

        if not authorized:
            self._history.append(CredentialRemediationResult(
                provider_id=req.provider_id, env_var=req.env_var,
                detected_status=initial.status.value, remediated=False,
                reason="remediation not authorized - escalate (no self-grant)",
                masked=initial.masked, phase=RecoveryPhase.ESCALATED,
            ))
            return self._history[-1]

        # 3) menerapkan nilai baru — TIDAK boleh dari SAM menebak; pastikan
        #    disuplai otoritas (owner/store). Set via provider (boundary-aware).
        if not owner_supplied or new_value is None:
            self._history.append(CredentialRemediationResult(
                provider_id=req.provider_id, env_var=req.env_var,
                detected_status=initial.status.value, remediated=False,
                reason="no valid replacement supplied by authority (cannot self-create)",
                masked=initial.masked, phase=RecoveryPhase.FAILED,
            ))
            return self._history[-1]

        # placeholder / terlalu pendek -> tolak (bukan remediasi valid)
        if len(new_value) < req.min_length:
            self._history.append(CredentialRemediationResult(
                provider_id=req.provider_id, env_var=req.env_var,
                detected_status=initial.status.value, remediated=False,
                reason="replacement invalid (too short / placeholder)",
                masked=initial.masked, phase=RecoveryPhase.FAILED,
            ))
            return self._history[-1]

        # 4) set + verifikasi via boundary (nilai masuk store, bukan ke log)
        self._set_secret(req.env_var, new_value)
        verified = self._boundary.resolve(req)
        remediated = verified.status == BoundaryStatus.AVAILABLE

        self._history.append(CredentialRemediationResult(
            provider_id=req.provider_id, env_var=req.env_var,
            detected_status=initial.status.value, remediated=remediated,
            verified_status=verified.status.value,
            reason=("remediated & verified available"
                    if remediated else f"still {verified.status.value}: {verified.reason}"),
            masked=verified.masked,
            phase=RecoveryPhase.COMPLETED if remediated else RecoveryPhase.FAILED,
        ))
        return self._history[-1]

    # --- bantuan set (melalui provider; nilai TIDAK diteruskan ke audit) ---

    def _set_secret(self, key: str, value: str) -> None:
        """Set secret ke provider (env-based) TANPA mengekspos nilai ke output."""
        provider = self._boundary._provider  # noqa: SLF001 - akses internal boundary untuk set
        # SecretProvider env-based: set ke dict env internal boundary.
        if hasattr(provider, "_env") and isinstance(provider._env, dict):  # noqa: SLF001
            provider._env[key] = value  # noqa: SLF001
        else:
            # PgSecretProvider tidak punja set publik -> tidak bisa remediasi
            # tanpa API store: jujur fail (bukan mock sukses).
            raise RuntimeError(
                f"provider type {type(provider).__name__} has no set; remediation unsupported"
            )

    def release(self, provider_id: Optional[str] = None) -> None:
        self._boundary.release(provider_id)

    def history(self, limit: int = 100) -> List[CredentialRemediationResult]:
        h = list(self._history)
        h.reverse()
        return h[:limit]
