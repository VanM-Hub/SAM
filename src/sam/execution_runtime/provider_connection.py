"""Provider Connection - IP-4.1-001 WP-04.

Provider Execution Foundation.
Membangun koneksi provider yang deterministik.

Scope (Foundation immutable):
- Provider dapat dihubungkan (resolve identity + metadata).
- Health Verification tersedia (tanpa memanggil jaringan eksekusi).
- Failure dapat dijelaskan (explainability).
- Tidak ada execution saat connection gagal (guard konsumen).
- Deterministik (Article VII), provider-agnostic (Article VIII).

CATATAN: "Connection" di sini = resolusi & verifikasi kesiapan provider,
BUKAN membuka koneksi jaringan. Handshake/jaringan aktif tetap domain
ProviderExecutor.execute() (mode execute + approval). Ini menjaga koneksi
tetap deterministik dan tanpa side-effect eksternal di tahap persiapan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from .credential_verifier import CredentialVerifier


# ---------------------------------------------------------------------------
# Model (immutable)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProviderIdentity:
    """Identitas provider yang ter-resolve (immutable)."""

    provider_id: str
    known: bool
    base_url: str = ""
    requires_credential: bool = False
    credential_env: str = ""

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "known": self.known,
            "base_url": self.base_url,
            "requires_credential": self.requires_credential,
            "credential_env": self.credential_env,
        }


@dataclass(frozen=True)
class ConnectionHealth:
    """Status kesehatan koneksi (immutable, read-only)."""

    healthy: bool
    credential_status: str = "unknown"
    resolved: bool = False
    detail: str = ""

    def as_dict(self) -> dict:
        return {
            "healthy": self.healthy,
            "credential_status": self.credential_status,
            "resolved": self.resolved,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ConnectionCheck:
    """Satu cek koneksi (immutable)."""

    name: str
    passed: bool
    detail: str = ""

    def as_dict(self) -> dict:
        return {"name": self.name, "passed": self.passed, "detail": self.detail}


@dataclass(frozen=True)
class ProviderConnection:
    """Hasil koneksi provider (immutable)."""

    provider_id: str
    connected: bool
    identity: ProviderIdentity
    health: ConnectionHealth
    checks: Tuple[ConnectionCheck, ...] = field(default_factory=tuple)
    reason: str = ""
    connected_at: str = ""

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "connected": self.connected,
            "identity": self.identity.as_dict(),
            "health": self.health.as_dict(),
            "checks": [c.as_dict() for c in self.checks],
            "reason": self.reason,
            "connected_at": self.connected_at,
        }


# ---------------------------------------------------------------------------
# Base URL table (deterministik, reflek detail PROVIDER_ENV dari executor)
# ---------------------------------------------------------------------------

PROVIDER_BASE_URLS: Dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com",
    "gemini": "https://generativelanguage.googleapis.com",
    "deepseek": "https://api.deepseek.com",
    "ollama": "http://localhost:11434",
    "openclaw": "http://127.0.0.1:18789",
    "filesystem": "",
    "shell": "",
    "sqlite": "",
    "docker": "",
}


# ---------------------------------------------------------------------------
# Connection manager
# ---------------------------------------------------------------------------


class ProviderConnectionManager:
    """Manager koneksi provider (read-only, no network).

    Menyediakan resolusi identitas + health check berbasis credential dan
    registry, tanpa membuka jaringan. Guard: can_connect() mencegah execution
    saat provider belum berhasil dihubungkan.
    """

    def __init__(
        self,
        verifier: Optional[CredentialVerifier] = None,
        base_urls: Optional[Dict[str, str]] = None,
    ) -> None:
        self._verifier = verifier or CredentialVerifier()
        self._base_urls = dict(base_urls or PROVIDER_BASE_URLS)

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def resolve_identity(self, provider_id: str) -> ProviderIdentity:
        """Resolve identitas provider (deterministik)."""
        ref = self._verifier.manager.reference_for(provider_id)
        if ref is None:
            return ProviderIdentity(provider_id, known=False)
        return ProviderIdentity(
            provider_id=provider_id,
            known=True,
            base_url=self._base_urls.get(provider_id, ""),
            requires_credential=ref.required or bool(ref.env_var),
            credential_env=ref.env_var,
        )

    def connect(self, provider_id: str, actor: str = "execution") -> ProviderConnection:
        """Hubungkan (resolve + health check) provider. No network."""
        identity = self.resolve_identity(provider_id)
        checks: List[ConnectionCheck] = []

        # Cek 1: provider dikenal
        checks.append(ConnectionCheck("provider_known", identity.known,
                                      "terdaftar" if identity.known else "tidak dikenal"))
        if not identity.known:
            return ProviderConnection(
                provider_id, False, identity,
                ConnectionHealth(False, "unknown", False, "provider tidak dikenal"),
                tuple(checks), "provider tidak dikenal", self._now(),
            )

        # Cek 2: verifikasi credential
        verification = self._verifier.verify(provider_id, actor)
        credential_status = verification.status
        checks.append(ConnectionCheck(
            "credential_verified", verification.verified,
            verification.reason if not verification.verified else "credential ok",
        ))
        credential_healthy = (not identity.requires_credential) or verification.verified
        healthy = credential_healthy
        health = ConnectionHealth(healthy, credential_status, True,
                                  "siap" if healthy else "credential belum terverifikasi")
        connected = healthy
        return ProviderConnection(
            provider_id, connected, identity, health, tuple(checks),
            "" if connected else "provider belum siap dihubungkan; credential tidak terverifikasi",
            self._now(),
        )

    def health(self, provider_id: str, actor: str = "execution") -> ConnectionHealth:
        return self.connect(provider_id, actor).health

    def can_execute(self, provider_id: str, actor: str = "execution") -> bool:
        """Guard konsumen: execution hanya bila provider connected."""
        return self.connect(provider_id, actor).connected

    def connected_providers(self, actor: str = "execution") -> Tuple[str, ...]:
        return tuple(p for p in self._verifier.manager.known_providers()
                     if self.can_execute(p, actor))

    def summary(self, actor: str = "execution") -> Dict[str, int]:
        providers = self._verifier.manager.known_providers()
        connected = sum(1 for p in providers if self.can_execute(p, actor))
        return {"total": len(providers), "connected": connected,
                "not_connected": len(providers) - connected}
