"""Execution Credential Verification - IP-4.1-001 WP-02.

Provider Execution Foundation.
Memastikan credential valid sebelum Provider digunakan untuk eksekusi.

Scope (Foundation immutable):
- Verifikasi keberadaan & format credential (via CredentialManager).
- Provider authentication check (keberadaan env/source).
- Verification result + explainability.
- Verification API (read-only).
- Tidak ada execution saat verifikasi gagal (guard konsumen).

Semua deterministik (Article VII), tanpa network, tanpa authority baru.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .credential import (
    CredentialStatus,
    CredentialStatusResult,
    ExecutionCredentialManager,
)


# ---------------------------------------------------------------------------
# Model (immutable)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class VerificationCheck:
    """Satu cek verifikasi credential (immutable)."""

    check_id: str
    name: str
    passed: bool
    detail: str = ""
    severity: str = "information"   # information | warning

    def as_dict(self) -> dict:
        return {
            "check_id": self.check_id,
            "name": self.name,
            "passed": self.passed,
            "detail": self.detail,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class CredentialVerification:
    """Hasil verifikasi credential provider (immutable)."""

    provider_id: str
    verified: bool
    checks: Tuple[VerificationCheck, ...] = field(default_factory=tuple)
    status: str = "unknown"          # verified | not_verified | missing | invalid
    reason: str = ""
    masked_credential: str = ""
    verified_at: str = ""

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "verified": self.verified,
            "checks": [c.as_dict() for c in self.checks],
            "status": self.status,
            "reason": self.reason,
            "masked_credential": self.masked_credential,
            "verified_at": self.verified_at,
        }


@dataclass(frozen=True)
class VerificationSummary:
    """Ringkasan verifikasi seluruh provider (immutable)."""

    total: int
    verified: int
    not_verified: int
    by_status: Dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "verified": self.verified,
            "not_verified": self.not_verified,
            "by_status": dict(self.by_status),
        }


# ---------------------------------------------------------------------------
# Verifier
# ---------------------------------------------------------------------------


class CredentialVerifier:
    """Verifier credential provider (read-only, no network).

    Memverifikasi bahwa credential tersedia & format wajar SEBELUM provider
    boleh dipakai untuk eksekusi. Setiap cek menghasilkan check + penjelasan.
    """

    def __init__(
        self,
        manager: Optional[ExecutionCredentialManager] = None,
    ) -> None:
        self._manager = manager or ExecutionCredentialManager()

    @property
    def manager(self) -> ExecutionCredentialManager:
        """Akses publik ke credential manager (read-only)."""
        return self._manager

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def verify(self, provider_id: str, actor: str = "execution") -> CredentialVerification:
        """Verifikasi credential satu provider. Tidak pernah mengubah state."""
        result = self._manager.resolve(provider_id, actor)  # type: CredentialStatusResult
        checks: List[VerificationCheck] = []

        # Cek 1: provider dikenal
        known = self._manager.reference_for(provider_id) is not None
        checks.append(VerificationCheck(
            "provider_known", "Provider dikenal", known,
            "" if known else "provider tidak terdaftar dalam registry credential",
        ))
        if not known:
            return self._build(result, checks, "not_verified", "provider tidak dikenal", self._now())

        ref = self._manager.reference_for(provider_id)  # type: ignore
        non_auth = (not ref.is_known()) or (not ref.env_var)

        # Cek 2: source credential (non-auth selalu passed)
        checks.append(VerificationCheck(
            "credential_source", "Sumber credential tersedia", non_auth or result.status != CredentialStatus.MISSING,
            ("provider non-auth, tanpa credential" if non_auth else
             ("env '{}' terisi".format(ref.env_var) if result.status == CredentialStatus.OK
              else "env '{}' kosong".format(result.missing_env or ref.env_var))),
        ))

        if non_auth:
            # provider non-auth dianggap terverifikasi (tanpa secret)
            return self._build(result, checks, "verified", "provider non-auth", self._now())

        if result.status == CredentialStatus.MISSING:
            return self._build(result, checks, "missing", result.reason, self._now())

        # Cek 3: format minimum (panjang)
        value = self._manager.raw_value(provider_id, actor)
        length_ok = len(value) >= 4
        checks.append(VerificationCheck(
            "credential_format", "Format credential wajar", length_ok,
            ("terdeteksi {} karakter".format(len(value)) if value else "kosong"),
            "warning" if not length_ok else "information",
        ))
        if not length_ok:
            return self._build(result, checks, "invalid", "credential terlalu pendek", self._now())

        # Cek 4: tidak kosong
        checks.append(VerificationCheck(
            "credential_present", "Credential terisi", bool(value),
            "ada" if value else "kosong",
        ))

        return self._build(result, checks, "verified", "credential terverifikasi", self._now())

    def _build(self, result: CredentialStatusResult, checks: List[VerificationCheck],
               status: str, reason: str, ts: str) -> CredentialVerification:
        return CredentialVerification(
            provider_id=result.provider_id,
            verified=(result.available and status == "verified"),
            checks=tuple(checks),
            status=status,
            reason=reason,
            masked_credential=result.masked_value,
            verified_at=ts,
        )

    def verify_all(self, actor: str = "execution") -> List[CredentialVerification]:
        """Verifikasi seluruh provider dikenal (read-only)."""
        return [self.verify(p, actor) for p in self._manager.known_providers()]

    def summary(self, actor: str = "execution") -> VerificationSummary:
        results = self.verify_all(actor)
        by = {}  # type: Dict[str, int]
        for r in results:
            by[r.status] = by.get(r.status, 0) + 1
        return VerificationSummary(
            total=len(results),
            verified=sum(1 for r in results if r.verified),
            not_verified=sum(1 for r in results if not r.verified),
            by_status=by,
        )

    def can_execute(self, provider_id: str, actor: str = "execution") -> bool:
        """Guard konsumen: eksekusi HANYA diizinkan bila credential terverifikasi.

        Ini mencegah execution saat verifikasi gagal (WP-02 acceptance).
        """
        return self.verify(provider_id, actor).verified
