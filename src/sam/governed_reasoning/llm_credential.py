"""LLM Credential Management - WP-02 (MISSION-4.4 / IP-4.4-001).

Pengelolaan credential LLM yang aman dan terpisah dari source code.

API Key tidak tersimpan di source code; credential dimuat dari Secret Store
atau Environment; secret selalu dimasking; seluruh akses credential
menghasilkan audit.
"""
from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


def mask_secret(secret: str, visible: int = 4) -> str:
    """Masking secret: tampilkan N karakter pertama, sisanya bintang."""
    if not secret:
        return ""
    if len(secret) <= visible:
        return "*" * len(secret)
    return secret[:visible] + "*" * (len(secret) - visible)


@dataclass(frozen=True)
class CredentialMetadata:
    """Metadata credential (tidak pernah menyimpan nilai rahasia)."""

    credential_id: str
    provider_id: str
    key_name: str
    source: str  # env | secret_store | inline
    masked: str = ""
    loaded_at: str = ""

    def as_dict(self) -> dict:
        return {
            "credential_id": self.credential_id,
            "provider_id": self.provider_id,
            "key_name": self.key_name,
            "source": self.source,
            "masked": self.masked,
            "loaded_at": self.loaded_at,
        }


@dataclass(frozen=True)
class CredentialAuditEntry:
    """Satu catatan akses credential (audit)."""

    credential_id: str
    event: str  # loaded | accessed | masked | cleared
    at: str = ""

    def as_dict(self) -> dict:
        return {"credential_id": self.credential_id, "event": self.event, "at": self.at}


class SecretResolver:
    """Resolver secret dari environment / secret store."""

    def __init__(self, store: Optional[Dict[str, str]] = None) -> None:
        self._store = store or {}
        self._audit: List[CredentialAuditEntry] = []

    def resolve(self, key_name: str, env_var: str = "") -> Optional[str]:
        if not env_var:
            return None
        value = self._store.get(env_var)
        if value is None:
            value = os.environ.get(env_var)
        return value

    def has(self, var: str) -> bool:
        return var in self._store

    def get(self, var: str) -> Optional[str]:
        return self._store.get(var)

    def audit_entries(self) -> Tuple[CredentialAuditEntry, ...]:
        return tuple(self._audit)


class CredentialStore:
    """Penyimpanan credential di memori (referensi saja, tak pernah diserialisasi)."""

    def __init__(self, resolver: Optional[SecretResolver] = None) -> None:
        self._resolver = resolver or SecretResolver()
        self._values: Dict[str, str] = {}
        self._metadata: Dict[str, CredentialMetadata] = {}
        self._audit: List[CredentialAuditEntry] = []

    def load(
        self,
        provider_id: str,
        *,
        key_name: str,
        env_var: str = "",
        secret_store_var: str = "",
    ) -> CredentialMetadata:
        secret: Optional[str] = None
        source = "env"
        if secret_store_var and self._resolver.has(secret_store_var):
            secret = self._resolver.get(secret_store_var)
            source = "secret_store"
        elif env_var:
            secret = self._resolver.resolve(key_name, env_var)
            source = "env"
        if secret is None:
            raise ValueError(f"Secret not found for {key_name}")
        credential_id = uuid.uuid4().hex
        metadata = CredentialMetadata(
            credential_id=credential_id,
            provider_id=provider_id,
            key_name=key_name,
            source=source,
            masked=mask_secret(secret),
        )
        self._values[credential_id] = secret
        self._metadata[credential_id] = metadata
        self._audit.append(
            CredentialAuditEntry(credential_id, "loaded", _now_utc())
        )
        return metadata

    def value(self, credential_id: str) -> Optional[str]:
        value = self._values.get(credential_id)
        if value is not None:
            self._audit.append(
                CredentialAuditEntry(credential_id, "accessed", _now_utc())
            )
        return value

    def masked(self, credential_id: str) -> str:
        meta = self._metadata.get(credential_id)
        if meta is None:
            return ""
        self._audit.append(
            CredentialAuditEntry(credential_id, "masked", _now_utc())
        )
        return meta.masked

    def clear(self) -> None:
        for cid in list(self._values):
            self._audit.append(CredentialAuditEntry(cid, "cleared", _now_utc()))
        self._values.clear()
        self._metadata.clear()

    def audit_report(self) -> Tuple[CredentialAuditEntry, ...]:
        return tuple(self._audit)

    def metadata(self, credential_id: str) -> Optional[CredentialMetadata]:
        return self._metadata.get(credential_id)

    def count(self) -> int:
        return len(self._values)
