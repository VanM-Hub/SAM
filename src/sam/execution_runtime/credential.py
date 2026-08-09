"""Execution Credential Management - IP-4.1-001 WP-01.

Provider Execution Foundation.
Menyediakan sistem pengelolaan credential provider yang aman, terpisah dari
execution, tervalidasi, dan ter-audit.

Prinsip (Foundation immutable):
- Credential TIDAK pernah disimpan di source code (immutable, no hardcode).
- Credential dimuat dari environment/secret store saat diperlukan.
- Secret SELALU dimasking saat disajikan ke luar.
- Seluruh akses credential menghasilkan audit record (Article XI).
- Deterministik (Article VII): tanpa credential, status = unavailable.

Tidak ada network. Tidak ada authority baru. Hanya penyimpan metadata + akses
aman menuju sumber credential (env), terpisah dari logika eksekusi.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple


class CredentialStatus(str, enum.Enum):
    OK = "ok"
    MISSING = "missing"
    INVALID = "invalid"
    EXPIRED = "expired"
    REVOKED = "revoked"
    UNKNOWN = "unknown"


class CredentialSource(str, enum.Enum):
    ENVIRONMENT = "environment"
    SECRET_STORE = "secret_store"
    UNAVAILABLE = "unavailable"


# ---------------------------------------------------------------------------
# Model (immutable)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CredentialReference:
    """Referensi ke sumber credential (immutable, TIDAK memuat nilai secret).

    Nilai secret TIDAK pernah disimpan di objek ini - hanya nama env var atau
    kunci secret store yang menunjuk ke lokasi credential.
    """

    provider_id: str
    env_var: str = ""          # nama env var (mis. OPENAI_API_KEY)
    source: CredentialSource = CredentialSource.ENVIRONMENT
    required: bool = False     # True = provider butuh credential untuk execute

    def is_known(self) -> bool:
        return bool(self.env_var) or self.source != CredentialSource.UNAVAILABLE

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "env_var": self.env_var,
            "source": self.source.value,
            "required": self.required,
        }


@dataclass(frozen=True)
class CredentialStatusResult:
    """Status kredensial provider (immutable)."""

    provider_id: str
    status: CredentialStatus
    available: bool                # dapat dipakai untuk execute
    masked_value: str = ""         # secret yang sudah dimasking ("" bila kosong)
    missing_env: str = ""          # env var yang tidak terisi (bila missing)
    reason: str = ""

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "status": self.status.value,
            "available": self.available,
            "masked_value": self.masked_value,
            "missing_env": self.missing_env,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class CredentialAuditRecord:
    """Satu record audit akses credential (immutable, Article XI)."""

    record_id: str
    provider_id: str
    action: str                    # resolve | verify | mask
    accessed_at: str
    actor: str = "execution"
    env_var: str = ""
    result: str = "ok"

    def as_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "provider_id": self.provider_id,
            "action": self.action,
            "accessed_at": self.accessed_at,
            "actor": self.actor,
            "env_var": self.env_var,
            "result": self.result,
        }


@dataclass(frozen=True)
class CredentialSummary:
    """Ringkasan status seluruh provider (immutable)."""

    total: int
    available: int
    missing: int
    invalid: int
    by_status: Dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "available": self.available,
            "missing": self.missing,
            "invalid": self.invalid,
            "by_status": dict(self.by_status),
        }


# ---------------------------------------------------------------------------
# Masking helpers (deterministik)
# ---------------------------------------------------------------------------


def mask_secret(value: str, visible: int = 4) -> str:
    """Masking deterministik secret.

    Menampilkan `visible` karakter terakhir, sisanya diganti '*'.
    String kosong -> empty. Tanpa RNG (Article VII).
    """
    if not value:
        return ""
    if len(value) <= visible:
        return "*" * len(value)
    return "*" * (len(value) - visible) + value[-visible:]


# ---------------------------------------------------------------------------
# Registry referensi credential (deterministik, berbasis tabel)
# ---------------------------------------------------------------------------

# provider_id -> env var yang menunjuk credential (TIDAK ada nilai secret).
# Provider non-auth (filesystem, shell, dll) tidak butuh credential.
CREDENTIAL_REFERENCES: Dict[str, CredentialReference] = {
    "openai": CredentialReference("openai", "OPENAI_API_KEY", CredentialSource.ENVIRONMENT, True),
    "anthropic": CredentialReference("anthropic", "ANTHROPIC_API_KEY", CredentialSource.ENVIRONMENT, True),
    "gemini": CredentialReference("gemini", "GEMINI_API_KEY", CredentialSource.ENVIRONMENT, True),
    "deepseek": CredentialReference("deepseek", "DEEPSEEK_API_KEY", CredentialSource.ENVIRONMENT, True),
    "ollama": CredentialReference("ollama", "OLLAMA_HOST", CredentialSource.ENVIRONMENT, True),
    "openclaw": CredentialReference("openclaw", "OPENCLAW_GATEWAY", CredentialSource.ENVIRONMENT, True),
    "filesystem": CredentialReference("filesystem", "", CredentialSource.UNAVAILABLE, False),
    "shell": CredentialReference("shell", "", CredentialSource.UNAVAILABLE, False),
    "sqlite": CredentialReference("sqlite", "", CredentialSource.UNAVAILABLE, False),
    "docker": CredentialReference("docker", "DOCKER_HOST", CredentialSource.ENVIRONMENT, False),
}


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------


class ExecutionCredentialManager:
    """Manager credential execution (read-only, no network).

    Memuat nilai credential dari env pada saat resolve (tidak pernah disimpan
    di objek manager), memvalidasi keberadaan, dan selalu menghasilkan audit.
    """

    def __init__(
        self,
        references: Optional[Dict[str, CredentialReference]] = None,
        environ: Optional[Dict[str, str]] = None,
    ) -> None:
        self._references = dict(references or CREDENTIAL_REFERENCES)
        # environ injection untuk test deterministik; default os.environ
        self._environ = environ if environ is not None else None
        self._audit: List[CredentialAuditRecord] = []

    # --- akses env (injectable untuk determinisme test) ---
    def _getenv(self, key: str) -> str:
        if self._environ is not None:
            return self._environ.get(key, "")
        import os
        return os.environ.get(key, "")

    def raw_value(self, provider_id: str, actor: str = "execution") -> str:
        """Ambil nilai credential mentah dari sumber (env) tanpa menyimpan.

        Hanya untuk dipakai verifier/consumer internal yang butuh nilai untuk
        validasi format. Menghasilkan audit. Tidak menerima credential di objek
        manager (dibaca on-demand).
        """
        ref = self._references.get(provider_id)
        if ref is None or not ref.env_var:
            self._audit.append(self._audit_record(provider_id, "raw", actor, "", "non_auth_or_unknown"))
            return ""
        value = self._getenv(ref.env_var)
        self._audit.append(self._audit_record(provider_id, "raw", actor, ref.env_var,
                                              "found" if value else "missing"))
        return value

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # --- lookup registri ---
    def reference_for(self, provider_id: str) -> Optional[CredentialReference]:
        return self._references.get(provider_id)

    def known_providers(self) -> Tuple[str, ...]:
        return tuple(sorted(self._references.keys()))

    # --- operasi credential (semua menghasilkan audit) ---
    def resolve(self, provider_id: str, actor: str = "execution") -> CredentialStatusResult:
        """Resolve status credential provider (read-only). Tidak mengubah apapun."""
        ref = self._references.get(provider_id)
        if ref is None:
            self._audit.append(self._audit_record(provider_id, "resolve", actor, "", "unknown_provider"))
            return CredentialStatusResult(
                provider_id, CredentialStatus.UNKNOWN, False, reason="provider tidak dikenal",
            )

        if not ref.is_known() or not ref.env_var:
            # provider non-auth: selalu tersedia (tidak butuh credential)
            self._audit.append(self._audit_record(provider_id, "resolve", actor, ref.env_var, "non_auth"))
            return CredentialStatusResult(
                provider_id, CredentialStatus.OK, True, reason="provider non-auth",
            )

        value = self._getenv(ref.env_var)
        if not value:
            self._audit.append(self._audit_record(provider_id, "resolve", actor, ref.env_var, "missing"))
            return CredentialStatusResult(
                provider_id, CredentialStatus.MISSING, False,
                missing_env=ref.env_var, reason=f"env '{ref.env_var}' kosong",
            )

        self._audit.append(self._audit_record(provider_id, "resolve", actor, ref.env_var, "found"))
        return CredentialStatusResult(
            provider_id, CredentialStatus.OK, True,
            masked_value=mask_secret(value), reason="credential tersedia",
        )

    def verify(self, provider_id: str, actor: str = "execution") -> CredentialStatusResult:
        """Verifikasi credential (keberadaan + format minimum). Tidak mengecek
        validitas jaringan (itu domain WP-02/Connection, bukan credential store).
        """
        result = self.resolve(provider_id, actor)
        if result.status == CredentialStatus.OK and result.available:
            value = self._getenv(self._references[provider_id].env_var)
            # sanity: non-empty sudah diverifikasi resolve; tambah panjang minimum
            if len(value) < 4:
                self._audit.append(self._audit_record(provider_id, "verify", actor,
                                                      self._references[provider_id].env_var, "too_short"))
                return CredentialStatusResult(
                    provider_id, CredentialStatus.INVALID, False,
                    masked_value=mask_secret(value), reason="credential terlalu pendek",
                )
        return result

    def list_status(self, actor: str = "execution") -> List[CredentialStatusResult]:
        """Status seluruh provider yang dikenal (read-only)."""
        return [self.resolve(p, actor) for p in self.known_providers()]

    def summary(self, actor: str = "execution") -> CredentialSummary:
        statuses = self.list_status(actor)
        by = {}  # type: Dict[str, int]
        for s in statuses:
            by[s.status.value] = by.get(s.status.value, 0) + 1
        return CredentialSummary(
            total=len(statuses),
            available=sum(1 for s in statuses if s.available),
            missing=sum(1 for s in statuses if s.status == CredentialStatus.MISSING),
            invalid=sum(1 for s in statuses if s.status == CredentialStatus.INVALID),
            by_status=by,
        )

    # --- audit ---
    def _audit_record(self, provider_id: str, action: str, actor: str,
                      env_var: str, result: str) -> CredentialAuditRecord:
        return CredentialAuditRecord(
            record_id="cred-{}-{}".format(provider_id, len(self._audit)),
            provider_id=provider_id,
            action=action,
            accessed_at=self._now(),
            actor=actor,
            env_var=env_var,
            result=result,
        )

    def audit_log(self) -> Tuple[CredentialAuditRecord, ...]:
        """Seluruh record audit credential (immutable, append-only)."""
        return tuple(self._audit)

    def clear_audit(self) -> None:
        """Bersihkan audit (terutama untuk test)."""
        self._audit.clear()
