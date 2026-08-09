"""Runtime & Provider Verification - WP-04/05 (MISSION-4.5 / IP-4.5-001).

Memverifikasi kondisi Runtime & Provider sebagai bagian dari investigasi.
Verification menghasilkan evidence, tidak ada mutation, dapat dijelaskan.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Tuple


@dataclass(frozen=True)
class RuntimeEvidence:
    """Evidence hasil verifikasi runtime."""

    runtime_id: str
    validated: bool
    health: str = ""
    detail: str = ""

    def as_dict(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "validated": self.validated,
            "health": self.health,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ProviderEvidence:
    """Evidence hasil verifikasi provider."""

    provider_id: str
    validated: bool
    available: bool = False
    health: str = ""
    detail: str = ""

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "validated": self.validated,
            "available": self.available,
            "health": self.health,
            "detail": self.detail,
        }


class RuntimeVerificationEngine:
    """Mesin verifikasi runtime (read-only)."""

    def __init__(self) -> None:
        self._probes: Dict[str, Callable[[], Dict[str, Any]]] = {}
        self._evidence: Tuple[RuntimeEvidence, ...] = ()

    def register_probe(self, runtime_id: str, fn: Callable[[], Dict[str, Any]]) -> None:
        self._probes[runtime_id] = fn

    def verify(self, runtime_id: str) -> RuntimeEvidence:
        fn = self._probes.get(runtime_id)
        if fn is None:
            ev = RuntimeEvidence(runtime_id, False, "unknown", "no probe")
        else:
            try:
                data = fn() or {}
                health = str(data.get("health", "unknown"))
                validated = health in ("healthy", "degraded")
                ev = RuntimeEvidence(runtime_id, validated, health, str(data.get("detail", "")))
            except Exception as exc:
                ev = RuntimeEvidence(runtime_id, False, "error", str(exc))
        self._evidence += (ev,)
        return ev

    def report(self) -> Tuple[RuntimeEvidence, ...]:
        return self._evidence

    def metrics(self) -> Dict[str, Any]:
        total = len(self._evidence)
        return {
            "total": total,
            "validated": sum(1 for e in self._evidence if e.validated),
        }


class ProviderVerificationEngine:
    """Mesin verifikasi provider (read-only, tanpa execution)."""

    def __init__(self) -> None:
        self._probes: Dict[str, Callable[[], Dict[str, Any]]] = {}
        self._evidence: Tuple[ProviderEvidence, ...] = ()

    def register_probe(self, provider_id: str, fn: Callable[[], Dict[str, Any]]) -> None:
        self._probes[provider_id] = fn

    def verify(self, provider_id: str) -> ProviderEvidence:
        fn = self._probes.get(provider_id)
        if fn is None:
            ev = ProviderEvidence(provider_id, False, False, "unknown", "no probe")
        else:
            try:
                data = fn() or {}
                health = str(data.get("health", "unknown"))
                available = bool(data.get("available", health == "healthy"))
                validated = available or health == "degraded"
                ev = ProviderEvidence(provider_id, validated, available, health, str(data.get("detail", "")))
            except Exception as exc:
                ev = ProviderEvidence(provider_id, False, False, "error", str(exc))
        self._evidence += (ev,)
        return ev

    def report(self) -> Tuple[ProviderEvidence, ...]:
        return self._evidence

    def metrics(self) -> Dict[str, Any]:
        total = len(self._evidence)
        return {
            "total": total,
            "available": sum(1 for e in self._evidence if e.available),
        }
